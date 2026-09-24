import type { ChatMessage } from "./api/types.gen";
import { localDate } from "./time";

export type ThreadRow = {
  message: ChatMessage;
  // First message of a local day: a date separator goes above it.
  startsDay: boolean;
  // First of a run from one speaker: runs get more space between them than bubbles within one.
  startsRun: boolean;
  // Last of a run: that's where its time stamp goes.
  endsRun: boolean;
};

// Pages arrive newest first, each oldest first; the thread reads top to bottom, oldest first.
export function chronological(pages: ChatMessage[][]): ChatMessage[] {
  return [...pages].reverse().flat();
}

export function threadRows(messages: ChatMessage[], timeZone?: string): ThreadRow[] {
  const day = (message?: ChatMessage) => message && localDate(new Date(message.at), timeZone);
  return messages.map((message, index) => ({
    message,
    startsDay: day(messages[index - 1]) !== day(message),
    startsRun: messages[index - 1]?.speaker !== message.speaker,
    endsRun: messages[index + 1]?.speaker !== message.speaker,
  }));
}

// A buddy reply sent as several texts, one per line.
export function bubbles(text: string): string[] {
  const lines = text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
  return lines.length ? lines : [text];
}

export const PAGE_SIZE = 50;

// The id to page back from, or undefined once the oldest page has come back short.
export function olderPageFrom(page: ChatMessage[]): number | undefined {
  return page.length < PAGE_SIZE ? undefined : page[0].id;
}
