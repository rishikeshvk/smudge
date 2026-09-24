import type { ChatMessage } from "./api/types.gen";
import { draftSteps, isInFlight } from "./draftStage";

function message(overrides: Partial<ChatMessage>): ChatMessage {
  return {
    id: 1,
    speaker: "user",
    text: "is a role just a group?",
    at: "2026-10-05T03:31:00Z",
    stage: "queued",
    turn_id: null,
    ...overrides,
  };
}

describe("draftSteps", () => {
  it.each(["queued", "classifying", "writing"] as const)("shows writing while %s", (stage) => {
    expect(draftSteps(stage)).toEqual({ writing: "now", checking: "todo" });
  });

  it("shows the spoiler check once the auditor has the draft", () => {
    expect(draftSteps("checking")).toEqual({ writing: "done", checking: "now" });
  });

  it.each(["answered", "failed", null] as const)("shows nothing when %s", (stage) => {
    expect(draftSteps(stage)).toBeNull();
  });
});

describe("isInFlight", () => {
  it("follows the user's messages until they are answered", () => {
    expect(isInFlight(message({ stage: "checking" }))).toBe(true);
    expect(isInFlight(message({ stage: "answered" }))).toBe(false);
    expect(isInFlight(message({ stage: "failed" }))).toBe(false);
  });

  it("never treats the buddy's own messages as in flight", () => {
    expect(isInFlight(message({ speaker: "buddy", stage: null, turn_id: 3 }))).toBe(false);
  });
});
