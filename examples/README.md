# Examples

Small inputs for trying both tools.

| File | Content |
|---|---|
| `abbey_road_15s.mp4` | 15 s of the Abbey Road zebra crossing in London at night (1280x720, no audio), for `video_frame_picker.py`. |
| `street_photos/` | Six frames from public street webcams (Abbey Road, London, and the Shinjuku crossing, Tokyo), for `image_picker.py`. |

## Which file comes from which stream

| File | Stream |
|---|---|
| `abbey_road_15s.mp4` | Abbey Road crossing, London |
| `street_photos/cam1_*.jpg` | Abbey Road crossing, London (same stream as the video) |
| `street_photos/cam2_*.jpg` | Abbey Road crossing, London (same stream, a different moment than `cam1_*`) |
| `street_photos/cam3_*.jpg` | Shinjuku crossing, Tokyo |

## Source

Captured from public live webcam streams on YouTube:

- Abbey Road crossing, London: https://www.youtube.com/watch?v=zMCea32gpmg
- Shinjuku crossing, Tokyo: https://www.youtube.com/watch?v=6dp-bvQ7RWo

People appear in public spaces and are not identifiable at this resolution. The files are included only to
demonstrate the tools. If you appear in them and want them removed, please open an issue.
