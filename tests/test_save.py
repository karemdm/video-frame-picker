"""Tests for saving frames: safe file names and non-ASCII folders."""

import os
import sys
import tempfile
import unittest

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import video_frame_picker  # noqa: E402


class SafeFilenameTest(unittest.TestCase):
    def test_windows_forbidden_characters_replaced(self):
        # unidecode turns the guillemets into "<<" and ">>", which Windows rejects
        name = video_frame_picker.frame_filename("«clip».mp4", 3)
        self.assertEqual(name, "__clip___frame_3.jpg")
        for ch in '<>:"/\|?*':
            self.assertNotIn(ch, video_frame_picker.frame_filename("a%sb.mp4" % ch, 1))

    def test_empty_name_gets_fallback(self):
        self.assertEqual(video_frame_picker.frame_filename("\U0001F600.mp4", 5), "video_frame_5.jpg")


class SaveFrameJpgTest(unittest.TestCase):
    def test_non_ascii_folder(self):
        frame = np.full((20, 30, 3), (10, 120, 240), np.uint8)  # BGR
        with tempfile.TemporaryDirectory() as tmp:
            folder = os.path.join(tmp, "ação 日本")
            os.makedirs(folder)
            path = os.path.join(folder, "f.jpg")
            self.assertTrue(video_frame_picker.save_frame_jpg(path, frame))
            data = np.fromfile(path, np.uint8)
            back = cv2.imdecode(data, cv2.IMREAD_COLOR)
        self.assertEqual(back.shape, frame.shape)
        self.assertLess(abs(int(back[5, 5, 2]) - 240), 6)  # red channel kept: no BGR/RGB swap

    def test_unwritable_path_returns_false(self):
        frame = np.zeros((4, 4, 3), np.uint8)
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(video_frame_picker.save_frame_jpg(os.path.join(tmp, "nope", "f.jpg"), frame))


if __name__ == "__main__":
    unittest.main()
