"""Browse a video with the keyboard, mouse wheel or scrollbar and save chosen frames as JPG."""

import argparse
import cv2
import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import os
from unidecode import unidecode

DEFAULT_STEPS = (40, 200, 800)
VIDEO_PATTERNS = ("*.mov", "*.mp4", "*.avi", "*.3gp")
VIDEO_FILETYPES = [("Video files", VIDEO_PATTERNS)]


def fit_size(vid_w, vid_h, max_w, max_h):
    """Return the largest (width, height) with the video's aspect ratio inside max_w x max_h.

    If the video size is unknown (zero or negative), return (max_w, max_h).
    """
    if vid_w <= 0 or vid_h <= 0:
        return max_w, max_h
    scale = min(max_w / vid_w, max_h / vid_h)
    return max(int(vid_w * scale), 1), max(int(vid_h * scale), 1)


def frame_filename(name_video, frame_index):
    """Return the output file name for a saved frame: <video name in ASCII>_frame_<n>.jpg."""
    base_name, _ = os.path.splitext(name_video)
    return f"{unidecode(base_name)}_frame_{frame_index}.jpg"


class VideoPlayer:
    """Tkinter window that shows a video frame by frame and saves the frame on screen.

    Keys: Right/Left move by steps[0] (back by half), Down/Up by steps[1] (back by half),
    the mouse wheel by steps[2]; Space, Enter or S saves the frame; Q quits.
    Creating the object opens the window and runs the Tk main loop until it is closed.
    """

    def __init__(self, video_path, name_video, out_dir=None, steps=DEFAULT_STEPS):
        self.video_path = video_path
        self.name_video = name_video
        self.out_dir = out_dir or os.getcwd()  # where saved frames go
        self.cap = cv2.VideoCapture(video_path)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.current_frame = 0
        # Frame steps: small (Right/Left), medium (Down/Up), large (mouse wheel)
        self.skip_frames, self.skip_frames_2, self.wheel_step = steps
        self.displayed_frame = None  # last frame shown on the canvas (BGR, full size)

        self.root = tk.Tk()
        self.root.title(name_video)

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

        # Status line (shows the result of the last save)
        self.status_var = tk.StringVar(value="")
        self.status_label = tk.Label(self.root, textvariable=self.status_var, anchor="w")
        self.status_label.pack(fill="x", padx=10, pady=(0, 8))
        self.saved_count = 0

        # Create a canvas for video display
        self.canvas = tk.Canvas(self.video_frame, width=self.frame_width, height=self.frame_height)
        self.canvas.pack()

        # Bind keyboard events
        self.root.bind("<Right>", self.next_frame)
        self.root.bind("<Left>", self.previous_frame)
        self.root.bind("<s>", self.save_current_frame)
        self.root.bind("<space>", self.save_current_frame)
        self.root.bind("<q>", self.quit)

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

    def preview_size(self):
        """Preview size for the open video: its aspect ratio, fitted in 80% x 60% of the screen."""
        max_w = int(self.root.winfo_screenwidth() * 0.8)
        max_h = int(self.root.winfo_screenheight() * 0.6)
        return fit_size(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH),
                        self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT), max_w, max_h)

    def key_pressed(self, event):
        """Handle Right/Left/Down/Up (seek) and S, Space, Enter (save) key presses."""
        if event.keysym == "Right":
            self.next_frame()
        elif event.keysym == "Left":
            self.previous_frame()
        elif event.keysym == "Down":
            self.skip_forward()
        elif event.keysym == "Up":
            self.skip_backward()
        elif event.keysym == "s":
            self.save_current_frame()
        elif event.keysym == "Return" or event.keysym == "space":
            self.save_current_frame()

    def update_display(self):
        """Read the current frame, show it resized on the canvas and sync the scrollbar."""
        # Read the current frame
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
        ret, frame = self.cap.read()

        if ret:
            # Keep the full-size frame so "save" writes exactly what is on screen
            self.displayed_frame = frame
            # Resize the frame to fit the display
            resized_frame = cv2.resize(frame, (self.frame_width, self.frame_height))

            # Convert the frame to PIL image format
            image = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(image)

            # Create a PhotoImage object
            self.photo_image = ImageTk.PhotoImage(image)

            # Update the display
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor="nw", image=self.photo_image)

            self.update_scrollbar()  # Update the scrollbar position


    def next_frame(self, event=None):
        """Move forward by the small step (Right key)."""
        if self.current_frame < self.total_frames - 1:
            self.current_frame = min(self.current_frame + self.skip_frames, self.total_frames - 1)
            self.update_display()

    def previous_frame(self, event=None):
        """Move back by half the small step (Left key)."""
        if self.current_frame > 0:
            self.current_frame = max(self.current_frame - self.skip_frames // 2, 0)
            self.update_display()

    def skip_forward(self):
        """Move forward by the medium step (Down key)."""
        self.current_frame = min(self.current_frame + self.skip_frames_2, self.total_frames - 1)
        self.update_display()

    def skip_backward(self):
        """Move back by half the medium step (Up key)."""
        self.current_frame = max(self.current_frame - self.skip_frames_2 // 2, 0)
        self.update_display()

    def save_current_frame(self, event=None):
        """Save the frame on screen as JPG in the output folder and update the status line."""
        # Save the frame currently on screen (not cap.read(), which would return the next frame)
        frame = self.displayed_frame
        if frame is not None:
            filename = frame_filename(self.name_video, self.current_frame)
            os.makedirs(self.out_dir, exist_ok=True)
            if cv2.imwrite(os.path.join(self.out_dir, filename), frame):
                self.saved_count += 1
                self.status_var.set(f"Saved {filename} ({self.saved_count} saved)")
                print(f"Frame {self.current_frame} saved as {filename}")
            else:
                self.status_var.set(f"Could not save {filename}")

    def scroll_video(self, *args):
        """Jump to the frame that matches the scrollbar position."""
        # Get the current scrollbar position
        position = self.scrollbar.get()[0]

        # Calculate the new frame based on the scrollbar position
        new_frame = int(position * (self.total_frames - 1))

        # Update the current frame only if it's different from the new frame
        if new_frame != self.current_frame:
            self.current_frame = new_frame
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
            self.update_display()


    def scroll_up(self, event=None):
        """Wheel up: go back by the large step."""
        self.current_frame = max(0, self.current_frame - self.wheel_step)
        self.update_display()
        self.update_scrollbar()

    def scroll_down(self, event=None):
        """Wheel down: go forward by the large step."""
        self.current_frame = min(self.total_frames - 1, self.current_frame + self.wheel_step)
        self.update_display()
        self.update_scrollbar()

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
        position = event.x / self.scrollbar.winfo_width()
        self.scrollbar.set(position, position)
        self.scroll_video()

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
            self.cap.release()  # Release the current video capture
            self.cap = cv2.VideoCapture(video_path)  # Open the new video
            self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.current_frame = 0
            self.displayed_frame = None
            self.name_video = os.path.basename(video_path)

            # Recompute the preview size for the new video and resize the canvas
            self.frame_width, self.frame_height = self.preview_size()
            self.canvas.config(width=self.frame_width, height=self.frame_height)
            self.update_display()

            # Update the window title with the new video name
            self.root.title(self.name_video)


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
        VideoPlayer(video_path, os.path.basename(video_path), args.out, args.steps)


if __name__ == "__main__":
    main()
