import type { RoadmapTopic, RoadmapView } from "./api/types.gen";

export type PullPreview = {
  // "tonight", "tomorrow" or "day 5": when the buddy will study the pulled topic.
  when: string;
  pulled: RoadmapTopic;
  // The topic it replaces there, which moves back a day.
  displaced: RoadmapTopic;
  lastDay: number;
};

// Mirrors the API: the slot is the first topic still locked, and the pulled topic takes it.
export function pullPreview(view: RoadmapView, slug: string): PullPreview | null {
  const displaced = view.topics.find((topic) => !topic.unlocked);
  const pulled = view.topics.find((topic) => topic.topic.slug === slug);
  if (!displaced || !pulled?.can_pull) return null;
  return {
    when: whenLabel(displaced.topic.day, view.day),
    pulled,
    displaced,
    lastDay: view.last_day,
  };
}

function whenLabel(day: number, today: number): string {
  if (day === today) return "tonight";
  if (day === today + 1) return "tomorrow";
  return `day ${day}`;
}

// "19:00", "7:30" or "0730" → "19:00:00"; anything else isn't a time.
export function parseStudyTime(text: string): string | null {
  const match = /^(\d{1,2}):?(\d{2})$/.exec(text.trim());
  if (!match) return null;
  const [hours, minutes] = [Number(match[1]), Number(match[2])];
  if (hours > 23 || minutes > 59) return null;
  return `${String(hours).padStart(2, "0")}:${match[2]}:00`;
}

// "19:00:00" → "19:00", for showing a plan time.
export function shortTime(time: string): string {
  return time.slice(0, 5);
}

export const PAUSE_DAYS = [1, 2, 3, 7];
