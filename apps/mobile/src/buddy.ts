import { useQuery } from "@tanstack/react-query";

import { readBuddyOptions } from "./api/@tanstack/react-query.gen";
import type { BuddyStatus } from "./api/types.gen";
import { hasStatus } from "./apiErrors";
import { type Session, useSession } from "./session";

export type Gate = "loading" | "signedOut" | "onboarding" | "ready" | "unreachable";

// No token means the invite code screen; no buddy (404) means this user hasn't onboarded
// yet; any other failure means the API is out of reach.
export function gateFor(session: Session, query: { data?: BuddyStatus; error: unknown }): Gate {
  if (!session.loaded) return "loading";
  if (session.token === null || hasStatus(query.error, 401)) return "signedOut";
  if (query.data) return "ready";
  if (hasStatus(query.error, 404)) return "onboarding";
  if (query.error) return "unreachable";
  return "loading";
}

// Chat polls while it's on screen so the lamp and the unavailable banner stay current.
export function useBuddy({ pollMs }: { pollMs?: number } = {}) {
  const session = useSession();
  return useQuery({
    ...readBuddyOptions(),
    enabled: session.token !== null,
    retry: (failures, error) => !hasStatus(error, 404) && !hasStatus(error, 401) && failures < 2,
    refetchInterval: pollMs ?? false,
  });
}
