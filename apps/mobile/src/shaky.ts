import type { NotebookNote } from "./api/types.gen";

type Shaky = Pick<NotebookNote, "shaky" | "sorted">;

// The shaky points the user hasn't helped sort out yet.
export function stillShaky(note: Shaky): string[] {
  const done = new Set(note.sorted.map((point) => point.shaky));
  return note.shaky.filter((point) => !done.has(point));
}

// A plain count, not a score: the guardrail rules out points.
export function notebookCaption(notes: NotebookNote[]): string {
  if (notes.length === 0) return "nothing written yet";
  const plural = (n: number, word: string) => `${n} ${word}${n === 1 ? "" : "s"}`;
  const open = notes.reduce((sum, note) => sum + stillShaky(note).length, 0);
  const sorted = notes.reduce((sum, note) => sum + note.sorted.length, 0);
  const parts = [plural(notes.length, "note"), `${plural(open, "shaky bit")} left`];
  if (sorted > 0) parts.push(`${sorted} sorted with your help`);
  return parts.join(" · ");
}
