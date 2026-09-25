import json
import re
from html.parser import HTMLParser
from pathlib import Path

SITE = Path(__file__).parent
# A quote may skip part of a message; each piece around the ellipsis stays verbatim.
ELLIPSIS = "…"


class QuoteParser(HTMLParser):
    """Collects the text of every element marked data-quote, nested markup included."""

    def __init__(self) -> None:
        super().__init__()
        self.quotes: list[str] = []
        self._depth = 0
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self._depth:
            self._depth += 1
        elif any(name == "data-quote" for name, _ in attrs):
            self._depth = 1
            self._text = []

    def handle_endtag(self, tag: str) -> None:
        if not self._depth:
            return
        self._depth -= 1
        if not self._depth:
            self.quotes.append("".join(self._text))

    def handle_data(self, data: str) -> None:
        if self._depth:
            self._text.append(data)


def normalise(text: str) -> str:
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", text).strip()


def page_quotes() -> list[str]:
    parser = QuoteParser()
    parser.feed((SITE / "public" / "index.html").read_text())
    return parser.quotes


def buddy_lines() -> list[str]:
    replay = json.loads((SITE / "replay.json").read_text())
    return [
        normalise(entry["message"]["text"])
        for day in replay["days"]
        for entry in day["messages"]
        if entry["message"]["speaker"] == "buddy"
    ]


def test_the_page_quotes_the_buddy() -> None:
    assert len(page_quotes()) >= 5


def test_every_buddy_line_on_the_page_is_from_the_recorded_run() -> None:
    lines = buddy_lines()
    for quote in page_quotes():
        pieces = [normalise(piece) for piece in quote.split(ELLIPSIS)]
        assert any(all(piece in line for piece in pieces) for line in lines), quote
