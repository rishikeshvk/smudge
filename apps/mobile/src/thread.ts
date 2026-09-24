import type { ChatMessage } from "./api/types.gen";

export type ThreadRow = {
  message: ChatMessage;
  // First of a run from one speaker: runs get more space between them than bubbles within one.
  startsRun: boolean;
  // Last of a run: that's where its time stamp goes.
  endsRun: boolean;
};

// Pages arrive newest first, each oldest first; the thread reads top to bottom, oldest first.
export function chronological(pages: ChatMessage[][]): ChatMessage[] {
  return [...pages].reverse().flat();
}

export function threadRows(messages: ChatMessage[]): ThreadRow[] {
  return messages.map((message, index) => ({
    message,
    startsRun: messages[index - 1]?.speaker !== message.speaker,
    endsRun: messages[index + 1]?.speaker !== message.speaker,
  }));
}

export const PAGE_SIZE = 50;

// The id to page back from, or undefined once the oldest page has come back short.
export function olderPageFrom(page: ChatMessage[]): number | undefined {
  return page.length < PAGE_SIZE ? undefined : page[0].id;
}
