// The API sends UTC instants and plain plan dates; people read them in their own timezone.

export function clockTime(instant: string, timeZone?: string): string {
  return new Intl.DateTimeFormat("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
    timeZone,
  }).format(new Date(instant));
}

// A plan date has no timezone, so it's formatted as written rather than shifted into the device's.
// Built from parts: ICU versions punctuate en-GB differently ("Thu, 24 Sept" on Android).
export function planDate(isoDate: string): string {
  const [year, month, day] = isoDate.split("-").map(Number);
  const parts = new Intl.DateTimeFormat("en-US", {
    weekday: "short",
    day: "numeric",
    month: "short",
    timeZone: "UTC",
  }).formatToParts(new Date(Date.UTC(year, month - 1, day)));
  const part = (type: Intl.DateTimeFormatPartTypes) =>
    parts.find((candidate) => candidate.type === type)?.value;
  return `${part("weekday")} ${part("day")} ${part("month")}`;
}

// "Wed 24 Sep" for an instant, on the calendar of the given timezone.
export function instantDay(instant: string, timeZone?: string): string {
  const parts = new Intl.DateTimeFormat("en-US", {
    weekday: "short",
    day: "numeric",
    month: "short",
    timeZone,
  }).formatToParts(new Date(instant));
  const part = (type: Intl.DateTimeFormatPartTypes) =>
    parts.find((candidate) => candidate.type === type)?.value;
  return `${part("weekday")} ${part("day")} ${part("month")}`;
}

const DAY_MS = 24 * 60 * 60 * 1000;

function daysBetween(from: Date, to: Date, timeZone?: string): number {
  return Math.round(
    (Date.parse(localDate(to, timeZone)) - Date.parse(localDate(from, timeZone))) / DAY_MS,
  );
}

// When something happened, as a friend would say it: today, yesterday, Sun, or 24 Sep.
export function relativeDay(instant: string, now: Date, timeZone?: string): string {
  const ago = daysBetween(new Date(instant), now, timeZone);
  if (ago <= 0) return "today";
  if (ago === 1) return "yesterday";
  const day = instantDay(instant, timeZone);
  return ago < 7 ? day.split(" ")[0] : day.split(" ").slice(1).join(" ");
}

// When something will happen: tonight at 19:00, tomorrow, or on Wed 24 Sep.
export function upcomingDay(instant: string, now: Date, timeZone?: string): string {
  const ahead = daysBetween(now, new Date(instant), timeZone);
  if (ahead <= 0) return `tonight, around ${clockTime(instant, timeZone)}`;
  if (ahead === 1) return "tomorrow";
  return `on ${instantDay(instant, timeZone)}`;
}

export function localHour(instant: Date, timeZone?: string): number {
  const hour = new Intl.DateTimeFormat("en-GB", { hour: "numeric", hourCycle: "h23", timeZone })
    .formatToParts(instant)
    .find((part) => part.type === "hour")?.value;
  return Number(hour);
}

export function localDate(instant: Date, timeZone?: string): string {
  return new Intl.DateTimeFormat("en-CA", { timeZone }).format(instant);
}

export function wallTime(time: string): string {
  return time.slice(0, 5);
}
