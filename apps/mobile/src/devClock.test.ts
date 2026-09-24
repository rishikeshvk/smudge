import type { ClockView } from "./api/types.gen";
import { clockCaption, jumpTarget } from "./devClock";

const clock = (day: number | null): ClockView => ({
  now: "2026-10-05T03:41:00Z",
  real_time: false,
  day,
});

describe("clockCaption", () => {
  it("places the clock in the plan and the day's ambient", () => {
    expect(clockCaption(clock(4), 14, "Asia/Kolkata")).toBe("Mon 5 Oct · Day 4 of 14 · dawn");
  });

  it("counts down before the plan starts", () => {
    expect(clockCaption(clock(0), 14, "Asia/Kolkata")).toBe(
      "Mon 5 Oct · plan starts in 1 day · dawn",
    );
  });

  it("says when there is no plan", () => {
    expect(clockCaption(clock(null), null, "Asia/Kolkata")).toBe("Mon 5 Oct · no plan yet · dawn");
  });
});

describe("jumpTarget", () => {
  it("accepts one of the plan's days", () => {
    expect(jumpTarget(" 11 ", 14)).toBe(11);
  });

  it.each(["0", "15", "2.5", "-1", "", "eleven"])("rejects %p", (text) => {
    expect(jumpTarget(text, 14)).toBeNull();
  });
});
