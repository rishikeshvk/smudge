import { Link } from "expo-router";
import { Settings } from "lucide-react-native";
import { Pressable, Text, View } from "react-native";

import { useThemeColor } from "@/theme/useTheme";

type Props = {
  title: string;
  caption?: string;
};

export function ScreenHeader({ title, caption }: Props) {
  const ink = useThemeColor("ink");
  return (
    <View className="flex-row items-start gap-2 pb-3 pt-5">
      <View className="flex-1 gap-[2px]">
        <Text accessibilityRole="header" className="font-display text-display text-ink">
          {title}
        </Text>
        {caption && <Text className="font-meta text-meta text-ink-muted">{caption}</Text>}
      </View>
      <Link href="/settings" asChild>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Settings"
          className="h-[44px] w-[44px] items-center justify-center rounded-full"
        >
          <Settings size={22} strokeWidth={1.75} color={ink} />
        </Pressable>
      </Link>
    </View>
  );
}
