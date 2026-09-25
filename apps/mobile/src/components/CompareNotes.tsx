import { useQuery } from "@tanstack/react-query";
import { Text, View } from "react-native";

import { readNotebookOptions } from "@/api/@tanstack/react-query.gen";
import type { CheckinCard } from "@/api/types.gen";
import { stillShaky } from "@/shaky";

function Side({ who, lines, empty }: { who: string; lines: string[]; empty: string }) {
  return (
    <View className="flex-1 gap-1">
      <Text className="font-label text-label uppercase text-ink-muted">{who}</Text>
      {lines.length === 0 ? (
        <Text className="font-meta text-meta text-ink-muted">{empty}</Text>
      ) : (
        lines.map((line) => (
          <Text key={line} className="font-meta text-meta text-ink">
            <Text className="bg-pencil-soft">{line}</Text>
          </Text>
        ))
      )}
    </View>
  );
}

// The user's check-in next to the buddy's own shaky points on the same topic. The notebook is
// gated, so a topic the buddy hasn't studied shows nothing of it.
export function CompareNotes({ card, buddyName }: { card: CheckinCard; buddyName: string }) {
  const notebook = useQuery(readNotebookOptions());
  const note = notebook.data?.notes.find((candidate) => candidate.topic.slug === card.topic.slug);

  return (
    <View className="w-[88%] gap-3 self-end rounded-md border border-line bg-surface-raised p-3">
      <Text className="font-body-strong text-[15px] leading-[20px] text-ink">
        {`Studied ${card.topic.title} · felt ${card.feeling}`}
      </Text>
      <View className="flex-row gap-3">
        <Side who="You" lines={card.fuzzy ? [card.fuzzy] : []} empty="nothing fuzzy" />
        <Side
          who={buddyName}
          lines={note ? stillShaky(note) : []}
          empty={note ? "nothing shaky" : "hasn't studied it yet"}
        />
      </View>
    </View>
  );
}
