import type { RoadmapTopic, RoadmapView } from "./api/types.gen";
import { parseStudyTime, pullPreview, shortTime } from "./replanning";

function topic(day: number, unlocked: boolean, canPull = false): RoadmapTopic {
  return {
    topic: { slug: `t${day}`, title: `Topic ${day}`, day },
    unlocks_at: "2026-10-01T13:30:00Z",
    unlocked,
    buddy_studied: unlocked,
    user_studied: false,
    can_pull: canPull,
  };
}

function view(day: number, unlockedThrough: number): RoadmapView {
  return {
    plan_title: "Tiny",
    day,
    last_day: 4,
    study_time: "19:00:00",
    streak: 0,
    gap: 0,
    checked_in_today: false,
    topics: [1, 2, 3, 4].map((d) => topic(d, d <= unlockedThrough, d > unlockedThrough + 1)),
  };
}

describe("pullPreview", () => {
  it("pulls into tonight's slot before the buddy studies", () => {
    const preview = pullPreview(view(2, 1), "t4");

    expect(preview?.when).toBe("tonight");
    expect(preview?.displaced.topic.day).toBe(2);
    expect(preview?.lastDay).toBe(4);
  });

  it("pulls into tomorrow once tonight's topic is unlocked", () => {
    expect(pullPreview(view(2, 2), "t4")?.when).toBe("tomorrow");
  });

  it("offers nothing for a topic the API can't pull", () => {
    expect(pullPreview(view(2, 1), "t2")).toBeNull();
    expect(pullPreview(view(2, 1), "missing")).toBeNull();
  });
});

describe("parseStudyTime", () => {
  it("reads a time of day in a few spellings", () => {
    expect(parseStudyTime("19:00")).toBe("19:00:00");
    expect(parseStudyTime(" 7:30 ")).toBe("07:30:00");
    expect(parseStudyTime("0730")).toBe("07:30:00");
  });

  it("rejects anything that isn't a time", () => {
    expect(parseStudyTime("24:00")).toBeNull();
    expect(parseStudyTime("7pm")).toBeNull();
    expect(parseStudyTime("")).toBeNull();
  });
});

test("plan times drop their seconds", () => {
  expect(shortTime("19:00:00")).toBe("19:00");
});
