import type { RoadmapTopic, RoadmapView } from "./api/types.gen";

export type Station = "done" | "here" | "level" | "todo";

export type Rails = {
  you: Station[];
  buddy: Station[];
  youFill: number;
  buddyFill: number;
  // Where the buddy's sight ends: everything from here on is fogged. null once all is unlocked.
  fogFrom: number | null;
};

const count = (topics: RoadmapTopic[], done: (topic: RoadmapTopic) => boolean) =>
  topics.filter(done).length;

// The user checks in topic by topic in plan order, so their next topic is the first unstudied.
function nextIndex(topics: RoadmapTopic[], done: (topic: RoadmapTopic) => boolean): number {
  return topics.findIndex((topic) => !done(topic));
}

export function rails(view: RoadmapView): Rails {
  const { topics } = view;
  const youNext = nextIndex(topics, (topic) => topic.user_studied);
  const buddyNext = nextIndex(topics, (topic) => topic.buddy_studied);
  // Both on the same topic share one double-ring station on the user's rail.
  const level = youNext >= 0 && youNext === buddyNext && topics[youNext].unlocked;
  const fog = topics.findIndex((topic) => !topic.unlocked);

  return {
    you: topics.map((topic, index) => {
      if (topic.user_studied) return "done";
      if (index === youNext) return level ? "level" : "here";
      return "todo";
    }),
    buddy: topics.map((topic, index) => {
      if (topic.buddy_studied) return "done";
      if (index === buddyNext && topic.unlocked && !level) return "here";
      return "todo";
    }),
    youFill: count(topics, (topic) => topic.user_studied) / topics.length,
    buddyFill: count(topics, (topic) => topic.buddy_studied) / topics.length,
    fogFrom: fog >= 0 ? fog / topics.length : null,
  };
}

// Positive when the buddy is ahead of the user.
export function gap(view: RoadmapView): number {
  return (
    count(view.topics, (topic) => topic.buddy_studied) -
    count(view.topics, (topic) => topic.user_studied)
  );
}

export function gapLine(view: RoadmapView, buddyName: string): { quiet: string; loud: string } {
  const behind = gap(view);
  const topics = (n: number) => `${n} ${n === 1 ? "topic" : "topics"}`;
  if (behind > 0) return { quiet: "You're ", loud: `${topics(behind)} behind ${buddyName}` };
  if (behind < 0) return { quiet: "You're ", loud: `${topics(-behind)} ahead of ${buddyName}` };
  return { quiet: "You're ", loud: `level with ${buddyName}` };
}

export function sightLine(view: RoadmapView, buddyName: string): string {
  const seen = view.topics.filter((topic) => topic.unlocked);
  if (seen.length === 0) return `${buddyName} hasn't seen any topic yet`;
  if (seen.length === view.topics.length) return `${buddyName} has seen the whole plan`;
  return `${buddyName} can't see past day ${seen.at(-1)?.topic.day}`;
}

// One split-weight headline per screen: a quiet phrase and one loud part.
export function headline(view: RoadmapView): { quiet: string; loud: string } {
  if (view.day < 1) {
    const wait = 1 - view.day;
    return { quiet: "Starts in ", loud: `${wait} ${wait === 1 ? "day" : "days"}` };
  }
  if (view.day > view.topics.length) return { quiet: "Plan ", loud: "complete" };
  return { quiet: `Day ${view.day}, `, loud: gap(view) === 0 ? "level" : "together" };
}

export function topicMeta(view: RoadmapView, topic: RoadmapTopic, buddyName: string): string {
  if (topic.user_studied && topic.buddy_studied) return "both done";
  if (topic.user_studied) return `you did this before ${buddyName}`;
  if (topic.buddy_studied) {
    const yourNext = view.topics.find((candidate) => !candidate.user_studied);
    return yourNext === topic ? `yours next · ${buddyName} has done it` : `${buddyName} has done it`;
  }
  if (topic.unlocked) return `${buddyName} studies this next`;
  const tomorrow = topic.topic.day === view.day + 1 ? " · tomorrow" : "";
  return `${buddyName} hasn't seen this yet${tomorrow}`;
}

export function weeks(topics: RoadmapTopic[]): { week: number; topics: RoadmapTopic[] }[] {
  const byWeek = new Map<number, RoadmapTopic[]>();
  for (const topic of topics) {
    const week = Math.ceil(topic.topic.day / 7);
    byWeek.set(week, [...(byWeek.get(week) ?? []), topic]);
  }
  return [...byWeek].map(([week, group]) => ({ week, topics: group }));
}

// The topic a check-in would mark: the user's next, in plan order.
export function nextForYou(view: RoadmapView): RoadmapTopic | undefined {
  return view.topics.find((topic) => !topic.user_studied);
}
