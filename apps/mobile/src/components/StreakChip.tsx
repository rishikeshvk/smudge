import { Text, View } from "react-native";

import { streakNumber } from "@/rituals";

// The shared streak: days in a row the user has studied, something kept together.
export function StreakChip({ streak }: { streak: number }) {
  return (
    <View
      accessibilityLabel={`${streak} ${streak === 1 ? "day" : "days"} in a row together`}
      className="flex-row items-center gap-2 rounded-full border border-line bg-surface-raised py-[3px] pl-2 pr-3"
    >
      <Text
        className="font-counter text-counter-sm text-ink"
        style={{ fontVariant: ["tabular-nums"] }}
      >
        {streakNumber(streak)}
      </Text>
      <Text className="font-meta text-meta text-ink-muted">together</Text>
    </View>
  );
}
