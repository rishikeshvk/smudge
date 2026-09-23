import { Link } from "expo-router";
import { Settings } from "lucide-react-native";
import { Pressable, View } from "react-native";

import { useThemeColor } from "@/theme/useTheme";

import { SplitTitle } from "./SplitTitle";

type Props = {
  quiet: string;
  loud: string;
};

export function ScreenHeader({ quiet, loud }: Props) {
  const inkMuted = useThemeColor("ink-muted");
  return (
    <View className="flex-row items-center justify-between pb-6 pt-8">
      <SplitTitle quiet={quiet} loud={loud} />
      <Link href="/settings" asChild>
        <Pressable
          accessibilityLabel="Settings"
          className="h-[44px] w-[44px] items-center justify-center rounded-full"
        >
          <Settings size={22} strokeWidth={1.75} color={inkMuted} />
        </Pressable>
      </Link>
    </View>
  );
}
