export type Ambient = "dawn" | "day" | "dusk" | "night";

export function ambientForHour(hour: number): Ambient {
  if (hour >= 5 && hour < 11) return "dawn";
  if (hour >= 11 && hour < 17) return "day";
  if (hour >= 17 && hour < 21) return "dusk";
  return "night";
}
