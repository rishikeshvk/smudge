import type { AskCard, MorningCard, NightReviewCard, StudyShareCard } from "./api/types.gen";
import { checkInMessage, ritualBand, shareStub, showsActions, streakNumber } from "./rituals";

const topic = { slug: "s3-encryption", title: "S3 encryption", day: 9 };
const morning: MorningCard = {
  kind: "morning",
  day: 9,
  you: topic,
  buddy: topic,
  quick_replies: ["Around the same time"],
};
const share: StudyShareCard = { kind: "study_share", day: 9, topic, shaky: ["why at rest?"] };
const ask: AskCard = { kind: "ask", note_id: 3, topic };
const night: NightReviewCard = {
  kind: "night_review",
  day: 9,
  streak: 9,
  gap: 1,
  checked_in_today: false,
};

test("bands name the ritual and its day", () => {
  expect(ritualBand(morning)).toBe("Morning · Day 9");
  expect(ritualBand(share)).toBe("Study share");
  expect(ritualBand(ask)).toBe("Small ask");
  expect(ritualBand(night)).toBe("Night review · Day 9");
});

test("the stub counts shaky points, or says there's no note", () => {
  expect(shareStub(share)).toBe("Day 9 · 1 shaky");
  expect(shareStub({ ...share, shaky: [] })).toBe("Day 9 · no note tonight");
});

test("only the newest morning or unanswered night review offers buttons", () => {
  expect(showsActions(morning, true)).toBe(true);
  expect(showsActions(morning, false)).toBe(false);
  expect(showsActions(night, true)).toBe(true);
  expect(showsActions({ ...night, checked_in_today: true }, true)).toBe(false);
  expect(showsActions(share, true)).toBe(false);
});

test("a check-in from the night review reads like the user wrote it", () => {
  expect(checkInMessage(topic)).toBe("I studied today · finished S3 encryption");
});

test("the streak shows two digits", () => {
  expect(streakNumber(9)).toBe("09");
  expect(streakNumber(12)).toBe("12");
});
