"""Shared helper so GUI tests never show a window on the user's screen."""

OFFSCREEN = "+-10000+-10000"


def show_offscreen(root):
    """Map `root` far outside every monitor (and fully transparent) so it can still
    take focus and receive synthetic events without being visible."""
    root.withdraw()
    root.update_idletasks()
    try:
        root.attributes("-alpha", 0.0)
    except Exception:
        pass
    # Keep the size the app chose; only move the position.
    root.geometry(f"{root.winfo_reqwidth()}x{root.winfo_reqheight()}{OFFSCREEN}")
    root.deiconify()
    root.update()
