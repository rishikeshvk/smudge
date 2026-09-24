import { router } from "expo-router";
import { ChevronLeft } from "lucide-react-native";
import { Pressable, Text, View } from "react-native";

import { useThemeColor } from "@/theme/useTheme";

export function BackHeader({ title, caption }: { title: string; caption?: string }) {
  const ink = useThemeColor("ink");
  return (
    <View className="flex-row items-start gap-2 px-2 pb-3 pt-5">
      <Pressable
        onPress={() => router.back()}
        accessibilityRole="button"
        accessibilityLabel="Back"
        className="h-[44px] w-[44px] items-center justify-center rounded-full"
      >
        <ChevronLeft size={22} strokeWidth={1.75} color={ink} />
      </Pressable>
      <View className="flex-1 gap-[2px] pr-4 pt-[6px]">
        <Text accessibilityRole="header" className="font-display text-display text-ink">
          {title}
        </Text>
        {caption && <Text className="font-meta text-meta text-ink-muted">{caption}</Text>}
      </View>
    </View>
  );
}
