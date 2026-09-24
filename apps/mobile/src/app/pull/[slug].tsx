import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { router, useLocalSearchParams } from "expo-router";
import { Text, View } from "react-native";

import { pullTopicMutation, readRoadmapOptions } from "@/api/@tanstack/react-query.gen";
import { useBuddy } from "@/buddy";
import { Button } from "@/components/Button";
import { Sheet } from "@/components/Sheet";
import { pullPreview } from "@/replanning";

function Row({ label, value }: { label: string; value: string }) {
  return (
    <View className="flex-row gap-3">
      <Text className="w-[72px] font-label text-label uppercase text-ink-muted">{label}</Text>
      <Text className="flex-1 font-meta text-meta text-ink">{value}</Text>
    </View>
  );
}

export default function PullEarlier() {
  const { slug } = useLocalSearchParams<{ slug: string }>();
  const queryClient = useQueryClient();
  const buddy = useBuddy();
  const roadmap = useQuery(readRoadmapOptions());
  const pull = useMutation({
    ...pullTopicMutation(),
    // Moving topics changes what every screen may show.
    onSuccess: () => queryClient.invalidateQueries().then(() => router.back()),
  });

  const preview = roadmap.data && pullPreview(roadmap.data, slug);
  const name = buddy.data?.name ?? "Your buddy";

  return (
    <Sheet onClose={() => router.back()}>
      {preview ? (
        <>
          <View className="gap-2">
            <Text className="font-label text-label uppercase text-ink-muted">
              {`Day ${preview.pulled.topic.day} → ${preview.when}`}
            </Text>
            <Text accessibilityRole="header" className="font-title text-title text-ink">
              {`Pull ${preview.pulled.topic.title} to ${preview.when}?`}
            </Text>
            <Text className="font-body text-body text-ink">
              {`${name} studies it ${preview.when} instead of ${preview.displaced.topic.title}, for real: it hasn't seen it yet. Everything after moves back a day.`}
            </Text>
          </View>
          <View className="gap-1 rounded-sm bg-surface-sunken p-3">
            <Row label={preview.when} value={preview.pulled.topic.title} />
            <Row
              label={`Day ${preview.displaced.topic.day + 1}`}
              value={preview.displaced.topic.title}
            />
            <Row label="Finish" value={`unchanged · day ${preview.lastDay}`} />
          </View>
          <View className="gap-2">
            <Button
              label={pull.isPending ? "Pulling…" : `Pull to ${preview.when}`}
              variant="primary"
              disabled={pull.isPending}
              onPress={() => pull.mutate({ body: { slug } })}
            />
            <Button label="Keep the plan" variant="text" onPress={() => router.back()} />
          </View>
          {pull.isError && (
            <Text className="font-meta text-meta text-leak">
              Couldn&apos;t move that topic. The plan may have changed; try again.
            </Text>
          )}
        </>
      ) : (
        <Text className="font-body text-body text-ink-muted">
          That topic can&apos;t be pulled earlier any more.
        </Text>
      )}
    </Sheet>
  );
}
