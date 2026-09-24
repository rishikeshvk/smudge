import { getCalendars } from "expo-localization";

import type { OnboardingEntry } from "./api/types.gen";
import { ApiError } from "./apiErrors";

// Only the latest plan card can be accepted; the Planner may have revised earlier ones.
export function latestProposalId(entries: OnboardingEntry[]): number | null {
  const withProposal = entries.filter((entry) => entry.proposal !== null);
  return withProposal.at(-1)?.message.id ?? null;
}

export function sendFailureText(error: unknown): string {
  if (!(error instanceof ApiError) || error.status === null) {
    return "Couldn't reach Kindred. Check the connection and try again.";
  }
  if (error.status === 422) return "Kindred doesn't recognise this phone's timezone.";
  return "Your buddy can't reply right now. Try again in a bit.";
}

// The plan's days follow the phone's timezone, so it goes with every onboarding message.
export function deviceTimeZone(): string {
  const timeZone = getCalendars()[0]?.timeZone;
  if (!timeZone) throw new Error("This phone doesn't report a timezone");
  return timeZone;
}
