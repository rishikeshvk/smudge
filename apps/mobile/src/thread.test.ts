import type { ChatMessage } from "./api/types.gen";
import { bubbles, chronological, olderPageFrom, PAGE_SIZE, threadRows } from "./thread";

function message(
  id: number,
  speaker: ChatMessage["speaker"],
  at = "2026-10-05T03:31:00Z",
): ChatMessage {
  return {
    id,
    speaker,
    text: `message ${id}`,
    at,
    stage: null,
    turn_id: null,
    card: null,
    reaction: null,
  };
}

describe("chronological", () => {
  it("puts older pages first while keeping each page's order", () => {
    const newest = [message(3, "user"), message(4, "buddy")];
    const older = [message(1, "user"), message(2, "buddy")];
    expect(chronological([newest, older]).map((m) => m.id)).toEqual([1, 2, 3, 4]);
  });
});

describe("threadRows", () => {
  it("marks where each speaker's run starts and ends", () => {
    const rows = threadRows([message(1, "user"), message(2, "user"), message(3, "buddy")]);
    expect(rows.map(({ startsRun, endsRun }) => [startsRun, endsRun])).toEqual([
      [true, false],
      [false, true],
      [true, true],
    ]);
  });

  it("marks the first message of each local day", () => {
    const rows = threadRows(
      [
        message(1, "user", "2026-10-04T17:00:00Z"),
        message(2, "buddy", "2026-10-04T18:00:00Z"),
        message(3, "user", "2026-10-04T18:40:00Z"),
      ],
      "Asia/Kolkata",
    );
    // 22:30 and 23:30 on 4 Oct in Kolkata, then 00:10 on 5 Oct.
    expect(rows.map((row) => row.startsDay)).toEqual([true, false, true]);
  });
});

describe("bubbles", () => {
  it("sends each line as its own text", () => {
    expect(bubbles("yeah, same.\n\nwhich bit keeps slipping?")).toEqual([
      "yeah, same.",
      "which bit keeps slipping?",
    ]);
  });

  it("keeps a one-line reply whole", () => {
    expect(bubbles("ha")).toEqual(["ha"]);
  });
});

describe("olderPageFrom", () => {
  it("pages back from the oldest message of a full page", () => {
    const full = Array.from({ length: PAGE_SIZE }, (_, index) => message(index + 10, "user"));
    expect(olderPageFrom(full)).toBe(10);
  });

  it("stops when a page comes back short", () => {
    expect(olderPageFrom([message(1, "user")])).toBeUndefined();
  });
});
