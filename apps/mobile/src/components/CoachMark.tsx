import { Pressable, Text, View } from "react-native";

import { type CoachId, usePref } from "@/prefs";

type Props = {
  id: CoachId;
  text: string;
  pointing: "up" | "down";
};

// A one-time hint: dismissed on tap and never shown again on this phone.
export function CoachMark({ id, text, pointing }: Props) {
  const seen = usePref(`coach.${id}`);
  if (!seen.loaded || seen.value) return null;

  return (
    <View className="max-w-[240px] flex-row items-center gap-2 rounded-sm bg-ink px-3 py-2">
      <View
        className={`absolute left-[20px] h-[12px] w-[12px] rotate-45 rounded-[2px] bg-ink ${pointing === "up" ? "-top-[6px]" : "-bottom-[6px]"}`}
      />
      <Text className="shrink font-meta text-meta text-surface-raised">{text}</Text>
      <Pressable
        onPress={() => seen.set(true)}
        accessibilityRole="button"
        hitSlop={12}
      >
        <Text className="font-body-strong text-[13px] leading-[18px] text-surface-raised underline">
          Got it
        </Text>
      </Pressable>
    </View>
  );
}
