import { ScrollView, Text } from "react-native";

import { Screen } from "@/components/Screen";
import { ScreenHeader } from "@/components/ScreenHeader";
import { roadmap } from "@/mocks/roadmap";

export default function Roadmap() {
  return (
    <Screen>
      <ScreenHeader quiet="Your " loud="roadmap" />
      <ScrollView contentContainerClassName="gap-2 pb-6">
        {roadmap.map(({ topic, unlocked }) => (
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
