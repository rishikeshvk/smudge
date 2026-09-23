import type { BuddyStatus, RoadmapView } from "./api/types.gen";
import type { AvatarState } from "./components/Avatar";
import { clockTime } from "./time";

export type StatusLine = {
  avatar: AvatarState;
  text: string;
  // Lamp-coloured text means the lamp is on, so it's only for studying.
  lamp: boolean;
};

export function buddyStatusLine(
  buddy: BuddyStatus,
  roadmap: RoadmapView | undefined,
  timeZone?: string,
): StatusLine {
  if (!buddy.available) return { avatar: "away", text: "unavailable right now", lamp: false };

  const topics = roadmap?.topics ?? [];
  if (buddy.studying) {
    const studying = topics.find((topic) => topic.unlocked && !topic.buddy_studied);
    return {
      avatar: "studying",
      text: studying ? `studying ${studying.topic.title}` : "studying",
      lamp: true,
    };
  }

  // Topics unlock at the plan's study time, so the next unlock is when the buddy studies next.
  const next = topics.find((topic) => !topic.unlocked);
  return {
    avatar: "idle",
    text: next ? `around · studies at ~${clockTime(next.unlocks_at, timeZone)}` : "around",
    lamp: false,
  };
}
