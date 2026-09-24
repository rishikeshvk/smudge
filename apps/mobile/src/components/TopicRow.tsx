import { Text, View } from "react-native";

import type { RoadmapTopic } from "@/api/types.gen";

import { Button } from "./Button";

type Props = {
  topic: RoadmapTopic;
  meta: string;
  today: boolean;
  onPull?: () => void;
};

function Mark({ filled }: { filled: string | null }) {
  return (
    <View
      className={`h-[10px] w-[10px] rounded-full ${filled ?? "border-2 border-line-strong"}`}
    />
  );
}

// Locked topics stay readable: it's the user's own plan. Only the buddy can't see them yet.
export function TopicRow({ topic, meta, today, onPull }: Props) {
  const locked = !topic.unlocked;
  const frame = locked
    ? "border-transparent bg-fog"
    : today
      ? "border-[1.5px] border-you bg-surface-raised"
      : "border-line bg-surface-raised";

  return (
    <View
      accessibilityLabel={`Day ${topic.topic.day}, ${topic.topic.title}, ${meta}`}
      className={`flex-row items-center gap-3 rounded-sm border p-3 ${frame}`}
    >
      <Text
        className={`w-[40px] text-center font-counter text-counter-sm ${today && !locked ? "text-you" : "text-ink-muted"}`}
        style={{ fontVariant: ["tabular-nums"] }}
      >
        {String(topic.topic.day).padStart(2, "0")}
      </Text>
      <View className="flex-1">
        <Text className="font-body-strong text-[15px] leading-[20px] text-ink">{topic.topic.title}</Text>
        <Text className={`font-meta text-meta ${locked ? "text-fog-ink" : "text-ink-muted"}`}>{meta}</Text>
      </View>
      {locked && onPull && <Button label="Pull earlier" small onPress={onPull} />}
      {!locked && (
        <View className="flex-row gap-1">
          <Mark filled={topic.user_studied ? "bg-you" : null} />
          <Mark filled={topic.buddy_studied ? "bg-lamp-ink" : null} />
        </View>
      )}
    </View>
  );
}
