import type { ReactNode } from "react";
import { Text, View } from "react-native";

// One line of Settings: a label on the left, its control on the right.
export function SettingRow({ label, children }: { label: string; children: ReactNode }) {
  return (
    <View className="min-h-[44px] flex-row items-center justify-between gap-3">
      <Text className="font-body-strong text-[15px] leading-[20px] text-ink">{label}</Text>
      {children}
    </View>
  );
}
