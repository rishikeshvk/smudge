"""Renders the film's still layers from the HTML templates with Playwright."""

from html import escape
from pathlib import Path
from string import Template

from playwright.sync_api import Page, sync_playwright

from kindred_film.frame import BEZEL, HEIGHT, SCREEN, SCREEN_RADIUS, WIDTH
from kindred_film.scenes import BUDDY, GROUNDS, SCENES, Card, Shot
from kindred_film.settings import get_settings

CAPTION_LINES = 2
CAPTION_LINE_HEIGHT = 78
WEEK = 7
RAIL_WIDTH = 336
STATION = 14


class CaptionTooLong(Exception):
    pass


def caption_html(caption: str, wash: str) -> str:
    text = escape(caption)
    if not wash:
        return text
    marked = escape(wash)
    if marked not in text:
        raise ValueError(f"wash {wash!r} isn't in the caption {caption!r}")
    return text.replace(marked, f"<mark>{marked}</mark>", 1)


def stations_html(you_day: int, buddy_day: int) -> str:
    stations = []
    for day in range(1, WEEK + 1):
        classes = []
        if day <= buddy_day:
            classes.append("buddy")
        if day == you_day:
            classes.append("you")
        stations.append(f'<span class="{" ".join(classes)}"></span>')
    return "".join(stations)


def done_width(buddy_day: int) -> str:
    """How far the lamp line runs: from the first station to the buddy's."""
    if buddy_day <= 1:
        return "0px"
    step = (RAIL_WIDTH - STATION) / (WEEK - 1)
    return f"{round(step * (min(buddy_day, WEEK) - 1))}px"


def plate_values(shot: Shot) -> dict[str, str]:
    return {
        "ground": GROUNDS[shot.ground],
        "glow": '<div class="glow-top"></div>' if shot.glow else "",
        "bezel_x": f"{SCREEN.x - BEZEL}px",
        "bezel_y": f"{SCREEN.y - BEZEL}px",
        "bezel_w": f"{SCREEN.w + 2 * BEZEL}px",
        "bezel_h": f"{SCREEN.h + 2 * BEZEL}px",
        "bezel_px": f"{BEZEL}px",
        "bezel_radius": f"{SCREEN_RADIUS + BEZEL}px",
    }


def overlay_values(shot: Shot) -> dict[str, str]:
    return {
        "meta": escape(shot.meta),
        "caption": caption_html(shot.caption, shot.wash),
        "stations": stations_html(shot.you_day, shot.buddy_day),
        "done_width": done_width(shot.buddy_day),
        "you_day": str(shot.you_day),
        "buddy": BUDDY,
        "buddy_day": str(shot.buddy_day),
    }


def plate_path(scene_id: str) -> Path:
    return get_settings().out_dir / "plates" / f"{scene_id}-plate.png"


def overlay_path(scene_id: str) -> Path:
    return get_settings().out_dir / "plates" / f"{scene_id}-overlay.png"


def mask_path() -> Path:
    return get_settings().out_dir / "plates" / "mask.png"


def ring_path() -> Path:
    return get_settings().out_dir / "plates" / "ring.png"


def thumbnail_path() -> Path:
    return get_settings().out_dir / "thumbnail.png"


def _html(name: str, values: dict[str, str]) -> str:
    templates = get_settings().templates_dir
    source = Template((templates / name).read_text()).substitute(values)
    # Relative links in the template (film.css, fonts) resolve from its folder.
    return source.replace("<head>", f'<head><base href="{templates.as_uri()}/">', 1)


def _shoot(
    page: Page, html: str, path: Path, width: int, height: int, clear: bool
) -> None:
    page.set_viewport_size({"width": width, "height": height})
    # A file page, not set_content: only a file:// page may load the fonts.
    source = path.with_suffix(".html")
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(html)
    page.goto(source.as_uri())
    page.evaluate("document.fonts.ready")
    page.screenshot(
        path=path,
        omit_background=clear,
        clip={"x": 0, "y": 0, "width": width, "height": height},
    )


def _check_caption(page: Page, shot: Shot) -> None:
    height = page.evaluate(
        "document.querySelector('.caption').getBoundingClientRect().height"
    )
    if height > CAPTION_LINES * CAPTION_LINE_HEIGHT:
        raise CaptionTooLong(f"scene {shot.id}: {shot.caption!r} runs past two lines")


def render(thumbnail_screenshot: Path | None = None) -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        for scene in SCENES:
            if isinstance(scene, Card):
                html = _html(f"{scene.template}.html", {})
                _shoot(page, html, plate_path(scene.id), WIDTH, HEIGHT, clear=False)
                continue
            plate = _html("plate.html", plate_values(scene))
            _shoot(page, plate, plate_path(scene.id), WIDTH, HEIGHT, clear=False)
            overlay = _html("overlay.html", overlay_values(scene))
            _shoot(page, overlay, overlay_path(scene.id), WIDTH, HEIGHT, clear=True)
            _check_caption(page, scene)
        mask = _html(
            "mask.html",
            {
                "width": f"{SCREEN.w}px",
                "height": f"{SCREEN.h}px",
                "radius": f"{SCREEN_RADIUS}px",
            },
        )
        _shoot(page, mask, mask_path(), SCREEN.w, SCREEN.h, clear=True)
        _shoot(page, _html("ring.html", {}), ring_path(), 96, 96, clear=True)
        if thumbnail_screenshot is not None:
            thumbnail = _html(
                "thumbnail.html", {"screenshot": thumbnail_screenshot.as_uri()}
            )
            _shoot(page, thumbnail, thumbnail_path(), 1280, 720, clear=False)
        browser.close()
