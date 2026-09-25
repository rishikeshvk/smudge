import type { ChatMessage, StudyShareCard } from "./api/types.gen";

// The buddy's rituals; the other cards are the user's own moments.
export type Ritual = Extract<
  NonNullable<ChatMessage["card"]>,
  { kind: "morning" | "study_share" | "ask" | "night_review" }
>;

export function ritualBand(card: Ritual): string {
  switch (card.kind) {
    case "morning":
      return `Morning · Day ${card.day}`;
    case "study_share":
      return "Study share";
    case "ask":
      return "Small ask";
    case "night_review":
      return `Night review · Day ${card.day}`;
  }
}

// The ticket stub under a study share.
export function shareStub(card: StudyShareCard): string {
  if (card.shaky.length === 0) return `Day ${card.day} · no note tonight`;
  return `Day ${card.day} · ${card.shaky.length} shaky`;
}

// A card's buttons only make sense while it's the latest thing said: once the user has
// answered, they would answer twice. A night review's own flag is frozen when it's sent, so a
// check-in from the Roadmap since then comes from the live roadmap.
export function showsActions(card: Ritual, newest: boolean, checkedInToday: boolean): boolean {
  if (!newest) return false;
  if (card.kind === "night_review") return !card.checked_in_today && !checkedInToday;
  return card.kind === "morning";
}

export const NOT_TODAY = "Not today";

export function streakNumber(streak: number): string {
  return String(streak).padStart(2, "0");
}
