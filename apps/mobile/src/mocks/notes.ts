import type { RetrievedNote } from "@/api";

// Excerpts of the buddy's notes in aws-2week.yaml; distance only matters to retrieval.
export const notes = [
  {
    note_id: 9,
    topic_slug: "s3-encryption-versioning",
    topic_title: "S3 encryption & versioning",
    day: 9,
    body: "Day 9 part 1: S3 encryption. Good news first: since Jan 5, 2023 every new upload is encrypted automatically with SSE-S3 (server-side encryption with Amazon S3 managed keys, AES-256), for free. I don't have to switch anything on.",
    shaky: [
      "I assumed 'encrypted' meant 'private'. It doesn't: with SSE-S3, anyone allowed to read the object gets it decrypted.",
      "SSE-S3 vs SSE-KMS vs DSSE-KMS vs SSE-C. I have to look at the list every time.",
    ],
    distance: 0,
  },
  {
    note_id: 8,
    topic_slug: "s3-access",
    topic_title: "S3 access control",
    day: 8,
    body: 'Day 8: S3 access control. Starting point: buckets and objects are private by default. Nobody gets in unless something grants access. The "somethings" are: IAM policies on identities, bucket policies, ACLs (legacy), and access points.',
    shaky: [
      "I turned BPA off in my head and assumed the bucket was public. It isn't. BPA only blocks; the grant has to come from a policy. Still feels backwards.",
    ],
    distance: 0,
  },
  {
    note_id: 7,
    topic_slug: "s3-basics",
    topic_title: "S3 fundamentals",
    day: 7,
    body: "Day 7, finally S3 (Simple Storage Service). It's object storage: I don't get a disk with a file system, I get buckets and I put objects in them. Object = the data itself + metadata.",
    shaky: [
      "S3 is not a file system and I keep forgetting it. No real folders, no rename, no append.",
    ],
    distance: 0,
  },
  {
    note_id: 6,
    topic_slug: "iam-roles",
    topic_title: "IAM roles & Identity Center",
    day: 6,
    body: "IAM roles. This one finally made STS click. A role is an identity with permissions but no long-term credentials: no password, no access keys. Whoever assumes it gets temporary credentials for a role session.",
    shaky: [
      "Trust policy = who, permissions policy = what. I just know I'll edit the wrong one at some point.",
    ],
    distance: 0,
  },
] satisfies RetrievedNote[];
