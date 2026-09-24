import { clockOffset } from "./kindredNow";

describe("clockOffset", () => {
  it("is how far ahead the Kindred Clock was when it was read", () => {
    const readAt = Date.parse("2026-09-23T15:00:00Z");
    expect(clockOffset("2026-09-24T15:00:00Z", readAt)).toBe(24 * 60 * 60 * 1000);
  });

  it("is zero when the Kindred Clock is on real time", () => {
    const readAt = Date.parse("2026-09-23T15:00:00Z");
    expect(clockOffset("2026-09-23T15:00:00Z", readAt)).toBe(0);
  });
});
