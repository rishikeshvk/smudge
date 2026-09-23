import { useQuery } from "@tanstack/react-query";

import { readTurnOptions } from "@/api/@tanstack/react-query.gen";
import { badgeParts } from "@/turnSummary";

import { XrayBadge } from "./XrayBadge";

// Fetched only while X-ray is on; a finished turn never changes, so it's fetched once.
export function TurnBadge({ turnId, onOpen }: { turnId: number; onOpen: () => void }) {
  const trace = useQuery({ ...readTurnOptions({ path: { turn_id: turnId } }), staleTime: Infinity });
  if (!trace.data) return null;
  return <XrayBadge parts={badgeParts(trace.data)} onPress={onOpen} />;
}
