import type { DraftAttempt, TurnTrace } from "./api/types.gen";
import { badgeParts, markEvidence } from "./turnSummary";

const passed: DraftAttempt = {
  reply: "that's our day 14 stuff, I haven't seen it yet",
  audit: { verdict: "pass", leaked_topic_slugs: [], evidence: [], rationale: "fine" },
};

const leaked: DraftAttempt = {
  reply: "EC2 fetches credentials from the metadata service",
  audit: {
    verdict: "leak",
    leaked_topic_slugs: ["ec2-roles-metadata"],
    evidence: ["EC2 fetches credentials from the metadata service"],
    rationale: "day 14",
  },
};

function trace(overrides: Partial<TurnTrace>): TurnTrace {
  return {
    message: "how do instance roles work?",
    at: "2026-10-05T03:31:00Z",
    classification: { category: "curriculum", topic_slugs: [], rationale: "why" },
    directive: { route: "deflect", answer_topics: [], deflect_topics: [], ahead_topics: [] },
    retrieved: [],
    attempts: [passed],
    final_reply: passed.reply,
    fell_back: false,
    models: { classifier: "c", drafter: "d", auditor: "a" },
    latency_ms: 3800,
    ...overrides,
  };
}

const words = (t: TurnTrace) => badgeParts(t).map((part) => `${part.text}:${part.tone}`);

describe("badgeParts", () => {
  it("reports a clean pass", () => {
    expect(words(trace({}))).toEqual(["deflect:plain", "pass:ok", "0 retries:plain"]);
  });

  it("counts the redrafts after a caught leak", () => {
    expect(words(trace({ attempts: [leaked, passed] }))).toEqual([
      "deflect:plain",
      "pass:ok",
      "1 retry:plain",
    ]);
  });

  it("names the fallback when every draft leaked", () => {
    expect(words(trace({ attempts: [leaked, leaked], fell_back: true }))).toEqual([
      "deflect:plain",
      "fallback:leak",
      "1 retry:plain",
    ]);
  });

  it("flags an unsure classification in its own word", () => {
    const unsure = trace({
      classification: { category: "unsure", topic_slugs: [], rationale: "?" },
    });
    expect(words(unsure)).toEqual(["deflect:plain", "unsure:unsure", "pass:ok", "0 retries:plain"]);
  });

  it("shows a crisis reply as the help template, not an audit result", () => {
    const crisis = trace({
      directive: { route: "crisis", answer_topics: [], deflect_topics: [], ahead_topics: [] },
      attempts: [],
      fell_back: true,
    });
    expect(words(crisis)).toEqual(["crisis:plain", "help template:plain"]);
  });
});

describe("markEvidence", () => {
  it("highlights the quoted sentence inside the draft", () => {
    expect(markEvidence("haven't got there yet! I think X leaks, but that's day 14.", ["I think X leaks"])).toEqual([
      { text: "haven't got there yet! ", marked: false },
      { text: "I think X leaks", marked: true },
      { text: ", but that's day 14.", marked: false },
    ]);
  });

  it("leaves the draft whole when the quote isn't in it", () => {
    expect(markEvidence("all fine", ["something else"])).toEqual([{ text: "all fine", marked: false }]);
  });
});
