import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";

import {
  listMessagesQueryKey,
  messageStatusOptions,
  sendMessageMutation,
} from "./api/@tanstack/react-query.gen";
import { listMessages } from "./api/sdk.gen";
import type { ChatMessage, TurnStage } from "./api/types.gen";
import { isInFlight } from "./draftStage";
import { olderPageFrom, PAGE_SIZE } from "./thread";

const pagesKey = () => [...listMessagesQueryKey(), "pages"] as const;

// While the buddy is away nothing moves, so there's no point asking every second.
const POLL_MS = { available: 1_000, away: 10_000 };

// Rituals arrive on the buddy's schedule, so the thread polls while it's on screen.
export function useChatPages({ pollMs }: { pollMs?: number } = {}) {
  return useInfiniteQuery({
    queryKey: pagesKey(),
    queryFn: async ({ pageParam, signal }) => {
      const { data } = await listMessages({
        query: { before_id: pageParam, limit: PAGE_SIZE },
        signal,
        throwOnError: true,
      });
      return data;
    },
    initialPageParam: undefined as number | undefined,
    getNextPageParam: olderPageFrom,
    refetchInterval: pollMs ?? false,
  });
}

export function useSendMessage({ onFailed }: { onFailed: (text: string) => void }) {
  const queryClient = useQueryClient();
  return useMutation({
    ...sendMessageMutation(),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: pagesKey() }),
    onError: (_error, variables) => onFailed(variables.body.text),
  });
}

// Follows the turn the worker is on (the oldest unanswered message) through its real stages,
// and reloads the thread once the reply is in.
export function useTurnStage(message: ChatMessage | undefined, available: boolean): TurnStage | null {
  const queryClient = useQueryClient();
  const status = useQuery({
    ...messageStatusOptions({ path: { message_id: message?.id ?? 0 } }),
    enabled: message !== undefined,
    refetchInterval: available ? POLL_MS.available : POLL_MS.away,
  });
  const settled = status.data !== undefined && !isInFlight(status.data.message);

  useEffect(() => {
    if (settled) queryClient.invalidateQueries({ queryKey: pagesKey() });
  }, [settled, queryClient]);

  return status.data?.message.stage ?? message?.stage ?? null;
}
