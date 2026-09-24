import type { BuddyStatus, MoodKind, RoadmapView } from "./api/types.gen";
import type { AvatarState } from "./components/Avatar";
import { clockTime, minutesUntil } from "./time";

export type StatusLine = {
  avatar: AvatarState;
  text: string;
  // Lamp-coloured text means the lamp is on, so it's only for studying.
  lamp: boolean;
  // How far through its study session the buddy is, from 0 to 1, while it studies.
  progress: number | null;
};

// Moods with a reason read as a friend's status; the reason names public titles only.
const MOOD_LINES: Partial<Record<MoodKind, string>> = {
  tired: "winding down",
  flat: "a bit flat",
  fried: "a bit fried",
};

export function buddyStatusLine(
  buddy: BuddyStatus,
  roadmap: RoadmapView | undefined,
  now: Date,
  timeZone?: string,
): StatusLine {
  if (!buddy.available) {
    return { avatar: "away", text: "unavailable right now", lamp: false, progress: null };
  }

  const { studying, mood } = buddy;
  if (studying) {
    const until = Date.parse(studying.until);
    const left = minutesUntil(studying.until, now);
    const started = roadmap?.topics.find((topic) => topic.topic.slug === studying.topic.slug);
    const start = started && Date.parse(started.unlocks_at);
    const progress = start ? Math.min(Math.max((now.getTime() - start) / (until - start), 0), 1) : null;
    return {
      avatar: "studying",
      text: `studying ${studying.topic.title} · ${left} min left`,
      lamp: true,
      progress,
    };
  }

  const line = MOOD_LINES[mood.kind];
  if (line && mood.reason) {
    return { avatar: "dim", text: `${line} · ${mood.reason}`, lamp: false, progress: null };
  }

  // Topics unlock at the plan's study time, so the next unlock is when the buddy studies next.
  const next = roadmap?.topics.find((topic) => !topic.unlocked);
  return {
    avatar: "idle",
    text: next ? `around · studies at ~${clockTime(next.unlocks_at, timeZone)}` : "around",
    lamp: false,
    progress: null,
  };
}
