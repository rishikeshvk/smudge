from dataclasses import dataclass

WIDTH = 1920
HEIGHT = 1080
FPS = 30

# The phone records 1080×2400; the screen sits at the same 9:20 on the frame.
DEVICE_WIDTH = 1080
DEVICE_HEIGHT = 2400


@dataclass(frozen=True)
class Rect:
    x: int
    y: int
    w: int
    h: int


SCREEN = Rect(x=1248, y=60, w=432, h=960)
SCREEN_RADIUS = 44
BEZEL = 3


def to_frame(device_x: int, device_y: int) -> tuple[int, int]:
    """Where a tap on the phone lands on the 1920×1080 frame."""
    scale = SCREEN.w / DEVICE_WIDTH
    return SCREEN.x + round(device_x * scale), SCREEN.y + round(device_y * scale)
