import type { ChatMessage, TurnStage } from "./api/types.gen";

export type DraftSteps = {
  writing: "now" | "done";
  checking: "now" | "todo";
};

const IN_FLIGHT: TurnStage[] = ["queued", "classifying", "writing", "checking"];

export function isInFlight(message: ChatMessage): boolean {
  return message.speaker === "user" && message.stage !== null && IN_FLIGHT.includes(message.stage);
}

// Shows the real turn pipeline as two steps; a redraft moves back from checking to writing.
export function draftSteps(stage: TurnStage | null): DraftSteps | null {
  switch (stage) {
    case "queued":
    case "classifying":
    case "writing":
      return { writing: "now", checking: "todo" };
    case "checking":
      return { writing: "done", checking: "now" };
    default:
      return null;
  }
}
