import type { ReactNode } from "react";
import { Text, View } from "react-native";

export function TraceSection({
  title,
  detail,
  children,
}: {
  title: string;
  detail?: string;
  children: ReactNode;
}) {
  return (
    <View className="gap-2">
      <View className="flex-row justify-between gap-3">
        <Text className="font-label text-label uppercase text-ink-muted">{title}</Text>
        {detail && (
          <Text className="shrink font-trace text-[12px] leading-[14px] text-ink-muted">{detail}</Text>
        )}
      </View>
      {children}
    </View>
  );
}

// Key–value rows in the trace's machine voice.
export function TraceFields({ rows }: { rows: [string, ReactNode][] }) {
  return (
    <View className="gap-1 rounded-sm bg-surface-sunken p-3">
      {rows.map(([key, value]) => (
        <View key={key} className="flex-row gap-3">
          <Text className="min-w-[64px] font-trace text-trace text-ink-muted">{key}</Text>
          <View className="flex-1">
            {typeof value === "string" ? (
              <Text className="font-trace text-trace text-ink">{value}</Text>
            ) : (
              value
            )}
          </View>
        </View>
      ))}
    </View>
  );
}
