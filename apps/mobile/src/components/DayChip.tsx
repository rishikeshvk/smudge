import { Text, View } from "react-native";

// Where the boards show the streak (M4), the chat header shows the plan day.
export function DayChip({ day }: { day: number }) {
  return (
    <View
      accessibilityLabel={`Day ${day}`}
      className="flex-row items-center gap-2 rounded-full border border-line bg-surface-raised py-[3px] pl-2 pr-3"
    >
      <Text
        className="font-counter text-counter-sm text-ink"
        style={{ fontVariant: ["tabular-nums"] }}
      >
        {String(day).padStart(2, "0")}
      </Text>
      <Text className="font-meta text-meta text-ink-muted">day</Text>
    </View>
  );
}
