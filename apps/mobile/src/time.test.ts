import { clockTime, localDate, localHour, planDate, wallTime } from "./time";

describe("clockTime", () => {
  it("shows a UTC instant as 24-hour local time", () => {
    expect(clockTime("2026-10-05T13:30:00Z", "Asia/Kolkata")).toBe("19:00");
  });
});

describe("planDate", () => {
  it("formats the date as written, whatever the device timezone", () => {
    expect(planDate("2026-10-02")).toBe("Fri 2 Oct");
  });
});

describe("localHour", () => {
  it("gives the hour on the local clock", () => {
    const instant = new Date("2026-10-05T03:41:00Z");
    expect(localHour(instant, "Asia/Kolkata")).toBe(9);
    expect(localHour(instant, "UTC")).toBe(3);
  });
});

describe("localDate", () => {
  it("gives the calendar date in the given timezone", () => {
    const lateEvening = new Date("2026-10-01T20:00:00Z");
    expect(localDate(lateEvening, "Asia/Kolkata")).toBe("2026-10-02");
    expect(localDate(lateEvening, "UTC")).toBe("2026-10-01");
  });
});

describe("wallTime", () => {
  it("drops the seconds from a plan's study time", () => {
    expect(wallTime("19:00:00")).toBe("19:00");
  });
});
