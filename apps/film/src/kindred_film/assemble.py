"""Builds the film from the takes and plates with ffmpeg."""

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from kindred_film import plates
from kindred_film.frame import FPS, HEIGHT, SCREEN, WIDTH, to_frame
from kindred_film.scenes import LOOP, SCENES, Card, Cut, Shot
from kindred_film.settings import get_settings

CROSSFADE = 0.5
CAPTION_IN = 0.4
CAPTION_RISE = 0.45
CAPTION_LIFT = 12
CAPTION_OUT = 0.25
CAPTION_OUT_LEAD = 0.5
CARD_IN = 0.6
END_OUT = 0.8
NIGHT = "0x0F1320"
PUSH = 0.03
# The push holds the phone's centre still while the frame grows around it.
PUSH_ANCHOR_X = (SCREEN.x + SCREEN.w / 2) / WIDTH
RING_SIZE = 96
RING_SECONDS = 0.35
LOOP_SIZE = (540, 1200)
LOOP_CROSSFADE = 0.3


@dataclass(frozen=True)
class Tap:
    """A scripted tap, in seconds from its take's start and phone pixels."""

    t: float
    x: int
    y: int


def take_path(take: str) -> Path:
    return get_settings().raw_dir / f"{take}.mp4"


def taps_path(take: str) -> Path:
    return get_settings().raw_dir / f"{take}.taps.json"


def scene_path(scene_id: str) -> Path:
    return get_settings().out_dir / "scenes" / f"{scene_id}.mp4"


def film_path() -> Path:
    return get_settings().out_dir / "smudge-film.mp4"


def loop_path(suffix: str) -> Path:
    return get_settings().out_dir / f"smudge-loop{suffix}"


def load_taps(take: str) -> list[Tap]:
    path = taps_path(take)
    if not path.exists():
        return []
    return [Tap(**tap) for tap in json.loads(path.read_text())]


def shot_taps(shot: Shot, taps: dict[str, list[Tap]]) -> list[Tap]:
    """Each take's taps, moved onto the shot's own timeline and the frame."""
    placed = []
    offset = 0.0
    for cut in shot.cuts:
        for tap in taps.get(cut.take, []):
            if cut.start <= tap.t < cut.end:
                x, y = to_frame(tap.x, tap.y)
                placed.append(Tap(t=offset + tap.t - cut.start, x=x, y=y))
        offset += cut.seconds
    return placed


def caption_lift(start: float) -> str:
    """The caption's offset in px: 12 at the start, easing out to 0."""
    progress = f"min(1,max(0,(t-{start})/{CAPTION_RISE}))"
    return f"{CAPTION_LIFT}*pow(1-{progress},3)"


def push_filter(window: tuple[float, float]) -> str:
    start, end = window
    zoom = f"1+{PUSH}*min(1,max(0,(it-{start})/{end - start}))"
    # Upscaled first, so the crop moves in sub-pixels and doesn't shimmer.
    return (
        f"scale={WIDTH * 2}:{HEIGHT * 2}:flags=lanczos,"
        f"zoompan=z='{zoom}':x='iw*{PUSH_ANCHOR_X:.4f}*(1-1/zoom)':"
        f"y='ih*0.5*(1-1/zoom)':d=1:s={WIDTH}x{HEIGHT}:fps={FPS}"
    )


def shot_command(shot: Shot, taps: list[Tap], out: Path) -> list[str]:
    seconds = shot.seconds
    inputs = ["-loop", "1", "-i", str(plates.plate_path(shot.id))]
    for cut in shot.cuts:
        inputs += ["-ss", f"{cut.start}", "-to", f"{cut.end}"]
        inputs += ["-i", str(take_path(cut.take))]
    mask = 1 + len(shot.cuts)
    overlay = mask + 1
    inputs += ["-loop", "1", "-i", str(plates.mask_path())]
    inputs += ["-loop", "1", "-i", str(plates.overlay_path(shot.id))]
    for _ in taps:
        inputs += ["-loop", "1", "-t", f"{RING_SECONDS}"]
        inputs += ["-i", str(plates.ring_path())]

    graph = []
    for index, cut in enumerate(shot.cuts):
        # screenrecord writes no frames while the screen is still, so a hold at the
        # end of a take is cloned from its last frame.
        graph.append(
            f"[{index + 1}:v]fps={FPS},"
            f"tpad=stop_mode=clone:stop_duration={cut.seconds},"
            f"trim=duration={cut.seconds},setpts=PTS-STARTPTS,"
            f"scale={SCREEN.w}:{SCREEN.h}:flags=lanczos,format=rgba[cut{index}]"
        )
    joined = "".join(f"[cut{index}]" for index in range(len(shot.cuts)))
    graph.append(f"{joined}concat=n={len(shot.cuts)}:v=1:a=0[phone]")
    graph.append(f"[{mask}:v]format=rgba,alphaextract[mask]")
    graph.append("[phone][mask]alphamerge[screen]")
    graph.append(
        f"[0:v]fps={FPS},format=rgba[plate];"
        f"[plate][screen]overlay={SCREEN.x}:{SCREEN.y}:shortest=1[layer0]"
    )
    layer = "layer0"
    for index, tap in enumerate(taps):
        ring = overlay + 1 + index
        fade_out = RING_SECONDS - 0.27
        graph.append(
            f"[{ring}:v]format=rgba,fade=in:st=0:d=0.08:alpha=1,"
            f"fade=out:st={fade_out:.2f}:d=0.27:alpha=1,"
            f"setpts=PTS+{tap.t:.3f}/TB[ring{index}]"
        )
        x = tap.x - RING_SIZE // 2
        y = tap.y - RING_SIZE // 2
        graph.append(
            f"[{layer}][ring{index}]overlay={x}:{y}:eof_action=pass[layer{index + 1}]"
        )
        layer = f"layer{index + 1}"
    if shot.push is not None:
        graph.append(f"[{layer}]{push_filter(shot.push)}[pushed]")
        layer = "pushed"
    caption_out = seconds - CAPTION_OUT_LEAD
    graph.append(
        f"[{overlay}:v]format=rgba,"
        f"fade=in:st={CAPTION_IN}:d={CAPTION_RISE}:alpha=1,"
        f"fade=out:st={caption_out:.2f}:d={CAPTION_OUT}:alpha=1[caption]"
    )
    graph.append(
        f"[{layer}][caption]overlay=0:'{caption_lift(CAPTION_IN)}':eval=frame,"
        f"format=yuv420p[out]"
    )
    return [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        *inputs,
        "-filter_complex",
        ";".join(graph),
        "-map",
        "[out]",
        "-t",
        f"{seconds}",
        "-r",
        f"{FPS}",
        *_intermediate(),
        str(out),
    ]


