import type { NotebookNote } from "./api/types.gen";
import { isFogged, notebookCaption } from "./noteFreshness";

function note(writtenAt: string, shaky: string[] = ["not sure"]): NotebookNote {
  return {
    note_id: 1,
    topic: { slug: "t1", title: "Topic 1", day: 1 },
    body: "# Day 1",
    shaky,
    sources: [],
    written_at: writtenAt,
  };
}

describe("isFogged", () => {
  it("fogs a note written after the first visit", () => {
    expect(isFogged(note("2026-10-02T14:30:00Z"), "2026-10-02T09:00:00Z", [])).toBe(true);
    expect(isFogged(note("2026-10-02T14:30:00Z"), "2026-10-02T20:00:00Z", [])).toBe(false);
  });

  it("stays lifted once the user has lifted it", () => {
    expect(isFogged(note("2026-10-02T14:30:00Z"), "2026-10-02T09:00:00Z", [1])).toBe(false);
  });

  it("fogs nothing before the notebook has ever been opened", () => {
    expect(isFogged(note("2026-10-02T14:30:00Z"), null, [])).toBe(false);
    expect(isFogged(note("2026-10-02T14:30:00Z"), undefined, [])).toBe(false);
  });
});

describe("notebookCaption", () => {
  it("counts the notes and the ones still shaky", () => {
    expect(notebookCaption([note("a"), note("b", []), note("c")])).toBe(
      "3 notes · 2 still have shaky parts",
    );
    expect(notebookCaption([note("a")])).toBe("1 note · 1 still has shaky parts");
  });

  it("says so when nothing is written yet", () => {
    expect(notebookCaption([])).toBe("nothing written yet");
  });
});
