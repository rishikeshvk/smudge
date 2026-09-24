import { View } from "react-native";

import type { Station } from "@/roadmapProgress";
import { useThemeColor } from "@/theme/useTheme";

type Props = {
  who: "you" | "buddy";
  stations: Station[];
  fill: number;
  // Fraction of the rail where the buddy's sight ends; only the buddy's rail is fogged.
  fogFrom?: number | null;
};

function useStationStyle(who: Props["who"]) {
  const color = {
    you: useThemeColor("you"),
    lampInk: useThemeColor("lamp-ink"),
    lamp: useThemeColor("lamp"),
    lampSoft: useThemeColor("lamp-soft"),
    lineStrong: useThemeColor("line-strong"),
    surface: useThemeColor("surface"),
    raised: useThemeColor("surface-raised"),
  };

  return (station: Station) => {
    switch (station) {
      case "done":
        return { size: 10, backgroundColor: who === "you" ? color.you : color.lampInk };
      case "here":
        return who === "you"
          ? { size: 16, backgroundColor: color.raised, boxShadow: `inset 0 0 0 4px ${color.you}` }
          : { size: 16, backgroundColor: color.lamp, boxShadow: `0 0 0 4px ${color.lampSoft}` };
      case "level":
        return {
          size: 20,
          backgroundColor: color.lamp,
          boxShadow: `inset 0 0 0 4px ${color.raised}, 0 0 0 3px ${color.you}`,
        };
      case "todo":
        return {
          size: 10,
          backgroundColor: color.surface,
          boxShadow: `inset 0 0 0 2px ${color.lineStrong}`,
        };
    }
  };
}

export function Rail({ who, stations, fill, fogFrom }: Props) {
  const styleFor = useStationStyle(who);

  return (
    <View className="h-[20px] flex-row items-center">
      <View className="absolute left-0 right-0 h-[2px] bg-line" />
      <View
        className={`absolute left-0 h-[2px] ${who === "you" ? "bg-you" : "bg-lamp-ink"}`}
        style={{ width: `${fill * 100}%` }}
      />
      {stations.map((station, index) => {
        const { size, ...style } = styleFor(station);
        return (
          <View key={index} className="flex-1 items-center">
            <View style={{ width: size, height: size, borderRadius: 9999, ...style }} />
          </View>
        );
      })}
      {fogFrom != null && (
        <View
          className="absolute -bottom-[6px] -top-[6px] right-0 rounded-l-full bg-fog opacity-[0.72]"
          style={{ left: `${fogFrom * 100}%` }}
        />
      )}
    </View>
  );
}
