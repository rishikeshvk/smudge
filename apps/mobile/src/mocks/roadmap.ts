import type { RoadmapEntry } from "@/api";

// aws-2week.yaml; the buddy has studied through day 9.
export const roadmap = [
  { topic: { slug: "cloud-basics", title: "What AWS is & global infrastructure", day: 1 }, unlocked: true },
  { topic: { slug: "account-billing", title: "Your AWS account, root user & billing", day: 2 }, unlocked: true },
  { topic: { slug: "iam-intro", title: "Shared responsibility & IAM overview", day: 3 }, unlocked: true },
  { topic: { slug: "iam-users-groups", title: "IAM users, groups & credentials", day: 4 }, unlocked: true },
  { topic: { slug: "iam-policies", title: "IAM policies & policy evaluation", day: 5 }, unlocked: true },
  { topic: { slug: "iam-roles", title: "IAM roles & Identity Center", day: 6 }, unlocked: true },
  { topic: { slug: "s3-basics", title: "S3 fundamentals", day: 7 }, unlocked: true },
  { topic: { slug: "s3-access", title: "S3 access control", day: 8 }, unlocked: true },
  { topic: { slug: "s3-encryption-versioning", title: "S3 encryption & versioning", day: 9 }, unlocked: true },
  { topic: { slug: "s3-classes-sharing", title: "S3 storage classes & sharing", day: 10 }, unlocked: false },
  { topic: { slug: "ec2-basics", title: "EC2 fundamentals", day: 11 }, unlocked: false },
  { topic: { slug: "ec2-network-access", title: "EC2 networking & connecting", day: 12 }, unlocked: false },
  { topic: { slug: "ec2-storage-lifecycle", title: "EC2 storage & instance lifecycle", day: 13 }, unlocked: false },
  { topic: { slug: "ec2-roles-metadata", title: "User data, instance metadata & roles for EC2", day: 14 }, unlocked: false },
] satisfies RoadmapEntry[];