def card_command(card: Card, last: bool, out: Path) -> list[str]:
    if last:
        fade = f"fade=out:st={card.seconds - END_OUT}:d={END_OUT}"
    else:
        fade = f"fade=in:st=0:d={CARD_IN}:color={NIGHT}"
    return [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        "-loop",
        "1",
        "-i",
        str(plates.plate_path(card.id)),
        "-vf",
        f"fps={FPS},{fade},format=yuv420p",
        "-t",
        f"{card.seconds}",
        *_intermediate(),
        str(out),
    ]


def xfade_offsets(durations: list[float], overlap: float) -> list[float]:
    """When each crossfade starts, on the joined timeline."""
    offsets = []
    running = durations[0]
    for duration in durations[1:]:
        offset = running - overlap
        offsets.append(round(offset, 3))
        running = offset + duration
    return offsets


def join_command(
    clips: list[Path], durations: list[float], overlap: float, out: Path
) -> list[str]:
    inputs = []
    for clip in clips:
        inputs += ["-i", str(clip)]
    graph = []
    previous = "0:v"
    for index, offset in enumerate(xfade_offsets(durations, overlap)):
        label = f"x{index}"
        graph.append(
            f"[{previous}][{index + 1}:v]xfade=transition=fade:"
            f"duration={overlap}:offset={offset}[{label}]"
        )
        previous = label
    return [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        *inputs,
        "-filter_complex",
        ";".join(graph),
        "-map",
        f"[{previous}]",
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "slow",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(out),
    ]


def loop_clip_command(cut: Cut, out: Path) -> list[str]:
    width, height = LOOP_SIZE
    return [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        "-ss",
        f"{cut.start}",
        "-to",
        f"{cut.end}",
        "-i",
        str(take_path(cut.take)),
        "-vf",
        f"fps={FPS},scale={width}:{height}:flags=lanczos,format=yuv420p",
        *_intermediate(),
        str(out),
    ]


def _intermediate() -> list[str]:
    return ["-an", "-c:v", "libx264", "-preset", "fast", "-crf", "14"]


def _run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def build_scenes() -> list[Path]:
    taps = {
        cut.take: load_taps(cut.take)
        for scene in SCENES
        if isinstance(scene, Shot)
        for cut in scene.cuts
    }
    clips = []
    for scene in SCENES:
        out = scene_path(scene.id)
        out.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(scene, Card):
            _run(card_command(scene, last=scene is SCENES[-1], out=out))
        else:
            _run(shot_command(scene, shot_taps(scene, taps), out))
        clips.append(out)
    return clips


def build_film() -> Path:
    clips = build_scenes()
    durations = [scene.seconds for scene in SCENES]
    _run(join_command(clips, durations, CROSSFADE, film_path()))
    return film_path()


def build_loop() -> None:
    clips = []
    for index, cut in enumerate(LOOP):
        out = get_settings().out_dir / "loop" / f"{index}.mp4"
        out.parent.mkdir(parents=True, exist_ok=True)
        _run(loop_clip_command(cut, out))
        clips.append(out)
    joined = get_settings().out_dir / "loop" / "joined.mp4"
    durations = [cut.seconds for cut in LOOP]
    _run(join_command(clips, durations, LOOP_CROSSFADE, joined))
    _run(
        [
            "ffmpeg", "-y", "-loglevel", "error", "-i", str(joined),
            "-an", "-c:v", "libx264", "-preset", "slow", "-crf", "28",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            str(loop_path(".mp4")),
        ]
    )  # fmt: skip
    _run(
        [
            "ffmpeg", "-y", "-loglevel", "error", "-i", str(joined),
            "-an", "-c:v", "libvpx-vp9", "-crf", "38", "-b:v", "0",
            "-row-mt", "1", str(loop_path(".webm")),
        ]
    )  # fmt: skip
    _run(
        [
            "ffmpeg", "-y", "-loglevel", "error", "-ss", "1", "-i", str(joined),
            "-frames:v", "1", "-q:v", "3", str(loop_path("-poster.jpg")),
        ]
    )  # fmt: skip


def main() -> None:
    thumb = get_settings().raw_dir / "thumbnail-screen.png"
    plates.render(thumb if thumb.exists() else None)
    print(build_film())
    if all(take_path(cut.take).exists() for cut in LOOP):
        build_loop()
        print(loop_path(".mp4"), loop_path(".webm"))


if __name__ == "__main__":
    main()
