import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { addCheckinMutation, readRoadmapOptions } from "./api/@tanstack/react-query.gen";
import type { TopicRef } from "./api/types.gen";
import { useBuddy } from "./buddy";
import { sealCaption } from "./roadmapProgress";

export type Sealed = { topic: TopicRef; caption: string };

// "I studied today": marks the next topic with how it went, brings up the study seal, and
// the buddy answers the check-in in chat.
export function useCheckIn() {
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
      // The roadmap, the streak and the thread all change.
      queryClient.invalidateQueries();
    },
  });

  return { checkIn, sealed };
}
