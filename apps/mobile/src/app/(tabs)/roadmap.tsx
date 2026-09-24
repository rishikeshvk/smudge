import { useQuery } from "@tanstack/react-query";
import { router } from "expo-router";
import { ScrollView, Text, View } from "react-native";

import { readRoadmapOptions } from "@/api/@tanstack/react-query.gen";
import type { RoadmapView } from "@/api/types.gen";
import { useBuddy } from "@/buddy";
import { useCheckIn } from "@/checkIn";
import { Button } from "@/components/Button";
import { LoadState } from "@/components/LoadState";
import { Rail } from "@/components/Rail";
import { Screen } from "@/components/Screen";
import { ScreenHeader } from "@/components/ScreenHeader";
import { StudySeal } from "@/components/StudySeal";
import { PausedRow, TopicRow } from "@/components/TopicRow";
import {
  gapLine,
  headline,
  nextForYou,
  rails,
  sightLine,
  topicMeta,
  weeks,
} from "@/roadmapProgress";
import { useRefetchOnScreenFocus } from "@/queryClient";
import { streakNumber } from "@/rituals";

function Hero({ view, buddyName }: { view: RoadmapView; buddyName: string }) {
  const title = headline(view);
  const track = rails(view);
  const gap = gapLine(view, buddyName);

  return (
    <View className="gap-[14px] rounded-md border border-line bg-surface-raised p-4">
      <View className="flex-row items-end justify-between">
        <View className="flex-1">
          <Text className="font-label text-label uppercase text-ink-muted">
            {`${view.plan_title} · ${view.last_day} days`}
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
              {streakNumber(view.streak)}
            </Text>
            <Text className="font-meta text-meta text-ink-muted">together</Text>
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

export default function Roadmap() {
  const buddy = useBuddy();
  const roadmap = useQuery(readRoadmapOptions());
  const { checkIn, sealed, closeSeal } = useCheckIn();
  useRefetchOnScreenFocus(roadmap.refetch);

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
          <Button label="Change plan" variant="text" onPress={() => router.push("/change-plan")} />
          {weeks(view).map((group) => (
            <View key={group.week} className="gap-2">
              <Text className="py-1 font-label text-label uppercase text-ink-muted">
                {`Week ${group.week}`}
              </Text>
              {group.days.map(({ day, topic }) =>
                topic ? (
                  <TopicRow
                    key={day}
                    topic={topic}
                    meta={topicMeta(view, topic, buddyName)}
                    today={day === view.day}
                    onPull={
                      topic.can_pull
                        ? () =>
                            router.push({ pathname: "/pull/[slug]", params: { slug: topic.topic.slug } })
                        : undefined
                    }
                  />
                ) : (
                  <PausedRow key={day} day={day} />
                ),
              )}
            </View>
          ))}
        </ScrollView>
      )}
      <StudySeal
        topic={sealed?.topic ?? null}
        caption={sealed?.caption ?? ""}
        onClose={closeSeal}
      />
    </Screen>
  );
}
