"""Tests for the pure helpers (no window is opened). Run: python -m unittest discover -s tests"""

import argparse
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import image_picker  # noqa: E402
import video_frame_picker  # noqa: E402


class ParseStepsTest(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(video_frame_picker.parse_steps("40,200,800"), (40, 200, 800))
        self.assertEqual(video_frame_picker.parse_steps("2,2,2"), (2, 2, 2))

    def test_invalid(self):
        for text in ("", "1,2", "1,2,3,4", "a,b,c", "40,200,1", "0,5,5", "-4,10,10"):
            with self.subTest(text=text):
                with self.assertRaises(argparse.ArgumentTypeError):
                    video_frame_picker.parse_steps(text)

    def test_default_in_cli(self):
        args = video_frame_picker.parse_args([])
        self.assertEqual(args.steps, (40, 200, 800))
        self.assertIsNone(args.video)
        self.assertIsNone(args.out)
        args = video_frame_picker.parse_args(["v.mp4", "--out", "d", "--steps", "10,20,30"])
        self.assertEqual((args.video, args.out, args.steps), ("v.mp4", "d", (10, 20, 30)))


class FitSizeTest(unittest.TestCase):
    def test_keeps_aspect_ratio(self):
        self.assertEqual(video_frame_picker.fit_size(1280, 720, 640, 640), (640, 360))
        self.assertEqual(video_frame_picker.fit_size(720, 1280, 640, 640), (360, 640))

    def test_upscales_small_videos_to_fit(self):
        self.assertEqual(video_frame_picker.fit_size(160, 90, 640, 640), (640, 360))

    def test_unknown_size_uses_maximum(self):
        self.assertEqual(video_frame_picker.fit_size(0, 0, 800, 600), (800, 600))

    def test_never_zero(self):
        self.assertEqual(video_frame_picker.fit_size(10000, 1, 100, 100), (100, 1))
        w, h = video_frame_picker.fit_size(1, 10000, 100, 100)
        self.assertGreaterEqual(w, 1)
        self.assertEqual(h, 100)


class FrameFilenameTest(unittest.TestCase):
    def test_name(self):
        self.assertEqual(video_frame_picker.frame_filename("clip.mp4", 120), "clip_frame_120.jpg")

    def test_accents_removed(self):
        self.assertEqual(video_frame_picker.frame_filename("vídeo ação.mov", 0),
                         "video acao_frame_0.jpg")

    def test_only_last_extension_removed(self):
        self.assertEqual(video_frame_picker.frame_filename("a.b.mp4", 7), "a.b_frame_7.jpg")


class ImagePickerHelpersTest(unittest.TestCase):
    def test_output_name(self):
        self.assertEqual(image_picker.output_name("img0.jpg"), "output_img0.jpg")

    def test_default_output_folder(self):
        parent = os.path.abspath(os.path.join("some", "parent"))
        got = image_picker.default_output_folder(os.path.join(parent, "photos"))
        self.assertEqual(got, os.path.join(parent, "output_photos"))
        got = image_picker.default_output_folder(os.path.join(parent, "photos") + os.sep)
        self.assertEqual(got, os.path.join(parent, "output_photos"))

    def test_default_output_folder_current_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            old = os.getcwd()
            os.chdir(tmp)
            try:
                got = image_picker.default_output_folder(".")
                name = os.path.basename(os.path.abspath("."))
            finally:
                os.chdir(old)
        self.assertEqual(os.path.basename(got), f"output_{name}")
        self.assertNotIn("output_.", got)

    def test_list_images(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name in ("b.JPG", "a.png", "c.txt", "d.jpeg", "e.bmp", "f.tiff", "h.TIF", "g.gif"):
                open(os.path.join(tmp, name), "w").close()
            os.mkdir(os.path.join(tmp, "sub.png"))  # directories are not filtered by type
            names = image_picker.list_images(tmp)
        self.assertEqual([n for n in names if n != "sub.png"],
                         ["a.png", "b.JPG", "d.jpeg", "e.bmp", "f.tiff", "h.TIF"])

    def test_cli(self):
        args = image_picker.parse_args(["photos", "--out", "o"])
        self.assertEqual((args.folder, args.out), ("photos", "o"))


if __name__ == "__main__":
    unittest.main()
