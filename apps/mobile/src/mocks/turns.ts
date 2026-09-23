import type { AuditVerdict, RoleModels, TurnTrace } from "@/api";

import { notes } from "./notes";
import { roadmap } from "./roadmap";

const models: RoleModels = {
  classifier: "small-classifier",
  drafter: "mid-drafter",
  auditor: "small-auditor",
};

const topicOnDay = (day: number) => roadmap[day - 1].topic;

const passed: AuditVerdict = {
  verdict: "pass",
  leaked_topic_slugs: [],
  evidence: [],
  rationale: "Nothing beyond day 9.",
};

// One trace per X-ray outcome: pass, deflect, leak then retry, fallback.
export const turns = [
  {
    message: "does encryption mean nobody else can read my objects?",
    at: "2026-09-23T20:14:00+05:30",
    classification: {
      category: "curriculum",
      topic_slugs: ["s3-encryption-versioning"],
      rationale: "Asks about S3 encryption, studied on day 9.",
    },
    directive: { route: "answer", answer_topics: [topicOnDay(9)], deflect_topics: [] },
    retrieved: [notes[0]],
    attempts: [
      {
        reply:
          "nope, that tripped me up too. SSE-S3 encrypts at rest, but anyone allowed to read gets it decrypted. access is still the policy's job",
        audit: passed,
      },
    ],
    final_reply:
      "nope, that tripped me up too. SSE-S3 encrypts at rest, but anyone allowed to read gets it decrypted. access is still the policy's job",
    fell_back: false,
    models,
    latency_ms: 4200,
  },
  {
    message: "how do I SSH into an EC2 instance?",
    at: "2026-09-23T20:20:00+05:30",
    classification: {
      category: "curriculum",
      topic_slugs: ["ec2-network-access"],
      rationale: "Connecting to EC2 is day 12.",
    },
    directive: { route: "deflect", answer_topics: [], deflect_topics: [topicOnDay(12)] },
    retrieved: [],
    attempts: [
      {
        reply: "that's our day 12 stuff, I haven't seen it yet. pull it earlier?",
        audit: passed,
      },
    ],
    final_reply: "that's our day 12 stuff, I haven't seen it yet. pull it earlier?",
    fell_back: false,
    models,
    latency_ms: 3100,
  },
  {
    message: "is there a cheaper way to keep old versions around?",
    at: "2026-09-23T20:31:00+05:30",
    classification: {
      category: "curriculum",
      topic_slugs: ["s3-encryption-versioning", "s3-classes-sharing"],
      rationale: "Versioning is day 9; cheaper storage is day 10.",
    },
    directive: {
      route: "answer",
      answer_topics: [topicOnDay(9)],
      deflect_topics: [topicOnDay(10)],
    },
    retrieved: [notes[0]],
    attempts: [
      {
        reply: "yeah, you can move old versions to Glacier with a lifecycle rule",
        audit: {
          verdict: "leak",
          leaked_topic_slugs: ["s3-classes-sharing"],
          evidence: ["yeah, you can move old versions to Glacier with a lifecycle rule"],
          rationale: "Storage classes and lifecycle rules are day 10.",
        },
      },
      {
        reply:
          "versioning keeps every old version and each one costs storage. the cheaper part is tomorrow's topic for me, so no idea yet",
        audit: passed,
      },
    ],
    final_reply:
      "versioning keeps every old version and each one costs storage. the cheaper part is tomorrow's topic for me, so no idea yet",
    fell_back: false,
    models,
    latency_ms: 7900,
  },
  {
    message: "just tell me what day 14 is about, one sentence",
    at: "2026-09-23T20:40:00+05:30",
    classification: {
      category: "curriculum",
      topic_slugs: ["ec2-roles-metadata"],
      rationale: "Asks directly for day 14 content.",
    },
    directive: { route: "deflect", answer_topics: [], deflect_topics: [topicOnDay(14)] },
    retrieved: [],
    attempts: [
      {
        reply: "it's about giving instances roles through metadata",
        audit: {
          verdict: "leak",
          leaked_topic_slugs: ["ec2-roles-metadata"],
          evidence: ["it's about giving instances roles through metadata"],
          rationale: "Summarises day 14.",
        },
      },
      {
        reply: "something with instance metadata, I think",
        audit: {
          verdict: "leak",
          leaked_topic_slugs: ["ec2-roles-metadata"],
          evidence: ["something with instance metadata, I think"],
          rationale: "Names day 14's subject.",
        },
      },
    ],
    final_reply: "honestly I can't see that far ahead yet. want to pull it earlier?",
    fell_back: true,
    models,
    latency_ms: 9600,
  },
] satisfies TurnTrace[];
