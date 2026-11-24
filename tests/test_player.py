"""Tests that drive VideoPlayer with Tk events (the window is withdrawn, the main loop is not run)."""

import os
import sys
import tempfile
import time
import tkinter as tk
import unittest
from unittest import mock

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import video_frame_picker as vfp  # noqa: E402
from _tk import show_offscreen  # noqa: E402

N = 40  # frames of the synthetic clip; frame i is a flat gray of value 5 * i


def make_clip(path, frames=N, size=(64, 48)):
    writer = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"MJPG"), 10, size)
    for i in range(frames):
        writer.write(np.full((size[1], size[0], 3), 5 * i, np.uint8))
    writer.release()


class PureLogicTest(unittest.TestCase):
    def test_clamp_frame(self):
        self.assertEqual(vfp.clamp_frame(-5, 10), 0)
        self.assertEqual(vfp.clamp_frame(99, 10), 9)
        self.assertEqual(vfp.clamp_frame(3, 10), 3)
        self.assertEqual(vfp.clamp_frame(3, 0), 0)  # unknown frame count: never negative

    def test_fraction_to_frame(self):
        self.assertEqual(vfp.fraction_to_frame(0.0, 450), 0)
        self.assertEqual(vfp.fraction_to_frame(1.0, 450), 449)
        self.assertEqual(vfp.fraction_to_frame(-0.2, 450), 0)
        self.assertEqual(vfp.fraction_to_frame(1.7, 450), 449)
        self.assertEqual(vfp.fraction_to_frame(0.5, 1), 0)

    def test_resize_frame_sizes_and_interpolation(self):
        frame = np.zeros((100, 200, 3), np.uint8)
        self.assertEqual(vfp.resize_frame(frame, 100, 50).shape, (50, 100, 3))
        self.assertEqual(vfp.resize_frame(frame, 400, 200).shape, (200, 400, 3))
        # shrinking a fine checkerboard by 2 with INTER_AREA gives the average gray, not aliasing
        board = np.indices((100, 100)).sum(axis=0) % 2 * 255
        board = np.dstack([board] * 3).astype(np.uint8)
        small = vfp.resize_frame(board, 50, 50)
        self.assertTrue(np.all(np.abs(small.astype(int) - 127) <= 1))


class PlayerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.clip = os.path.join(cls.tmp.name, "clip.avi")
        make_clip(cls.clip)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.out = tempfile.TemporaryDirectory()
        with mock.patch.object(tk.Tk, "mainloop"):
            self.player = vfp.VideoPlayer(self.clip, "clip.avi", self.out.name, (4, 10, 20))
        show_offscreen(self.player.root)  # key and wheel events need a mapped window with focus
        self.player.root.focus_force()
        self.player.root.update()

    def tearDown(self):
        self.player.cap.release()
        self.player.root.destroy()
        self.out.cleanup()

    def saved(self):
        return sorted(os.listdir(self.out.name))

    def test_can_read_video(self):
        self.assertTrue(vfp.can_read_video(self.clip))
        self.assertFalse(vfp.can_read_video(os.path.join(self.tmp.name, "missing.avi")))
        bad = os.path.join(self.tmp.name, "bad.mp4")
        with open(bad, "wb") as f:
            f.write(b"not a video")
        self.assertFalse(vfp.can_read_video(bad))

    def test_saved_frame_matches_index_in_name(self):
        p = self.player
        for index in (0, 7, N - 1):
            p.goto(index)
            p.save_current_frame()
            path = os.path.join(self.out.name, f"clip_frame_{index}.jpg")
            img = cv2.imdecode(np.fromfile(path, np.uint8), cv2.IMREAD_COLOR)
            self.assertLess(abs(float(img.mean()) - 5 * index), 4, index)

    def test_keys_and_wheel_never_leave_range(self):
        p = self.player
        for _ in range(3):
            p.root.event_generate("<Up>")
            p.root.update()
        p.scroll_up()
        p.previous_frame()
        self.assertEqual(p.current_frame, 0)
        for _ in range(30):
            p.scroll_down()
        self.assertEqual(p.current_frame, N - 1)
        p.next_frame()
        p.medium_forward()
        self.assertEqual(p.current_frame, N - 1)

    def test_wheel_events(self):
        p = self.player
        p.canvas.event_generate("<MouseWheel>", delta=-120)  # Windows: down = forward
        p.canvas.event_generate("<MouseWheel>", delta=-1)  # macOS: small deltas
        p.root.update()
        self.assertEqual(p.current_frame, 40 - 1)  # 2 x 20, clamped to the last frame
        p.canvas.event_generate("<Button-4>")  # Linux wheel up
        p.root.update()
        self.assertEqual(p.current_frame, 19)

    def test_empty_video_never_goes_negative(self):
        p = self.player
        p.total_frames = 0
        p.current_frame = 0
        p.scroll_down()
        p.medium_forward()
        p.next_frame()
        self.assertEqual(p.current_frame, 0)

    def test_overestimated_frame_count_keeps_name_and_image_in_sync(self):
        p = self.player
        p.total_frames = N + 25  # the container claims more frames than it has
        p.goto(10)
        p.goto(10_000)  # clamps to the (wrong) last index
        self.assertEqual(p.total_frames, N)
        self.assertEqual(p.current_frame, N - 1)
        self.assertEqual(p.displayed_index, N - 1)
        p.save_current_frame()
        self.assertEqual(self.saved(), [f"clip_frame_{N - 1}.jpg"])

    def test_scrollbar_commands(self):
        p = self.player
        p.scroll_video("moveto", "1.0")
        self.assertEqual(p.current_frame, N - 1)
        p.scroll_video("moveto", "-0.5")
        self.assertEqual(p.current_frame, 0)
        p.scroll_video("scroll", "1", "units")  # arrow button: one frame
        self.assertEqual(p.current_frame, 1)
        p.scroll_video("scroll", "1", "pages")  # click in the trough: medium step
        self.assertEqual(p.current_frame, 11)
        p.scroll_video("scroll", "-5", "pages")
        self.assertEqual(p.current_frame, 0)

    def test_drag_outside_the_bar_is_clamped(self):
        p = self.player
        p.root.update()
        p.move_scroll(mock.Mock(x=-80))
        self.assertEqual(p.current_frame, 0)
        p.move_scroll(mock.Mock(x=10 ** 6))
        self.assertEqual(p.current_frame, N - 1)

    def test_upper_case_q_quits(self):
        p = self.player
        with mock.patch.object(p.root, "quit") as quit_mock:
            p.root.event_generate("<Q>")
            p.root.update()
        quit_mock.assert_called()
        p.cap = cv2.VideoCapture(self.clip)  # quit released it; tearDown releases again

    def test_canvas_follows_real_frame_size(self):
        p = self.player
        p.frame_width, p.frame_height = 10, 10  # as if the reported size were wrong
        p.update_display()
        self.assertEqual((p.frame_width, p.frame_height), vfp.fit_size(
            64, 48, int(p.root.winfo_screenwidth() * 0.8), int(p.root.winfo_screenheight() * 0.6)))
        self.assertEqual(int(p.canvas.cget("width")), p.frame_width)

    def test_saving_never_overwrites_a_different_file(self):
        p = self.player
        other = os.path.join(self.out.name, "clip_frame_0.jpg")
        with open(other, "wb") as f:  # a frame of another video with the same name
            f.write(b"other video")
        p.save_current_frame()
        self.assertEqual(self.saved(), ["clip_frame_0.jpg", "clip_frame_0_2.jpg"])
        with open(other, "rb") as f:
            self.assertEqual(f.read(), b"other video")
        self.assertIn("Saved clip_frame_0_2.jpg (1 saved)", p.status_var.get())
        # the same frame again in this session keeps its name instead of creating _3
        p.save_current_frame()
        self.assertEqual(self.saved(), ["clip_frame_0.jpg", "clip_frame_0_2.jpg"])
        self.assertIn("Saved clip_frame_0_2.jpg (2 saved)", p.status_var.get())

    def test_same_name_from_another_video_gets_a_suffix(self):
        p = self.player
        p.save_current_frame()
        copy = os.path.join(self.tmp.name, "sub")
        os.makedirs(copy, exist_ok=True)
        same_name = os.path.join(copy, "clip.avi")
        make_clip(same_name)
        self.assertTrue(p.open_video(same_name))
        p.save_current_frame()
        self.assertEqual(self.saved(), ["clip_frame_0.jpg", "clip_frame_0_2.jpg"])

    def test_unique_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(vfp.unique_path(tmp, "a.jpg")[0], "a.jpg")
            for name in ("a.jpg", "a_2.jpg"):
                open(os.path.join(tmp, name), "wb").close()
            name, path = vfp.unique_path(tmp, "a.jpg")
            self.assertEqual((name, path), ("a_3.jpg", os.path.join(tmp, "a_3.jpg")))

    def test_space_on_a_focused_button_saves_once(self):
        p = self.player
        for widget in (p.save_button, p.open_button, p.root):
            for f in os.listdir(self.out.name):
                os.remove(os.path.join(self.out.name, f))
            p.saved_names.clear()
            p.saved_count = 0
            widget.focus_force()
            p.root.update()
            widget.event_generate("<KeyPress-space>")
            widget.event_generate("<KeyRelease-space>")
            p.root.update()
            time.sleep(0.3)  # Tk invokes a focused button 100 ms after Space
            p.root.update()
            self.assertEqual(self.saved(), ["clip_frame_0.jpg"], widget)
            self.assertEqual(p.saved_count, 1, widget)
        # a click on the button still saves
        p.save_button.invoke()
        self.assertIn("Saved", p.status_var.get())

    def test_seeking_past_an_underreported_frame_count(self):
        p = self.player
        p.total_frames = N - 15  # the container claims fewer frames than it has
        p.goto(N - 5)
        self.assertEqual(p.current_frame, N - 5)
        self.assertEqual(p.displayed_index, N - 5)
        self.assertEqual(p.total_frames, N - 4)
        p.goto(10_000)  # far past the end: stops at the last readable frame
        self.assertEqual(p.current_frame, N - 1)
        self.assertEqual(p.total_frames, N)
        p.next_frame()  # really the end: stays
        self.assertEqual(p.current_frame, N - 1)
        p.save_current_frame()
        self.assertEqual(self.saved(), [f"clip_frame_{N - 1}.jpg"])

    def test_save_in_non_ascii_folder(self):
        p = self.player
        p.out_dir = os.path.join(self.out.name, "ação")
        p.save_current_frame()
        self.assertEqual(os.listdir(p.out_dir), ["clip_frame_0.jpg"])
        self.assertIn("Saved", p.status_var.get())


if __name__ == "__main__":
    unittest.main()
