import type { NotebookNote } from "./api/types.gen";
import { notebookCaption, stillShaky } from "./shaky";

function note(shaky: string[], sorted: string[] = []): NotebookNote {
  return {
    note_id: 1,
    topic: { slug: "t1", title: "Topic 1", day: 1 },
    body: "# Day 1",
    shaky,
    sorted: sorted.map((point) => ({
      shaky: point,
      insight: "got it",
      sorted_at: "2026-10-02T00:05:00Z",
    })),
    sources: [],
    written_at: "2026-10-01T14:30:00Z",
  };
}

describe("stillShaky", () => {
  it("leaves out what the user helped sort out", () => {
    expect(stillShaky(note(["a", "b"], ["a"]))).toEqual(["b"]);
  });
});

describe("notebookCaption", () => {
  it("counts the notes, the shaky bits left and what was sorted", () => {
    expect(notebookCaption([note(["a", "b"], ["a"]), note(["c"])])).toBe(
      "2 notes · 2 shaky bits left · 1 sorted with your help",
    );
    expect(notebookCaption([note(["a"])])).toBe("1 note · 1 shaky bit left");
  });

  it("says so when nothing is written yet", () => {
    expect(notebookCaption([])).toBe("nothing written yet");
  });
});
