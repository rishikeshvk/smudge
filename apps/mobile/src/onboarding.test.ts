import type { OnboardingEntry, PlanProposal } from "./api/types.gen";
import { ApiError } from "./apiErrors";
import { latestProposalId, sendFailureText } from "./onboarding";

const proposal: PlanProposal = {
  curriculum_slug: "aws-2week",
  title: "AWS fundamentals in two weeks",
  start_date: "2026-10-02",
  study_time: "19:00:00",
  hours_per_day: 1,
  topics: [],
};

function entry(id: number, withProposal: boolean): OnboardingEntry {
  return {
    message: {
      id,
      speaker: "buddy",
      text: "here's the plan",
      at: "2026-10-01T09:00:00Z",
      stage: null,
      turn_id: null,
    },
    proposal: withProposal ? proposal : null,
  };
}

describe("latestProposalId", () => {
  it("picks the most recent reply that carried a plan card", () => {
    expect(latestProposalId([entry(1, true), entry(2, false), entry(3, true), entry(4, false)])).toBe(3);
  });

  it("is null until the Planner has proposed anything", () => {
    expect(latestProposalId([entry(1, false)])).toBeNull();
  });
});

describe("sendFailureText", () => {
  it("says the server is out of reach when there was no answer", () => {
    expect(sendFailureText(new ApiError(null, new TypeError("Network request failed")))).toMatch(
      /Couldn't reach Kindred/,
    );
  });

  it("names the timezone problem", () => {
    expect(sendFailureText(new ApiError(422, { detail: "unknown timezone" }))).toMatch(/timezone/);
  });

  it("treats other failures as the buddy being unavailable", () => {
    expect(sendFailureText(new ApiError(503, "down"))).toMatch(/can't reply right now/);
  });
});
