import type { RoadmapTopic, RoadmapView } from "./api/types.gen";
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

const buddy = { name: "Juno", available: true, studying: false };

describe("buddyStatusLine", () => {
  it("says the buddy is unavailable whatever else is going on", () => {
    expect(buddyStatusLine({ ...buddy, available: false, studying: true }, roadmap)).toEqual({
      avatar: "away",
      text: "unavailable right now",
      lamp: false,
    });
  });

  it("names the topic being studied while the lamp is on", () => {
    expect(buddyStatusLine({ ...buddy, studying: true }, roadmap)).toEqual({
      avatar: "studying",
      text: "studying Topic 2",
      lamp: true,
    });
  });

  it("says when the buddy studies next, from the next unlock", () => {
    expect(buddyStatusLine(buddy, roadmap, "Asia/Kolkata").text).toBe(
      "around · studies at ~19:00",
    );
  });

  it("just says around once every topic is unlocked", () => {
    const done = { ...roadmap, topics: [topic(1, true, true)] };
    expect(buddyStatusLine(buddy, done).text).toBe("around");
  });
});
