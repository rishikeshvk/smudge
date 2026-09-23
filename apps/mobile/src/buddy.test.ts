import { ApiError } from "./apiErrors";
import { gateFor } from "./buddy";

const buddy = { name: "Juno", available: true, studying: false };

describe("gateFor", () => {
  it("opens the app once there is a buddy", () => {
    expect(gateFor({ data: buddy, error: null })).toBe("ready");
  });

  it("sends a new user to onboarding when there is no buddy yet", () => {
    expect(gateFor({ error: new ApiError(404, { detail: "there is no buddy yet" }) })).toBe(
      "onboarding",
    );
  });

  it("reports the API as unreachable when it doesn't answer", () => {
    expect(gateFor({ error: new ApiError(null, new TypeError("Network request failed")) })).toBe(
      "unreachable",
    );
  });

  it("treats a server error as unreachable rather than as a new user", () => {
    expect(gateFor({ error: new ApiError(500, "boom") })).toBe("unreachable");
  });

  it("waits while the first answer is on its way", () => {
    expect(gateFor({ error: null })).toBe("loading");
  });
});
