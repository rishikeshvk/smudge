import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { ScrollView, Text, View } from "react-native";

import {
  addCheckinMutation,
  readRoadmapOptions,
  readRoadmapQueryKey,
} from "@/api/@tanstack/react-query.gen";
import type { RoadmapView, TopicRef } from "@/api/types.gen";
import { useBuddy } from "@/buddy";
import { Button } from "@/components/Button";
import { LoadState } from "@/components/LoadState";
import { Rail } from "@/components/Rail";
import { Screen } from "@/components/Screen";
import { ScreenHeader } from "@/components/ScreenHeader";
import { StudySeal } from "@/components/StudySeal";
import { TopicRow } from "@/components/TopicRow";
import {
  gapLine,
  headline,
  nextForYou,
  rails,
  sightLine,
  topicMeta,
  weeks,
} from "@/roadmapProgress";

function Hero({ view, buddyName }: { view: RoadmapView; buddyName: string }) {
  const title = headline(view);
  const track = rails(view);
  const gap = gapLine(view, buddyName);

  return (
    <View className="gap-[14px] rounded-md border border-line bg-surface-raised p-4">
      <View className="flex-row items-end justify-between">
        <View className="flex-1">
          <Text className="font-label text-label uppercase text-ink-muted">
            {`${view.plan_title} · ${view.topics.length} days`}
          </Text>
          <Text className="font-display-light text-display text-ink">
            {title.quiet}
            <Text className="font-display-bold">{title.loud}</Text>
          </Text>
        </View>
        {view.day >= 1 && (
          <View className="items-start gap-[2px]">
            <Text
              className="font-counter text-counter text-ink"
              style={{ fontVariant: ["tabular-nums"] }}
            >
              {String(Math.min(view.day, view.topics.length)).padStart(2, "0")}
            </Text>
            <Text className="font-meta text-meta text-ink-muted">day</Text>
          </View>
        )}
      </View>
      <View className="gap-2">
        {(["you", "buddy"] as const).map((who) => (
          <View key={who} className="flex-row items-center">
            <Text className="w-[44px] font-label text-label uppercase text-ink-muted">
              {who === "you" ? "You" : buddyName}
            </Text>
            <View className="flex-1">
              <Rail
                who={who}
                stations={who === "you" ? track.you : track.buddy}
                fill={who === "you" ? track.youFill : track.buddyFill}
                fogFrom={who === "buddy" ? track.fogFrom : null}
              />
            </View>
          </View>
        ))}
      </View>
      <View className="flex-row flex-wrap justify-between gap-3">
        <Text className="font-meta text-meta text-ink-muted">
          {gap.quiet}
          <Text className="font-body-strong text-ink">{gap.loud}</Text>
        </Text>
        <Text className="font-meta text-meta text-ink-muted">{sightLine(view, buddyName)}</Text>
      </View>
    </View>
  );
}

// After a check-in, the gap it leaves, in the same plain words as the hero.
function sealCaption(view: RoadmapView, sealed: TopicRef, buddyName: string): string {
  const after = {
    ...view,
    topics: view.topics.map((topic) =>
      topic.topic.slug === sealed.slug ? { ...topic, user_studied: true } : topic,
    ),
  };
  const gap = gapLine(after, buddyName);
  return `${sealed.title} is sealed on your roadmap. ${gap.quiet}${gap.loud} now.`;
}

export default function Roadmap() {
  const queryClient = useQueryClient();
  const buddy = useBuddy();
  const roadmap = useQuery(readRoadmapOptions());
  const [sealed, setSealed] = useState<{ topic: TopicRef; caption: string } | null>(null);

  const checkIn = useMutation({
    ...addCheckinMutation(),
    onSuccess: (topic) => {
      if (roadmap.data && buddy.data) {
        setSealed({ topic, caption: sealCaption(roadmap.data, topic, buddy.data.name) });
      }
      queryClient.invalidateQueries({ queryKey: readRoadmapQueryKey() });
    },
  });

  const view = roadmap.data;
  const buddyName = buddy.data?.name ?? "Your buddy";
  const next = view && nextForYou(view);

  return (
    <Screen>
      <ScreenHeader title="Roadmap" />
      <LoadState isPending={roadmap.isPending} error={roadmap.error} />
      {view && (
        <ScrollView contentContainerClassName="gap-2 pb-6">
          <Hero view={view} buddyName={buddyName} />
          {next && (
            // Named, because a check-in can't be undone and marks topics in plan order.
            <Button
              label={checkIn.isPending ? "Sealing…" : `I studied: ${next.topic.title}`}
              variant="primary"
              disabled={checkIn.isPending}
              onPress={() => checkIn.mutate({})}
            />
          )}
          {checkIn.isError && (
            <Text className="font-meta text-meta text-leak">
              Couldn&apos;t save that check-in. Try again.
            </Text>
          )}
          {weeks(view.topics).map((group) => (
            <View key={group.week} className="gap-2">
              <Text className="py-1 font-label text-label uppercase text-ink-muted">
                {`Week ${group.week}`}
              </Text>
              {group.topics.map((topic) => (
                <TopicRow
                  key={topic.topic.slug}
                  topic={topic}
                  meta={topicMeta(view, topic, buddyName)}
                  today={topic.topic.day === view.day}
                />
              ))}
            </View>
          ))}
        </ScrollView>
      )}
      <StudySeal
        topic={sealed?.topic ?? null}
        caption={sealed?.caption ?? ""}
        onClose={() => setSealed(null)}
      />
    </Screen>
  );
}
