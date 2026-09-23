import type { ChatTurn } from "@/api";

// Plain turns only; ritual cards have no contract until M4.
export const chat = [
  { speaker: "buddy", text: "morning! today's mine is S3 encryption & versioning. doing it around 7pm, you?" },
  { speaker: "user", text: "around 8pm, after dinner" },
  {
    speaker: "buddy",
    text: "deal. I'll be done with mine by then. tell me how access control goes, I thought the block public access part was backwards",
  },
] satisfies ChatTurn[];
