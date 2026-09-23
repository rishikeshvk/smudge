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
