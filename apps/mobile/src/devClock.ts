import type { ClockView } from "./api/types.gen";
import { ambientForHour } from "./theme/ambient";
import { instantDay, localHour } from "./time";

export const HOUR = 1;
export const DAY_HOURS = 24;

// "Fri 2 Oct · Day 4 of 14 · dawn": where the Kindred Clock stands in the plan.
export function clockCaption(clock: ClockView, planDays: number | null, timeZone?: string): string {
  const date = instantDay(clock.now, timeZone);
  const ambient = ambientForHour(localHour(new Date(clock.now), timeZone));
  if (clock.day === null) return `${date} · no plan yet · ${ambient}`;
  if (clock.day < 1) {
    const wait = 1 - clock.day;
    return `${date} · plan starts in ${wait} ${wait === 1 ? "day" : "days"} · ${ambient}`;
  }
  const of = planDays === null ? "" : ` of ${planDays}`;
  return `${date} · Day ${clock.day}${of} · ${ambient}`;
}

// A day to jump to, or null if the text isn't one of the plan's days.
export function jumpTarget(text: string, planDays: number): number | null {
  if (!/^\d+$/.test(text.trim())) return null;
  const day = Number(text.trim());
  return day >= 1 && day <= planDays ? day : null;
}
