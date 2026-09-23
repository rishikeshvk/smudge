import type { ReactNode } from "react";
import { View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

type Props = {
  // Chat swaps in its ambient ground; every other screen stays on surface.
  background?: string;
  children: ReactNode;
};

export function Screen({ background = "bg-surface", children }: Props) {
  const insets = useSafeAreaInsets();
  return (
    <View className={`flex-1 px-4 ${background}`} style={{ paddingTop: insets.top }}>
      {children}
    </View>
  );
}
