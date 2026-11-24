"""Tests for image_picker: preview loading and ImageViewer driven with Tk events."""

import os
import sys
import tempfile
import time
import tkinter as tk
import unittest
from unittest import mock

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import image_picker  # noqa: E402


def color_at(img, x, y):
    return img.getpixel((x, y))


def read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


class LoadPreviewTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def path(self, name):
        return os.path.join(self.tmp.name, name)

    def test_letterbox_keeps_aspect_ratio(self):
        Image.new("RGB", (100, 100), (255, 0, 0)).save(self.path("sq.png"))
        preview = image_picker.load_preview(self.path("sq.png"))
        self.assertEqual(preview.size, image_picker.PREVIEW_SIZE)
        self.assertEqual(color_at(preview, 300, 200), (255, 0, 0))  # centre: the image
        self.assertEqual(color_at(preview, 10, 200), (32, 32, 32))  # sides: letterbox bars

    def test_exif_orientation_applied(self):
        # left half red, right half blue; EXIF orientation 6 = show rotated 90 degrees clockwise
        img = Image.new("RGB", (40, 20), (255, 0, 0))
        img.paste((0, 0, 255), (20, 0, 40, 20))
        exif = Image.Exif()
        exif[274] = 6
        img.save(self.path("rot.jpg"), quality=100, exif=exif)
        preview = image_picker.load_preview(self.path("rot.jpg"))
        top, bottom = color_at(preview, 300, 40), color_at(preview, 300, 360)
        self.assertGreater(top[0], 200)  # red on top
        self.assertGreater(bottom[2], 200)  # blue at the bottom
        self.assertEqual(color_at(preview, 10, 200), (32, 32, 32))  # portrait: bars at the sides

    def test_16_bit_gray_is_not_clipped_to_white(self):
        data = np.full((20, 20), 20000, np.uint16)
        Image.fromarray(data).save(self.path("deep.png"))
        preview = image_picker.load_preview(self.path("deep.png"))
        value = color_at(preview, 300, 200)[0]
        self.assertTrue(60 < value < 100, value)  # 20000 / 256 = 78

    def test_palette_and_alpha_images(self):
        Image.new("RGBA", (10, 10), (0, 255, 0, 128)).save(self.path("a.png"))
        Image.new("P", (10, 10)).save(self.path("p.png"))
        for name in ("a.png", "p.png"):
            self.assertEqual(image_picker.load_preview(self.path(name)).mode, "RGB")

    def test_corrupt_file_raises_oserror(self):
        with open(self.path("bad.jpg"), "wb") as f:
            f.write(b"not an image")
        with self.assertRaises(OSError):
            image_picker.load_preview(self.path("bad.jpg"))

    def test_file_is_closed_and_unmodified(self):
        Image.new("RGB", (10, 10)).save(self.path("x.png"))
        before = read_bytes(self.path("x.png"))
        image_picker.load_preview(self.path("x.png"))
        self.assertEqual(read_bytes(self.path("x.png")), before)
        os.rename(self.path("x.png"), self.path("y.png"))  # fails on Windows if still open


class ViewerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.inp = os.path.join(self.tmp.name, "in")
        self.out = os.path.join(self.tmp.name, "out")
        os.mkdir(self.inp)
        for i, name in enumerate(("img1.png", "img2.png", "img10.png")):
            Image.new("RGB", (30, 20), (i * 80, 0, 0)).save(os.path.join(self.inp, name))
        self.root = tk.Tk()
        self.root.deiconify()
        self.viewer = image_picker.ImageViewer(self.root, self.inp, self.out)
        self.root.update()

    def tearDown(self):
        self.root.destroy()
        self.tmp.cleanup()

    def test_natural_order_and_keys(self):
        v = self.viewer
        self.assertEqual(v.images, ["img1.png", "img2.png", "img10.png"])
        for key, expected in (("Right", 1), ("Right", 2), ("Right", 2), ("Left", 1), ("Down", 2), ("Up", 0)):
            self.root.event_generate(f"<{key}>")
            self.root.update()
            self.assertEqual(v.current_index, expected, key)

    def test_save_copies_unchanged_and_advances(self):
        v = self.viewer
        v.save_image()
        copied = os.path.join(self.out, "output_img1.png")
        self.assertEqual(read_bytes(copied), read_bytes(os.path.join(self.inp, "img1.png")))
        self.assertEqual(v.current_index, 1)
        self.assertIn("Saved output_img1.png (1 saved)", v.status_label.cget("text"))

    def test_save_never_overwrites_a_different_file(self):
        v = self.viewer
        os.makedirs(self.out)
        taken = os.path.join(self.out, "output_img1.png")
        with open(taken, "wb") as f:  # from another folder, same file name
            f.write(b"other")
        v.save_image()
        self.assertEqual(read_bytes(taken), b"other")
        self.assertEqual(read_bytes(os.path.join(self.out, "output_img1_2.png")),
                         read_bytes(os.path.join(self.inp, "img1.png")))
        self.assertIn("Saved output_img1_2.png (1 saved)", v.status_label.cget("text"))
        # the same image saved again in this session keeps its name
        v.back_image()
        v.save_image()
        self.assertEqual(sorted(os.listdir(self.out)), ["output_img1.png", "output_img1_2.png"])
        self.assertIn("Saved output_img1_2.png (2 saved)", v.status_label.cget("text"))

    def test_space_on_a_focused_button_saves_once(self):
        v = self.viewer
        for button in (v.save_button, v.next_button, self.root):
            button.focus_force()
            self.root.update()
            before = v.saved_count
            button.event_generate("<KeyPress-space>")
            button.event_generate("<KeyRelease-space>")
            time.sleep(0.3)  # Tk invokes a focused button 100 ms after Space
            self.root.update()
            self.assertEqual(v.saved_count, before + 1, button)
            v.current_index = 0
            v.show_image(0)

    def test_corrupt_image_does_not_break_browsing_or_desync_the_name(self):
        with open(os.path.join(self.inp, "img3.png"), "wb") as f:
            f.write(b"broken")
        v = self.viewer
        v.images = image_picker.list_images(self.inp)
        v.current_index = v.images.index("img3.png")
        v.show_image(v.current_index)
        self.assertIn("img3.png", v.image_name_label.cget("text"))
        self.assertIn("cannot preview", v.image_name_label.cget("text"))
        v.back_image()
        self.assertEqual(v.image_name_label.cget("text"), "Image: img2.png")

    def test_failed_save_stays_on_the_image(self):
        v = self.viewer
        with mock.patch("image_picker.shutil.copy", side_effect=PermissionError("denied")):
            v.save_image()
        self.assertEqual(v.current_index, 0)
        self.assertEqual(v.saved_count, 0)
        self.assertIn("Could not save", v.status_label.cget("text"))

    def test_empty_folder(self):
        empty = os.path.join(self.tmp.name, "empty")
        os.mkdir(empty)
        with mock.patch("image_picker.filedialog.askdirectory", return_value=empty):
            self.viewer.open_folder()
        v = self.viewer
        self.assertEqual(v.images, [])
        self.assertIn("No images found", v.image_name_label.cget("text"))
        v.save_image()
        v.next_image()
        v.back_10_images()
        v.next_10_images()
        self.assertEqual(v.current_index, 0)
        self.assertFalse(os.path.exists(self.out))

    def test_open_folder_missing_keeps_current(self):
        missing = os.path.join(self.tmp.name, "gone")
        with mock.patch("image_picker.filedialog.askdirectory", return_value=missing):
            self.viewer.open_folder()
        self.assertEqual(self.viewer.input_folder, self.inp)
        self.assertEqual(len(self.viewer.images), 3)
        self.assertIn("Could not open", self.viewer.status_label.cget("text"))

    def test_open_folder_output_follows_unless_custom(self):
        other = os.path.join(self.tmp.name, "other")
        os.mkdir(other)
        with mock.patch("image_picker.filedialog.askdirectory", return_value=other):
            self.viewer.open_folder()
            self.assertEqual(self.viewer.output_folder, os.path.join(self.tmp.name, "output_other"))
            self.viewer.custom_output = True
            self.viewer.output_folder = "fixed"
            self.viewer.open_folder()
        self.assertEqual(self.viewer.output_folder, "fixed")


if __name__ == "__main__":
    unittest.main()
