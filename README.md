# video-frame-picker

Two small desktop tools (Tkinter + OpenCV + Pillow) for building image datasets by hand:

| Script | What it does |
|---|---|
| `video_frame_picker.py` | Opens a video, lets you jump through frames with the keyboard, mouse wheel or scrollbar, and saves the frames you choose as JPG. |
| `image_picker.py` | Opens a folder of images, lets you browse them and copies the ones you choose to an `output_<folder>` directory. |

## Installation

Requires Python 3.8+. Tkinter is included in the standard Python installers for Windows and macOS. On Debian/Ubuntu install it separately:

```bash
sudo apt install python3-tk
```

### Linux / macOS (bash)

```bash
git clone https://github.com/karemdm/video-frame-picker.git
cd video-frame-picker
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Windows (PowerShell)

```powershell
git clone https://github.com/karemdm/video-frame-picker.git
cd video-frame-picker
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If PowerShell blocks the activation script, run `Set-ExecutionPolicy -Scope Process RemoteSigned` in that window first.

## video_frame_picker.py

```bash
python video_frame_picker.py [VIDEO] [--out DIR]
```

Without arguments a file dialog asks for a video (`.mp4`, `.mov`, `.avi`, `.3gp`). Pass a `VIDEO` path to skip the dialog and `--out DIR` to choose the folder for the saved frames (created if missing).

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

Frames are saved in `--out DIR` (default: the **current working directory**) as
`<video name without accents>_frame_<n>.jpg` (`<n>` = 0-based frame index).
A status line under the buttons confirms each save, e.g. `Saved abbey_frame_120.jpg (3 saved)`.

## image_picker.py

```bash
python image_picker.py [FOLDER] [--out DIR]
```

Without arguments a folder dialog asks for an image folder (`.png`, `.jpg`, `.jpeg`, `.bmp`, `.tiff`); pass `FOLDER` to skip it.
Selected images are copied to `--out DIR`, or by default to `output_<folder name>` next to the input folder.
A status line shows each save, e.g. `Saved output_img0.jpg (1 saved)`.

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
