import type { ReactNode } from "react";
import { Text, View } from "react-native";

type Props = {
  band: string;
  bandDetail?: string;
  children: ReactNode;
};

// A buddy card: the lamp-soft band says what kind of card it is.
export function Card({ band, bandDetail, children }: Props) {
  return (
    <View className="w-[92%] self-start overflow-hidden rounded-md border border-line bg-surface-raised">
      <View className="flex-row items-center justify-between gap-2 bg-lamp-soft px-4 py-2">
        <Text className="font-label text-label uppercase text-lamp-ink">{band}</Text>
        {bandDetail && (
          <Text className="font-trace text-[12px] leading-[14px] text-lamp-ink">{bandDetail}</Text>
        )}
      </View>
      <View className="gap-2 px-4 pb-4 pt-3">{children}</View>
    </View>
  );
}
