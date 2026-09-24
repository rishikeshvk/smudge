import type { ReactNode } from "react";
import { Pressable, View } from "react-native";
import Animated, { SlideInDown } from "react-native-reanimated";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { shadowSheet } from "@/theme/themeVars";
import { useThemeName } from "@/theme/useTheme";

const SLIDE_MS = 280;

type Props = {
  onClose: () => void;
  children: ReactNode;
};

// A bottom sheet, shown by a transparentModal route: Expo Go clips an RN Modal's bottom edge.
export function Sheet({ onClose, children }: Props) {
  const insets = useSafeAreaInsets();
  const theme = useThemeName();

  return (
    <View className="flex-1 justify-end">
      <Pressable
        onPress={onClose}
        accessibilityRole="button"
        accessibilityLabel="Close"
        className="absolute inset-0 bg-ink opacity-[0.32]"
      />
      <Animated.View
        entering={SlideInDown.duration(SLIDE_MS)}
        accessibilityViewIsModal
        className="max-h-[80%] gap-4 rounded-t-sheet bg-surface-raised px-4 pt-2"
        style={{ boxShadow: shadowSheet[theme], paddingBottom: insets.bottom + 24 }}
      >
        <View className="h-[4px] w-[36px] self-center rounded-full bg-line-strong" />
        {children}
      </Animated.View>
    </View>
  );
}
