import { ambientForHour } from "./ambient";

describe("ambientForHour", () => {
  it.each([
    [5, "dawn"],
    [10, "dawn"],
    [11, "day"],
    [16, "day"],
    [17, "dusk"],
    [20, "dusk"],
    [21, "night"],
    [0, "night"],
    [4, "night"],
  ])("puts hour %i in the %s ground", (hour, ambient) => {
    expect(ambientForHour(hour)).toBe(ambient);
  });
});
