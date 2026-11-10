# video-frame-picker

Two small desktop tools (Tkinter + OpenCV + Pillow) for building image datasets by hand:

| Script | What it does |
|---|---|
| `video_frame_picker.py` | Opens a video, lets you jump through frames with the keyboard, mouse wheel or scrollbar, and saves the frames you choose as JPG. |
| `image_picker.py` | Opens a folder of images, lets you browse them and copies the ones you choose to an `output_<folder>` directory. |

## Installation

Requires Python 3.8+ (Tkinter is included in the standard Python installers for Windows and macOS; on Linux install `python3-tk`).

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## video_frame_picker.py

```bash
python video_frame_picker.py
```

A file dialog asks for a video (`.mp4`, `.mov`, `.avi`, `.3gp`).

| Key / control | Action |
|---|---|
| `→` | forward 40 frames |
| `←` | back 20 frames |
| `↓` | forward 200 frames |
| `↑` | back 100 frames |
| Mouse wheel (over the video) | down: forward 800 frames, up: back 800 frames |
| Scrollbar | seek anywhere in the video |
| `Space`, `Enter`, `S` or **Save Frame** button | save the frame on screen |
| `Q` | quit |
| **Open New Video** button | open another video |

Frames are saved in the **current working directory** as
`<video name without accents>_frame_<n>.jpg` (`<n>` = 0-based frame index).

## image_picker.py

```bash
python image_picker.py
```

A folder dialog asks for an image folder (`.png`, `.jpg`, `.jpeg`, `.bmp`, `.tiff`).
Selected images are copied to `output_<folder name>` next to the input folder.

| Key / button | Action |
|---|---|
| `→` / **Next** | next image |
| `←` / **Back** | previous image |
| `↓` / **Next 10** | forward 10 images |
| `↑` / **Back 10** | back 10 images |
| `Space`, `Enter` / **Save** | copy image to the output folder and go to the next one |
| **Open Image Folder** | choose another folder |

## Known limitations

- Frame steps (40 / 200 / 800) are hard-coded in `VideoPlayer.__init__`.
- The preview size is computed from the first video; a video opened later with **Open New Video** is shown at that same size.
- `image_picker.py` shows every image at a fixed 600x400 preview (aspect ratio not preserved; the copied file is untouched).

## License

[MIT](LICENSE)
