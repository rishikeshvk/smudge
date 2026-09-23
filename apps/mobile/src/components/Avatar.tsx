import { View } from "react-native";

import { useThemeColor } from "@/theme/useTheme";

export type AvatarState = "studying" | "idle" | "away";

const DISC: Record<AvatarState, string> = {
  studying: "bg-lamp",
  idle: "bg-lamp-soft",
  away: "bg-transparent",
};

// The buddy is a desk lamp, not a face: a disc whose light shows whether it's studying.
export function Avatar({ state, size = 36 }: { state: AvatarState; size?: number }) {
  const lampSoft = useThemeColor("lamp-soft");
  const lampInk = useThemeColor("lamp-ink");
  const lineStrong = useThemeColor("line-strong");
  const ring = {
    studying: `0 0 0 4px ${lampSoft}`,
    idle: `inset 0 0 0 2px ${lampInk}`,
    away: `inset 0 0 0 2px ${lineStrong}`,
  }[state];

  return (
    <View
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
      className={`rounded-full ${DISC[state]}`}
      style={{ width: size, height: size, boxShadow: ring }}
    >
      {state !== "away" && (
        <View
          className={`absolute right-[22%] top-[22%] h-[30%] w-[30%] rounded-full ${state === "idle" ? "bg-lamp-ink" : "bg-lamp-soft"}`}
        />
      )}
    </View>
  );
}
