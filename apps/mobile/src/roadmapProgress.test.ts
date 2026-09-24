import type { RoadmapTopic, RoadmapView } from "./api/types.gen";
import {
  gapLine,
  headline,
  nextForYou,
  rails,
  sealCaption,
  sightLine,
  topicMeta,
  weeks,
} from "./roadmapProgress";

function topic(
  day: number,
  { unlocked = false, buddy = false, user = false } = {},
): RoadmapTopic {
  return {
    topic: { slug: `t${day}`, title: `Topic ${day}`, day },
    unlocks_at: "2026-10-01T13:30:00Z",
    unlocked,
    buddy_studied: buddy,
    user_studied: user,
    can_pull: false,
  };
}

// Day 3 of 5: the buddy has studied 1–3, the user 1–2, and days 4–5 are still locked.
const behind: RoadmapView = {
  plan_title: "Tiny",
  day: 3,
  last_day: 5,
  study_time: "19:00:00",
  streak: 2,
  gap: 1,
  checked_in_today: false,
  topics: [
    topic(1, { unlocked: true, buddy: true, user: true }),
    topic(2, { unlocked: true, buddy: true, user: true }),
    topic(3, { unlocked: true, buddy: true }),
    topic(4),
    topic(5),
  ],
};

describe("rails", () => {
  it("marks each learner's done topics, the user's next, and the fog", () => {
    const view = rails(behind);
    expect(view.you).toEqual(["done", "done", "here", "todo", "todo"]);
    expect(view.buddy).toEqual(["done", "done", "done", "todo", "todo"]);
    expect(view.youFill).toBeCloseTo(0.4);
    expect(view.buddyFill).toBeCloseTo(0.6);
    expect(view.fogFrom).toBeCloseTo(0.6);
  });

  it("merges both learners into one level station on the same topic", () => {
    const level = {
      ...behind,
      topics: [
        topic(1, { unlocked: true, buddy: true, user: true }),
        topic(2, { unlocked: true }),
        topic(3),
      ],
    };
    expect(rails(level).you).toEqual(["done", "level", "todo"]);
    expect(rails(level).buddy).toEqual(["done", "todo", "todo"]);
  });

  it("shows the buddy's current station while it hasn't studied an unlocked topic", () => {
    const studying = {
      ...behind,
      topics: [topic(1, { unlocked: true, buddy: true }), topic(2, { unlocked: true }), topic(3)],
    };
    expect(rails(studying).buddy).toEqual(["done", "here", "todo"]);
  });

  it("clears the fog once everything is unlocked", () => {
    const open = { ...behind, topics: [topic(1, { unlocked: true })] };
    expect(rails(open).fogFrom).toBeNull();
  });
});

describe("gapLine", () => {
  it("states the gap plainly, without guilt", () => {
    expect(gapLine(behind, "Juno")).toEqual({ quiet: "You're ", loud: "1 topic behind Juno" });
  });

  it("says when you're level or ahead", () => {
    const level = { ...behind, topics: [topic(1, { unlocked: true, buddy: true, user: true })] };
    expect(gapLine(level, "Juno").loud).toBe("level with Juno");
    const ahead = { ...behind, topics: [topic(1, { user: true }), topic(2, { user: true })] };
    expect(gapLine(ahead, "Juno").loud).toBe("2 topics ahead of Juno");
  });
});

describe("headline", () => {
  it("counts down before the plan starts", () => {
    expect(headline({ ...behind, day: 0 })).toEqual({ quiet: "Starts in ", loud: "1 day" });
    expect(headline({ ...behind, day: -2 })).toEqual({ quiet: "Starts in ", loud: "3 days" });
  });

  it("names the day and whether you're level", () => {
    expect(headline(behind)).toEqual({ quiet: "Day 3, ", loud: "together" });
  });

  it("isn't complete until the finish day a pause moved", () => {
    expect(headline({ ...behind, day: 6, last_day: 6 })).toEqual({ quiet: "Day 6, ", loud: "together" });
    expect(headline({ ...behind, day: 7, last_day: 6 })).toEqual({ quiet: "Plan ", loud: "complete" });
  });
});

describe("sightLine", () => {
  it("says how far the buddy can see", () => {
    expect(sightLine(behind, "Juno")).toBe("Juno can't see past day 3");
    expect(sightLine({ ...behind, topics: [topic(1)] }, "Juno")).toBe("Juno hasn't seen any topic yet");
  });
});

describe("topicMeta", () => {
  it("describes each row from both learners' progress", () => {
    const [first, , third, fourth, fifth] = behind.topics;
    expect(topicMeta(behind, first, "Juno")).toBe("both done");
    expect(topicMeta(behind, third, "Juno")).toBe("yours next · Juno has done it");
    expect(topicMeta(behind, fourth, "Juno")).toBe("Juno hasn't seen this yet · tomorrow");
    expect(topicMeta(behind, fifth, "Juno")).toBe("Juno hasn't seen this yet");
  });
});

describe("weeks", () => {
  it("groups days into weeks of seven", () => {
    const fortnight = Array.from({ length: 14 }, (_, index) => topic(index + 1));
    const view = { ...behind, last_day: 14, topics: fortnight };
    expect(weeks(view).map((group) => [group.week, group.days.length])).toEqual([
      [1, 7],
      [2, 7],
    ]);
  });

  it("shows a paused day as a day without a topic", () => {
    const view = { ...behind, last_day: 4, topics: [topic(1), topic(2), topic(4)] };
    const [week] = weeks(view);
    expect(week.days.map((day) => [day.day, day.topic?.topic.day ?? null])).toEqual([
      [1, 1],
      [2, 2],
      [3, null],
      [4, 4],
    ]);
  });
});

describe("nextForYou", () => {
  it("is the topic a check-in would mark", () => {
    expect(nextForYou(behind)?.topic.day).toBe(3);
  });
});

describe("sealCaption", () => {
  it("says what the check-in sealed and the gap it leaves", () => {
    const sealed = behind.topics[2].topic;

    expect(sealCaption(behind, sealed, "Juno")).toBe(
      `${sealed.title} is sealed on your roadmap. You're level with Juno now.`,
    );
  });
});
