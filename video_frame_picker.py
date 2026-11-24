"""Browse a video with the keyboard, mouse wheel or scrollbar and save chosen frames as JPG."""

import argparse
import re
import cv2
import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import os
from unidecode import unidecode

DEFAULT_STEPS = (40, 200, 800)
VIDEO_PATTERNS = ("*.mov", "*.mp4", "*.avi", "*.3gp")
VIDEO_FILETYPES = [("Video files", VIDEO_PATTERNS)]
JPEG_QUALITY = 95  # quality of the saved frames (OpenCV's default, made explicit)

# characters not allowed in Windows file names, plus control characters
_INVALID_FILENAME_CHARS = re.compile('[' + re.escape('<>:"/' + chr(92) + '|?*') + chr(0) + '-' + chr(31) + ']')


def fit_size(vid_w, vid_h, max_w, max_h):
    """Return the largest (width, height) with the video's aspect ratio inside max_w x max_h.

    If the video size is unknown (zero or negative), return (max_w, max_h).
    """
    if vid_w <= 0 or vid_h <= 0:
        return max_w, max_h
    scale = min(max_w / vid_w, max_h / vid_h)
    return max(int(vid_w * scale), 1), max(int(vid_h * scale), 1)


def clamp_frame(index, total_frames):
    """Clamp a frame index to 0..total_frames-1 (0 when the frame count is unknown)."""
    return max(0, min(index, total_frames - 1))


def fraction_to_frame(fraction, total_frames):
    """Frame index for a scrollbar position (0.0 = first frame, 1.0 = last), clamped."""
    return clamp_frame(round(fraction * (total_frames - 1)), total_frames)


def resize_frame(frame, width, height):
    """Resize a frame for display: INTER_AREA when shrinking (no aliasing), bilinear when enlarging."""
    h, w = frame.shape[:2]
    shrinking = width < w or height < h
    return cv2.resize(frame, (width, height),
                      interpolation=cv2.INTER_AREA if shrinking else cv2.INTER_LINEAR)


def can_read_video(video_path):
    """Return True if OpenCV can open the video and decode its first frame."""
    cap = cv2.VideoCapture(video_path)
    try:
        return cap.isOpened() and cap.read()[0]
    finally:
        cap.release()


def frame_filename(video_name, frame_index):
    """Return the output file name for a saved frame: <video name in ASCII>_frame_<n>.jpg.

    Characters that are not allowed in Windows file names (unidecode turns "«" into "<<")
    are replaced with "_"; a name that ends up empty becomes "video".
    """
    base_name, _ = os.path.splitext(video_name)
    base_name = _INVALID_FILENAME_CHARS.sub("_", unidecode(base_name)).strip() or "video"
    return f"{base_name}_frame_{frame_index}.jpg"


def unique_path(folder, name):
    """Return (name, path) for a file that does not exist yet in folder.

    If folder/name is free it is used as is; otherwise _2, _3, ... is added before the extension.
    """
    base, ext = os.path.splitext(name)
    candidate, n = name, 1
    while os.path.exists(os.path.join(folder, candidate)):
        n += 1
        candidate = f"{base}_{n}{ext}"
    return candidate, os.path.join(folder, candidate)


def save_frame_jpg(path, frame, quality=JPEG_QUALITY):
    """Write a BGR frame as JPG at path; return True on success.

    cv2.imwrite fails silently on Windows when the path has non-ASCII characters, so the
    image is encoded in memory and written with numpy instead.
    """
    ok, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        return False
    try:
        buffer.tofile(path)
    except OSError:
        return False
    return True


