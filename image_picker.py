"""Browse a folder of images and copy the ones you choose to an output folder."""

import argparse
import os
import shutil
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageOps, ImageTk

SKIP = 10  # images skipped by Next 10 / Back 10
PREVIEW_SIZE = (600, 400)  # preview area; images are letterboxed into it
IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff')


def list_images(folder):
    """Return the sorted names of the image files directly inside folder (by extension)."""
    return sorted(f for f in os.listdir(folder) if f.lower().endswith(IMAGE_EXTENSIONS))


def default_output_folder(input_folder):
    """Return output_<folder name> next to the input folder (works for '.' and trailing slashes)."""
    input_folder = os.path.abspath(input_folder)
    return os.path.join(os.path.dirname(input_folder), f"output_{os.path.basename(input_folder)}")


def output_name(image_name):
    """Return the name a copied image gets in the output folder: output_<original name>."""
    return f"output_{image_name}"


class ImageViewer:
    """Tkinter view that browses the images of a folder and copies chosen ones to an output folder.

    Keys: Right/Left = next/back, Down/Up = forward/back 10, Space or Enter = copy and go to next.
    """

    def __init__(self, root, input_folder, output_folder, custom_output=False):
        self.root = root
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.custom_output = custom_output  # --out given: keep it when opening another folder
        self.images = list_images(input_folder)
        self.current_index = 0

        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

        # Label that shows the image
        self.image_label = tk.Label(root)
        self.image_label.pack(pady=20)  # space between the image and the buttons

        # Label with the image file name, below the image
        self.image_name_label = tk.Label(root, text="", anchor="w", font=("Arial", 10, "bold"))
        self.image_name_label.pack(anchor="w", padx=10, pady=5)

        # Status line (shows the result of the last save)
        self.status_label = tk.Label(root, text="", anchor="w")
        self.status_label.pack(anchor="w", padx=10)
        self.saved_count = 0

        self.create_buttons()
        self.show_image(self.current_index)

        # bind_all captures every key event
        self.root.bind_all("<Key>", self.key_pressed)
        self.root.focus_force()  # force focus on the window

    def key_pressed(self, event):
        """Dispatch the arrow, Space and Enter keys to the matching action."""
        if event.keysym == "Up":
            self.back_10_images(event)
        elif event.keysym == "Left":
            self.back_image(event)
        elif event.keysym in ("Return", "space"):
            self.save_image(event)
        elif event.keysym == "Right":
            self.next_image(event)
        elif event.keysym == "Down":
            self.skip_10_images(event)

    def create_buttons(self):
        """Create the Back 10 / Back / Save / Next / Next 10 buttons."""
        # Frame for the buttons
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10, padx=10)

        self.back_10_button = tk.Button(
            button_frame, text="Back 10", command=self.back_10_images,
            width=12, height=2, borderwidth=1, relief="solid"
        )
        self.back_10_button.grid(row=0, column=0, padx=5)

        self.back_button = tk.Button(
            button_frame, text="Back", command=self.back_image,
            width=12, height=2, borderwidth=1, relief="solid"
        )
        self.back_button.grid(row=0, column=1, padx=5)

        self.save_button = tk.Button(
            button_frame, text="Save", command=self.save_image,
            width=12, height=2, borderwidth=1, relief="solid"
        )
        self.save_button.grid(row=0, column=2, padx=5)

        self.next_button = tk.Button(
            button_frame, text="Next", command=self.next_image,
            width=12, height=2, borderwidth=1, relief="solid"
        )
        self.next_button.grid(row=0, column=3, padx=5)

        self.skip_10_button = tk.Button(
            button_frame, text="Next 10", command=self.skip_10_images,
            width=12, height=2, borderwidth=1, relief="solid"
        )
        self.skip_10_button.grid(row=0, column=4, padx=5)

    def show_image(self, index):
        """Show the image at index (letterboxed in the preview area) and its file name."""
        if not self.images:
            self.image_label.config(image="")
            self.image_label.image = None
            self.image_name_label.config(text=f"No images found in: {self.input_folder}")
            return
        img_path = os.path.join(self.input_folder, self.images[index])
        img = Image.open(img_path).convert("RGB")
        # Keep the aspect ratio: fit inside the preview area and letterbox the rest
        img = ImageOps.contain(img, PREVIEW_SIZE)
        preview = Image.new("RGB", PREVIEW_SIZE, (32, 32, 32))
        preview.paste(img, ((PREVIEW_SIZE[0] - img.width) // 2, (PREVIEW_SIZE[1] - img.height) // 2))
        img_tk = ImageTk.PhotoImage(preview)
        self.image_label.config(image=img_tk)
        self.image_label.image = img_tk

        # Update the image name
        self.image_name_label.config(text=f"Image: {self.images[index]}")

    def save_image(self, event=None):
        """Copy the current image to the output folder as output_<name>, then go to the next one."""
        if not self.images:
            return
        img_path = os.path.join(self.input_folder, self.images[self.current_index])
        saved_name = output_name(self.images[self.current_index])
        output_img_path = os.path.join(self.output_folder, saved_name)
        shutil.copy(img_path, output_img_path)
        self.saved_count += 1
        self.status_label.config(
            text=f"Saved {saved_name} ({self.saved_count} saved)")
        print(f"Image saved: {output_img_path}")
        self.next_image()

    def next_image(self, event=None):
        """Go to the next image (stays on the last one)."""
        if self.current_index < len(self.images) - 1:
            self.current_index += 1
            self.show_image(self.current_index)
        else:
            print("Already at the last image.")

    def back_image(self, event=None):
        """Go to the previous image (stays on the first one)."""
        if self.current_index > 0:
            self.current_index -= 1
            self.show_image(self.current_index)
        else:
            print("Already at the first image.")

    def skip_10_images(self, event=None):
        """Go forward 10 images (or to the last one)."""
        if self.current_index + SKIP < len(self.images):
            self.current_index += SKIP
        else:
            self.current_index = max(len(self.images) - 1, 0)
        self.show_image(self.current_index)

    def back_10_images(self, event=None):
        """Go back 10 images (or to the first one)."""
        if self.current_index - SKIP >= 0:
            self.current_index -= SKIP
        else:
            self.current_index = 0
        self.show_image(self.current_index)

    def open_folder(self):
        """Ask for another image folder and load it (the output folder follows it unless --out was given)."""
        new_folder = filedialog.askdirectory(title="Select a new image folder")
        if new_folder:
            new_folder = os.path.normpath(new_folder)
            self.input_folder = new_folder
            if not self.custom_output:
                self.output_folder = default_output_folder(new_folder)
            if not os.path.exists(self.output_folder):
                os.makedirs(self.output_folder)
            self.images = list_images(new_folder)
            self.current_index = 0
            self.show_image(self.current_index)


def select_folder():
    """Ask for an image folder with a dialog; return '' or () if cancelled."""
    return filedialog.askdirectory(title="Select an image folder")

def parse_args(argv=None):
    """Parse the command line (FOLDER, --out)."""
    parser = argparse.ArgumentParser(
        description="Browse a folder of images and copy the ones you choose to an output folder.")
    parser.add_argument("folder", nargs="?",
                        help="image folder to open (a folder dialog is shown if omitted)")
    parser.add_argument("--out", metavar="DIR",
                        help="output folder (default: output_<folder> next to the input folder)")
    return parser.parse_args(argv)


def main(argv=None):
    """Entry point: pick an image folder (argument or dialog) and open the viewer."""
    args = parse_args(argv)
    input_folder = args.folder
    if input_folder and not os.path.isdir(input_folder):
        raise SystemExit(f"Folder not found: {input_folder}")

    root = tk.Tk()
    root.title("Image Picker")

    if not input_folder:
        input_folder = select_folder()
    if not input_folder:
        print("No input folder selected.")
        return
    input_folder = os.path.abspath(input_folder)

    output_folder = args.out or default_output_folder(input_folder)

    viewer = ImageViewer(root, input_folder, output_folder, custom_output=bool(args.out))

    # "Open Image Folder" button (packed after the viewer, so it appears below it)
    open_button = tk.Button(
        root, text="Open Image Folder", command=viewer.open_folder,
        width=20, height=2, borderwidth=1, relief="solid"
    )
    open_button.pack(anchor="nw", padx=10, pady=10)

    root.mainloop()


if __name__ == "__main__":
    main()
