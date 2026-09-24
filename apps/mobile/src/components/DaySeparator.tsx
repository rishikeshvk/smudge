import { Text, View } from "react-native";

export function DaySeparator({ label }: { label: string }) {
  return (
    <View accessibilityRole="header" className="flex-row items-center gap-3 pb-1 pt-6">
      <View className="h-[1px] flex-1 bg-line" />
      <Text className="font-label text-label uppercase text-ink-muted">{label}</Text>
      <View className="h-[1px] flex-1 bg-line" />
    </View>
  );
}
