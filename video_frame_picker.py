import cv2
import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import os
from unidecode import unidecode

class VideoPlayer:
    def __init__(self, video_path, name_video):
        self.video_path = video_path
        self.name_video = name_video
        self.cap = cv2.VideoCapture(video_path)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.current_frame = 0
        self.skip_frames = 40  # Number of frames to skip when using keyboard or mouse
        self.skip_frames_2 = 200
        self.frame_skip_amount = 0
        self.displayed_frame = None  # last frame shown on the canvas (BGR, full size)

        self.root = tk.Tk()
        self.root.title(name_video)

        # Retrieve screen resolution
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Calculate video frame size based on screen resolution
        self.frame_width = int(screen_width * 0.8)
        self.frame_height = int(screen_height * 0.6)

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

        # Read the first frame
        ret, frame = self.cap.read()
        if ret:
            # Fit the display size to the video's aspect ratio
            frame_ratio = frame.shape[1] / frame.shape[0]
            window_ratio = screen_width / screen_height

            if frame_ratio > window_ratio:
                self.frame_width = int(screen_width * 0.8)
                self.frame_height = int(self.frame_width / frame_ratio)
            else:
                self.frame_height = int(screen_height * 0.6)
                self.frame_width = int(self.frame_height * frame_ratio)

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

    def key_pressed(self, event):
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
        # Move to the next frame
        if self.current_frame < self.total_frames - 1:
            self.current_frame = min(self.current_frame + self.skip_frames, self.total_frames - 1)
            self.update_display()

    def previous_frame(self, event=None):
        # Move to the previous frame
        if self.current_frame > 0:
            self.current_frame = max(self.current_frame - self.skip_frames // 2, 0)
            self.update_display()

    def skip_forward(self):
        self.current_frame = min(self.current_frame + self.skip_frames_2, self.total_frames - 1)
        self.update_display()

    def skip_backward(self):
        self.current_frame = max(self.current_frame - self.skip_frames_2 // 2, 0)
        self.update_display()

    def save_current_frame(self, event=None):
        # Save the frame currently on screen (not cap.read(), which would return the next frame)
        frame = self.displayed_frame
        if frame is not None:
            base_name, _ = os.path.splitext(self.name_video)
            base_name = unidecode(base_name)

            filename = base_name + f"_frame_{self.current_frame}.jpg"
            cv2.imwrite(filename, frame)
            print(f"Frame {self.current_frame} saved as {filename}")

    def scroll_video(self, *args):
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
        # Wheel up: go back
        self.current_frame = max(0, self.current_frame - self.skip_frames_2 * 4)
        self.update_display()
        self.update_scrollbar()

    def scroll_down(self, event=None):
        # Wheel down: go forward
        self.current_frame = min(self.total_frames - 1, self.current_frame + self.skip_frames_2 * 4)
        self.update_display()
        self.update_scrollbar()

    def scroll_mouse_wheel(self, event=None):
        # Windows/macOS wheel event
        if event.delta > 0:
            self.scroll_up()
        else:
            self.scroll_down()

    def start_scroll(self, event=None):
        # Start scrolling
        self.canvas.unbind("<Button-4>")
        self.canvas.unbind("<Button-5>")
        self.canvas.unbind("<MouseWheel>")

    def move_scroll(self, event=None):
        # Move the scrollbar based on the mouse position
        position = event.x / self.scrollbar.winfo_width()
        self.scrollbar.set(position, position)
        self.scroll_video()

    def stop_scroll(self, event=None):
        # Stop scrolling
        self.canvas.bind("<Button-4>", self.scroll_up)
        self.canvas.bind("<Button-5>", self.scroll_down)
        self.canvas.bind("<MouseWheel>", self.scroll_mouse_wheel)

    def update_scrollbar(self):
        # Update the scrollbar position based on the current frame
        position = self.current_frame / max(self.total_frames - 1, 1)
        self.scrollbar.set(position, position)

    def quit(self, event=None):
        # Quit the program
        self.cap.release()
        cv2.destroyAllWindows()
        self.root.quit()

    def open_new_video(self):
        # Open file dialog to choose a new video
        filetypes = [("Video files", "*.mov;*.mp4;*.avi;*.3gp")]
        video_path = filedialog.askopenfilename(title="Choose a video", filetypes=filetypes)
        if video_path:
            self.cap.release()  # Release the current video capture
            self.cap = cv2.VideoCapture(video_path)  # Open the new video
            self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.current_frame = 0
            self.displayed_frame = None
            self.name_video = os.path.basename(video_path)
            self.update_display()

            # Update the window title with the new video name
            self.root.title(self.name_video)


def main():
    # Ask for a video with a file dialog
    root = tk.Tk()
    root.withdraw()  # hide the helper window
    filetypes = [("Video files", "*.mov;*.mp4;*.avi;*.3gp")]
    video_path = filedialog.askopenfilename(title="Choose a video", filetypes=filetypes)
    root.destroy()

    if video_path:
        VideoPlayer(video_path, os.path.basename(video_path))

if __name__ == "__main__":
    main()
