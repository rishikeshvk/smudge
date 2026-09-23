import { useQuery } from "@tanstack/react-query";

import { readBuddyOptions } from "./api/@tanstack/react-query.gen";
import type { BuddyStatus } from "./api/types.gen";
import { hasStatus } from "./apiErrors";

export type Gate = "loading" | "onboarding" | "ready" | "unreachable";

// No buddy (404) means nobody has onboarded yet; any other failure means the API is out of reach.
export function gateFor(query: { data?: BuddyStatus; error: unknown }): Gate {
  if (query.data) return "ready";
  if (hasStatus(query.error, 404)) return "onboarding";
  if (query.error) return "unreachable";
  return "loading";
}

export function useBuddy() {
  return useQuery({
    ...readBuddyOptions(),
    retry: (failures, error) => !hasStatus(error, 404) && failures < 2,
  });
}
