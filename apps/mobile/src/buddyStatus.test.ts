import type { BuddyStatus, RoadmapTopic, RoadmapView } from "./api/types.gen";
import { buddyStatusLine } from "./buddyStatus";

function topic(day: number, unlocked: boolean, buddyStudied: boolean): RoadmapTopic {
  return {
    topic: { slug: `topic-${day}`, title: `Topic ${day}`, day },
    unlocks_at: `2026-10-0${day}T13:30:00Z`,
    unlocked,
    buddy_studied: buddyStudied,
    user_studied: false,
    can_pull: false,
  };
}

const roadmap: RoadmapView = {
  plan_title: "AWS fundamentals in two weeks",
  day: 2,
  last_day: 3,
  study_time: "19:00:00",
  streak: 0,
  gap: 1,
  checked_in_today: false,
  topics: [topic(1, true, true), topic(2, true, false), topic(3, false, false)],
};

const buddy: BuddyStatus = {
  name: "Juno",
  mood: { kind: "steady", reason: null },
  available: true,
  studying: null,
};
const studying = {
  topic: { slug: "topic-2", title: "Topic 2", day: 2 },
  until: "2026-10-02T14:30:00Z",
};
// Half an hour into the session from 13:30Z.
const now = new Date("2026-10-02T14:00:00Z");

describe("buddyStatusLine", () => {
  it("says the buddy is unavailable whatever else is going on", () => {
    expect(buddyStatusLine({ ...buddy, available: false, studying }, roadmap, now)).toEqual({
      avatar: "away",
      text: "unavailable right now",
      lamp: false,
      progress: null,
    });
  });

  it("names the topic, the time left and how far through the session it is", () => {
    expect(buddyStatusLine({ ...buddy, studying }, roadmap, now)).toEqual({
      avatar: "studying",
      text: "studying Topic 2 · 30 min left",
      lamp: true,
      progress: 0.5,
    });
  });

  it("shows a mood with its reason, with the lamp dimmed", () => {
    const fried = { ...buddy, mood: { kind: "fried" as const, reason: "Topic 2 was a lot" } };
    expect(buddyStatusLine(fried, roadmap, now)).toMatchObject({
      avatar: "dim",
      text: "a bit fried · Topic 2 was a lot",
    });
  });

  it("says when the buddy studies next, from the next unlock", () => {
    expect(buddyStatusLine(buddy, roadmap, now, "Asia/Kolkata").text).toBe(
      "around · studies at ~19:00",
    );
  });

  it("just says around once every topic is unlocked", () => {
    const done = { ...roadmap, topics: [topic(1, true, true)] };
    expect(buddyStatusLine(buddy, done, now).text).toBe("around");
  });
});
