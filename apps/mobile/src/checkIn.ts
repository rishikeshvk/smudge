import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import {
  addCheckinMutation,
  readRoadmapOptions,
  readRoadmapQueryKey,
} from "./api/@tanstack/react-query.gen";
import type { TopicRef } from "./api/types.gen";
import { useBuddy } from "./buddy";
import { sealCaption } from "./roadmapProgress";

export type Sealed = { topic: TopicRef; caption: string };

// "I studied today", from the roadmap or a night review: marks the next topic and brings up
// the study seal.
export function useCheckIn({ onCheckedIn }: { onCheckedIn?: (topic: TopicRef) => void } = {}) {
  const queryClient = useQueryClient();
  const buddy = useBuddy();
  const roadmap = useQuery(readRoadmapOptions());
  const [sealed, setSealed] = useState<Sealed | null>(null);

  const checkIn = useMutation({
    ...addCheckinMutation(),
    onSuccess: (topic) => {
      if (roadmap.data && buddy.data) {
        setSealed({ topic, caption: sealCaption(roadmap.data, topic, buddy.data.name) });
      }
      queryClient.invalidateQueries({ queryKey: readRoadmapQueryKey() });
      onCheckedIn?.(topic);
    },
  });

  return { checkIn, sealed, closeSeal: () => setSealed(null) };
}
