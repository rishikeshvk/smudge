import { useQuery } from "@tanstack/react-query";
import { ScrollView, Text } from "react-native";

import { readRoadmapOptions } from "@/api/@tanstack/react-query.gen";
import { LoadState } from "@/components/LoadState";
import { Screen } from "@/components/Screen";
import { ScreenHeader } from "@/components/ScreenHeader";

export default function Roadmap() {
  const roadmap = useQuery(readRoadmapOptions());

  return (
    <Screen>
      <ScreenHeader quiet="Your " loud="roadmap" />
      <LoadState isPending={roadmap.isPending} error={roadmap.error} />
      <ScrollView contentContainerClassName="gap-2 pb-6">
        {roadmap.data?.topics.map(({ topic, unlocked }) => (
          <Text
            key={topic.slug}
            className={`font-body text-body ${unlocked ? "text-ink" : "text-fog-ink"}`}
          >
            {`${String(topic.day).padStart(2, "0")}  ${topic.title}`}
          </Text>
        ))}
      </ScrollView>
    </Screen>
  );
}
