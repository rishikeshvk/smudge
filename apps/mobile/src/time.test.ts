import {
  clockTime,
  instantDay,
  localDate,
  localHour,
  planDate,
  relativeDay,
  upcomingDay,
  wallTime,
} from "./time";

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

describe("instantDay", () => {
  it("names the local calendar day of an instant", () => {
    expect(instantDay("2026-10-01T20:00:00Z", "Asia/Kolkata")).toBe("Fri 2 Oct");
  });
});

describe("relativeDay", () => {
  const now = new Date("2026-10-05T05:00:00Z");
  it.each([
    ["2026-10-05T03:00:00Z", "today"],
    ["2026-10-04T14:30:00Z", "yesterday"],
    ["2026-10-02T14:30:00Z", "Fri"],
    ["2026-09-24T14:30:00Z", "24 Sep"],
  ])("calls %s %s", (instant, expected) => {
    expect(relativeDay(instant, now, "Asia/Kolkata")).toBe(expected);
  });
});

describe("upcomingDay", () => {
  const now = new Date("2026-10-05T05:00:00Z");
  it.each([
    ["2026-10-05T13:30:00Z", "tonight, around 19:00"],
    ["2026-10-06T13:30:00Z", "tomorrow"],
    ["2026-10-08T13:30:00Z", "on Thu 8 Oct"],
  ])("calls %s %s", (instant, expected) => {
    expect(upcomingDay(instant, now, "Asia/Kolkata")).toBe(expected);
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