class VideoPlayer:
    """Tkinter window that shows a video frame by frame and saves the frame on screen.

    Keys: Right/Left move by steps[0] (back by half), Down/Up by steps[1] (back by half),
    the mouse wheel by steps[2]; Space, Enter or S saves the frame; Q quits.
    Creating the object opens the window and runs the Tk main loop until it is closed.
    """

    def __init__(self, video_path, video_name, out_dir=None, steps=DEFAULT_STEPS):
        self.video_path = video_path
        self.video_name = video_name
        self.out_dir = out_dir or os.getcwd()  # where saved frames go
        self.cap = cv2.VideoCapture(video_path)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.current_frame = 0
        # Frame steps: small (Right/Left), medium (Down/Up), large (mouse wheel)
        self.small_step, self.medium_step, self.large_step = steps
        self.displayed_frame = None  # last frame shown on the canvas (BGR, full size)
        self.displayed_index = None  # index of displayed_frame (the number used in the file name)

        self.root = tk.Tk()
        self.root.title(video_name)

        # Preview size is computed for every video (see preview_size)
        self.frame_width, self.frame_height = self.preview_size()

        # Create a frame to display the video
        self.video_frame = tk.Frame(self.root)
        self.video_frame.pack()

        # Create a scrollbar
        self.scrollbar = ttk.Scrollbar(self.root, orient="horizontal", command=self.scroll_video)
        self.scrollbar.pack(fill="x")

        # Create a frame for the buttons
        self.button_frame = tk.Frame(self.root)
        self.button_frame.pack(pady=10)

        # Create a button to save the current frame
        self.save_button = tk.Button(self.button_frame, text="Save Frame", command=self.save_current_frame)
        self.save_button.pack(side="left", padx=10)

        # Create a button to open a new video
        self.open_button = tk.Button(self.button_frame, text="Open New Video", command=self.open_new_video)
        self.open_button.pack(side="left", padx=10)

        # Space is a window key binding (save). A focused button would also "click" on Space,
        # saving twice, so buttons are not focusable and swallow Space themselves.
        for button in (self.save_button, self.open_button):
            button.config(takefocus=0)
            button.bind("<space>", self.save_current_frame_break)

        # Status line (shows the result of the last save)
        self.status_var = tk.StringVar(value="")
        self.status_label = tk.Label(self.root, textvariable=self.status_var, anchor="w")
        self.status_label.pack(fill="x", padx=10, pady=(0, 8))
        self.saved_count = 0
        self.saved_names = {}  # (video path, frame index) -> file name saved in this session

        # Create a canvas for video display
        self.canvas = tk.Canvas(self.video_frame, width=self.frame_width, height=self.frame_height)
        self.canvas.pack()

        # Bind keyboard events
        self.root.bind("<Right>", self.next_frame)
        self.root.bind("<Left>", self.previous_frame)
        self.root.bind("<s>", self.save_current_frame)
        self.root.bind("<S>", self.save_current_frame)
        self.root.bind("<space>", self.save_current_frame)
        self.root.bind("<q>", self.quit)
        self.root.bind("<Q>", self.quit)
        self.root.protocol("WM_DELETE_WINDOW", self.quit)  # window close button

        # Bind mouse events
        self.canvas.bind("<Button-4>", self.scroll_up)  # Wheel up (Linux/X11)
        self.canvas.bind("<Button-5>", self.scroll_down)  # Wheel down (Linux/X11)
        self.canvas.bind("<MouseWheel>", self.scroll_mouse_wheel)  # Wheel (Windows/macOS)
        self.scrollbar.bind("<Button-1>", self.start_scroll)
        self.scrollbar.bind("<B1-Motion>", self.move_scroll)
        self.scrollbar.bind("<ButtonRelease-1>", self.stop_scroll)
        self.root.bind("<Key>", self.key_pressed)

        self.update_display()
        self.root.mainloop()

    def preview_size(self, vid_w=None, vid_h=None):
        """Preview size for a video size (default: the open video's): aspect ratio kept, fitted in 80% x 60% of the screen."""
        max_w = int(self.root.winfo_screenwidth() * 0.8)
        max_h = int(self.root.winfo_screenheight() * 0.6)
        if vid_w is None:
            vid_w = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            vid_h = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        return fit_size(vid_w, vid_h, max_w, max_h)

    def key_pressed(self, event):
        """Handle Right/Left/Down/Up (seek) and S, Space, Enter (save) key presses."""
        if event.keysym == "Right":
            self.next_frame()
        elif event.keysym == "Left":
            self.previous_frame()
        elif event.keysym == "Down":
            self.medium_forward()
        elif event.keysym == "Up":
            self.medium_backward()
        elif event.keysym in ("s", "S"):
            self.save_current_frame()
        elif event.keysym == "Return" or event.keysym == "space":
            self.save_current_frame()

    def update_display(self):
        """Read the current frame, show it resized on the canvas and sync the scrollbar."""
        # Read the current frame
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
        ret, frame = self.cap.read()

        if not ret:
            if self.current_frame > 0 and self.current_frame >= self.total_frames - 1:
                # The reported frame count was too high: the video really ends before this frame
                self.find_real_end()
            elif self.displayed_index is not None:
                # Unreadable frame in the middle: stay on the one that is on screen
                self.status_var.set(f"Could not read frame {self.current_frame}")
                self.current_frame = self.displayed_index
                self.update_scrollbar()
            return

        # Keep the full-size frame so "save" writes exactly what is on screen
        self.displayed_frame = frame
        self.displayed_index = self.current_frame
        # Use the real frame size (rotation metadata can make it differ from the reported one)
        size = self.preview_size(frame.shape[1], frame.shape[0])
        if size != (self.frame_width, self.frame_height):
            self.frame_width, self.frame_height = size
            self.canvas.config(width=self.frame_width, height=self.frame_height)
        # Resize the frame to fit the display
        resized_frame = resize_frame(frame, self.frame_width, self.frame_height)

        # Convert the frame to PIL image format
        image = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(image)

        # Create a PhotoImage object
        self.photo_image = ImageTk.PhotoImage(image)

        # Update the display
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.photo_image)

        self.update_scrollbar()  # Update the scrollbar position

    def find_real_end(self):
        """The reported frame count was too high: binary-search the last readable frame and go there."""
        good = min(self.displayed_index or 0, self.current_frame - 1)  # a frame assumed readable
        bad = self.current_frame  # a frame known to be unreadable
        while bad - good > 1:
            mid = (good + bad) // 2
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, mid)
            if self.cap.read()[0]:
                good = mid
            else:
                bad = mid
        self.total_frames = good + 1
        self.current_frame = good
        self.update_display()

    def goto(self, frame_index):
        """Show frame_index, clamped to the valid range (never negative, never past the last frame)."""
        self.current_frame = clamp_frame(frame_index, self.total_frames)
        self.update_display()

    def next_frame(self, event=None):
        """Move forward by the small step (Right key)."""
        self.goto(self.current_frame + self.small_step)

    def previous_frame(self, event=None):
        """Move back by half the small step (Left key)."""
        self.goto(self.current_frame - self.small_step // 2)

    def medium_forward(self):
        """Move forward by the medium step (Down key)."""
        self.goto(self.current_frame + self.medium_step)

    def medium_backward(self):
        """Move back by half the medium step (Up key)."""
        self.goto(self.current_frame - self.medium_step // 2)

    def save_current_frame(self, event=None):
        """Save the frame on screen as JPG in the output folder and update the status line."""
        # Save the frame currently on screen (not cap.read(), which would return the next frame)
        frame = self.displayed_frame
        if frame is not None:
            key = (os.path.abspath(self.video_path), self.displayed_index)
            filename = frame_filename(self.video_name, self.displayed_index)
            os.makedirs(self.out_dir, exist_ok=True)
            previous = self.saved_names.get(key)
            if previous and os.path.exists(os.path.join(self.out_dir, previous)):
                filename = previous  # the same frame saved again in this session: keep its name
            else:
                # never overwrite another file: add _2, _3, ... if the name is taken
                filename, _ = unique_path(self.out_dir, filename)
            if save_frame_jpg(os.path.join(self.out_dir, filename), frame):
                self.saved_names[key] = filename
                self.saved_count += 1
                self.status_var.set(f"Saved {filename} ({self.saved_count} saved)")
                print(f"Frame {self.displayed_index} saved as {filename}")
            else:
                self.status_var.set(f"Could not save {filename}")

    def save_current_frame_break(self, event=None):
        """Save from a button's Space binding and stop the event, so one key press saves once."""
        self.save_current_frame()
        return "break"

    def scroll_video(self, *args):
        """Scrollbar command: jump to a position ('moveto f') or move by a unit or page ('scroll n units|pages').

        With no arguments, jump to the frame that matches the current thumb position.
        A unit (arrow button) is one frame, a page (click in the trough) is the medium step.
        """
        if args and args[0] == "scroll":
            step = self.medium_step if args[2] == "pages" else 1
            new_frame = self.current_frame + int(args[1]) * step
        else:
            fraction = float(args[1]) if args else self.scrollbar.get()[0]
            new_frame = fraction_to_frame(fraction, self.total_frames)

        # Update the current frame only if it's different from the new frame
        new_frame = clamp_frame(new_frame, self.total_frames)
        if new_frame != self.current_frame:
            self.goto(new_frame)

    def scroll_up(self, event=None):
        """Wheel up: go back by the large step."""
        self.goto(self.current_frame - self.large_step)

    def scroll_down(self, event=None):
        """Wheel down: go forward by the large step."""
        self.goto(self.current_frame + self.large_step)

    def scroll_mouse_wheel(self, event=None):
        """Windows/macOS wheel event: positive delta goes back, negative goes forward."""
        if event.delta > 0:
            self.scroll_up()
        else:
            self.scroll_down()

    def start_scroll(self, event=None):
        """Scrollbar drag started: disable the wheel bindings while dragging."""
        self.canvas.unbind("<Button-4>")
        self.canvas.unbind("<Button-5>")
        self.canvas.unbind("<MouseWheel>")

    def move_scroll(self, event=None):
        """Scrollbar drag: move the thumb to the mouse position and seek there."""
        width = max(self.scrollbar.winfo_width(), 1)
        position = min(max(event.x / width, 0.0), 1.0)  # dragging outside the bar stays in range
        self.scrollbar.set(position, position)
        self.scroll_video("moveto", position)

    def stop_scroll(self, event=None):
        """Scrollbar drag ended: restore the wheel bindings."""
        self.canvas.bind("<Button-4>", self.scroll_up)
        self.canvas.bind("<Button-5>", self.scroll_down)
        self.canvas.bind("<MouseWheel>", self.scroll_mouse_wheel)

    def update_scrollbar(self):
        """Place the scrollbar thumb according to the current frame."""
        position = self.current_frame / max(self.total_frames - 1, 1)
        self.scrollbar.set(position, position)

    def quit(self, event=None):
        """Release the video and leave the main loop (Q key)."""
        self.cap.release()
        cv2.destroyAllWindows()
        self.root.quit()

    def open_new_video(self):
        """Ask for another video and switch to it (the saved counter keeps counting)."""
        video_path = filedialog.askopenfilename(title="Choose a video", filetypes=VIDEO_FILETYPES)
        if video_path:
            self.open_video(video_path)

    def open_video(self, video_path):
        """Switch to the video at video_path; if it cannot be read, keep the current one."""
        name = os.path.basename(video_path)
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        ok, _ = cap.read() if cap.isOpened() and total_frames > 0 else (False, None)
        if not ok:
            cap.release()
            self.status_var.set(f"Could not open {name}")
            return False
        self.cap.release()  # Release the previous video capture
        self.cap = cap
        self.total_frames = total_frames
        self.current_frame = 0
        self.displayed_frame = None
        self.displayed_index = None
        self.video_name = name
        self.video_path = video_path

        # Recompute the preview size for the new video and resize the canvas
        self.frame_width, self.frame_height = self.preview_size()
        self.canvas.config(width=self.frame_width, height=self.frame_height)
        self.update_display()
        self.status_var.set("")

        # Update the window title with the new video name
        self.root.title(self.video_name)
        return True


def parse_steps(text):
    """Parse --steps 'A,B,C' into three ints >= 2 (argparse type); else raise ArgumentTypeError."""
    try:
        steps = tuple(int(part) for part in text.split(","))
    except ValueError:
        steps = ()
    if len(steps) != 3 or min(steps) < 2:
        raise argparse.ArgumentTypeError("expected three integers >= 2, e.g. 40,200,800")
    return steps


def parse_args(argv=None):
    """Parse the command line (VIDEO, --out, --steps)."""
    parser = argparse.ArgumentParser(
        description="Browse a video and save the frames you choose as JPG.")
    parser.add_argument("video", nargs="?",
                        help="video file to open (a file dialog is shown if omitted)")
    parser.add_argument("--out", metavar="DIR",
                        help="folder for the saved frames (default: current directory)")
    parser.add_argument("--steps", metavar="A,B,C", type=parse_steps, default=DEFAULT_STEPS,
                        help="frame steps for left/right arrows (A), up/down arrows (B) and the "
                             "mouse wheel (C): three integers >= 2 (default: 40,200,800); "
                             "backward moves with the arrows are half of A and B")
    return parser.parse_args(argv)


def main(argv=None):
    """Entry point: pick a video (argument or file dialog) and open the player."""
    args = parse_args(argv)
    video_path = args.video
    if not video_path:
        # Ask for a video with a file dialog
        root = tk.Tk()
        root.withdraw()  # hide the helper window
        video_path = filedialog.askopenfilename(title="Choose a video", filetypes=VIDEO_FILETYPES)
        root.destroy()
    elif not os.path.isfile(video_path):
        raise SystemExit(f"Video not found: {video_path}")

    if video_path:
        if not can_read_video(video_path):
            raise SystemExit(f"Could not read the video: {video_path}")
        VideoPlayer(video_path, os.path.basename(video_path), args.out, args.steps)


if __name__ == "__main__":
    main()
