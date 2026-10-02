"""Drives the USB phone with adb: reads the screen, taps, types, records."""

import json
import random
import re
import shlex
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

DEVICE_CLIP = "/sdcard/kindred-take.mp4"
DEVICE_DUMP = "/sdcard/kindred-ui.xml"
SCREENRECORD_LIMIT = 180
BIT_RATE = 20_000_000
NODE = re.compile(r"<node [^>]*?/?>")
ATTRIBUTE = re.compile(r'(text|content-desc|bounds)="([^"]*)"')
BOUNDS = re.compile(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]")


class PhoneTimeout(Exception):
    pass


@dataclass(frozen=True)
class Element:
    text: str
    x: int
    y: int


def _adb(*args: str) -> str:
    result = subprocess.run(["adb", *args], check=True, capture_output=True)
    return result.stdout.decode()


def parse_elements(xml: str) -> list[Element]:
    elements = []
    for node in NODE.findall(xml):
        attributes = dict(ATTRIBUTE.findall(node))
        label = attributes.get("text") or attributes.get("content-desc")
        bounds = BOUNDS.search(attributes.get("bounds", ""))
        if not label or bounds is None:
            continue
        left, top, right, bottom = (int(value) for value in bounds.groups())
        elements.append(Element(label, (left + right) // 2, (top + bottom) // 2))
    return elements


class Phone:
    def __init__(self) -> None:
        self._recording: subprocess.Popen[bytes] | None = None
        self._started = 0.0
        self.taps: list[dict[str, float]] = []

    def elements(self) -> list[Element]:
        _adb("shell", "uiautomator", "dump", DEVICE_DUMP)
        return parse_elements(_adb("exec-out", "cat", DEVICE_DUMP))

    def find(self, text: str) -> Element | None:
        return next((e for e in self.elements() if text in e.text), None)

    def wait_for(self, text: str, timeout: float = 60) -> Element:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            element = self.find(text)
            if element is not None:
                return element
            time.sleep(0.5)
        raise PhoneTimeout(f"{text!r} didn't appear in {timeout:.0f} s")

    def wait_gone(self, text: str, timeout: float = 120) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.find(text) is None:
                return
            time.sleep(0.5)
        raise PhoneTimeout(f"{text!r} was still there after {timeout:.0f} s")

    def tap(self, x: int, y: int) -> None:
        if self._recording is not None:
            self.taps.append({"t": time.monotonic() - self._started, "x": x, "y": y})
        _adb("shell", "input", "tap", str(x), str(y))

    def tap_text(self, text: str, timeout: float = 30) -> None:
        element = self.wait_for(text, timeout)
        self.tap(element.x, element.y)

    def type(self, text: str) -> None:
        if not text.isascii():
            raise ValueError(f"adb can only type ASCII: {text!r}")
        # One character per call reads as a person typing; a whole string lands at once.
        for character in text:
            # `input text` reads %s as a space.
            chunk = "%s" if character == " " else character
            _adb("shell", "input", "text", shlex.quote(chunk))
            time.sleep(random.uniform(0.02, 0.09))

    def swipe(self, x1: int, y1: int, x2: int, y2: int, ms: int = 450) -> None:
        _adb("shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(ms))

    def back(self) -> None:
        _adb("shell", "input", "keyevent", "KEYCODE_BACK")

    def hide_keyboard(self) -> None:
        if "mInputShown=true" in _adb("shell", "dumpsys", "input_method"):
            self.back()

    def screenshot(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(
            subprocess.run(
                ["adb", "exec-out", "screencap", "-p"], check=True, capture_output=True
            ).stdout
        )

    def status_bar(self, hhmm: str) -> None:
        """Android demo mode: a still status bar showing the Smudge time."""
        _adb("shell", "settings", "put", "global", "sysui_demo_allowed", "1")
        commands = [
            ["enter"],
            ["clock", "-e", "hhmm", hhmm],
            ["battery", "-e", "level", "100", "-e", "plugged", "false"],
            [
                "network",
                "-e",
                "wifi",
                "show",
                "-e",
                "level",
                "4",
                "-e",
                "fully",
                "true",
            ],
            ["network", "-e", "mobile", "hide"],
            ["notifications", "-e", "visible", "false"],
        ]
        for command in commands:
            _adb(
                "shell", "am", "broadcast", "-a", "com.android.systemui.demo",
                "-e", "command", *command,
            )  # fmt: skip

    def leave_demo_mode(self) -> None:
        _adb(
            "shell", "am", "broadcast", "-a", "com.android.systemui.demo",
            "-e", "command", "exit",
        )  # fmt: skip

    def start_recording(self) -> None:
        self.taps = []
        self._recording = subprocess.Popen(
            [
                "adb", "shell", "screenrecord", "--bit-rate", str(BIT_RATE),
                "--time-limit", str(SCREENRECORD_LIMIT), DEVICE_CLIP,
            ]
        )  # fmt: skip
        self._started = time.monotonic()
        # screenrecord needs a moment before its first frame.
        time.sleep(1)

    def stop_recording(self, clip: Path, taps: Path) -> None:
        if self._recording is None:
            raise RuntimeError("no recording is running")
        time.sleep(1)
        # It may have stopped already, at its time limit.
        subprocess.run(["adb", "shell", "pkill", "-INT", "screenrecord"], check=False)
        self._recording.wait(timeout=30)
        self._recording = None
        # The file is finalised just after the process exits.
        time.sleep(1.5)
        clip.parent.mkdir(parents=True, exist_ok=True)
        _adb("pull", DEVICE_CLIP, str(clip))
        taps.write_text(json.dumps(self.taps, indent=2))
