import type { NotebookNote } from "./api/types.gen";

// A note is new if the buddy wrote it after the notebook was last opened. Before the first
// visit there's no baseline, so nothing is new: the fog lift is for notes that arrive later.
export function isNew(note: NotebookNote, lastOpened: string | null | undefined): boolean {
  if (!lastOpened) return false;
  return Date.parse(note.written_at) > Date.parse(lastOpened);
}

export function notebookCaption(notes: NotebookNote[]): string {
  if (notes.length === 0) return "nothing written yet";
  const shaky = notes.filter((note) => note.shaky.length > 0).length;
  const plural = (n: number, word: string) => `${n} ${word}${n === 1 ? "" : "s"}`;
  return `${plural(notes.length, "note")} · ${shaky} still ${shaky === 1 ? "has" : "have"} shaky parts`;
}
