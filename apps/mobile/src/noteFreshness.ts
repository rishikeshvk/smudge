import type { NotebookNote } from "./api/types.gen";

// A note stays fogged until the user lifts it, if the buddy wrote it after the notebook was
// first opened. Before the first visit there's no baseline, so nothing is fogged: the fog lift
// is for notes that arrive later.
export function isFogged(
  note: NotebookNote,
  firstOpened: string | null | undefined,
  lifted: number[],
): boolean {
  if (!firstOpened) return false;
  return Date.parse(note.written_at) > Date.parse(firstOpened) && !lifted.includes(note.note_id);
}
