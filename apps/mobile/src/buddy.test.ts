import type { BuddyStatus } from "./api/types.gen";
import { ApiError } from "./apiErrors";
import { gateFor } from "./buddy";
import type { Session } from "./session";

const buddy: BuddyStatus = {
  name: "Juno",
  mood: { kind: "steady", reason: null },
  available: true,
  studying: null,
};

const signedIn: Session = { loaded: true, token: "t" };

describe("gateFor", () => {
  it("waits for the saved sign-in to load", () => {
    expect(gateFor({ loaded: false, token: null }, { error: null })).toBe("loading");
  });

  it("asks for an invite code when nobody is signed in", () => {
    expect(gateFor({ loaded: true, token: null }, { error: null })).toBe("signedOut");
  });

  it("asks for a code again when the API turns the token away", () => {
    expect(gateFor(signedIn, { error: new ApiError(401, { detail: "sign in" }) })).toBe(
      "signedOut",
    );
  });

  it("opens the app once there is a buddy", () => {
    expect(gateFor(signedIn, { data: buddy, error: null })).toBe("ready");
  });

  it("sends a new user to onboarding when there is no buddy yet", () => {
    expect(gateFor(signedIn, { error: new ApiError(404, { detail: "there is no buddy yet" }) })).toBe(
      "onboarding",
    );
  });

  it("reports the API as unreachable when it doesn't answer", () => {
    expect(gateFor(signedIn, { error: new ApiError(null, new TypeError("Network request failed")) })).toBe(
      "unreachable",
    );
  });

  it("treats a server error as unreachable rather than as a new user", () => {
    expect(gateFor(signedIn, { error: new ApiError(500, "boom") })).toBe("unreachable");
  });

  it("waits while the first answer is on its way", () => {
    expect(gateFor(signedIn, { error: null })).toBe("loading");
  });
});
