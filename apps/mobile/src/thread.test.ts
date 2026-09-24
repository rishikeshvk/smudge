import type { ChatMessage } from "./api/types.gen";
import { chronological, olderPageFrom, PAGE_SIZE, threadRows } from "./thread";

function message(id: number, speaker: ChatMessage["speaker"]): ChatMessage {
  return {
    id,
    speaker,
    text: `message ${id}`,
    at: "2026-10-05T03:31:00Z",
    stage: null,
    turn_id: null,
    card: null,
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
