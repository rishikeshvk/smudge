import { View } from "react-native";
import Svg, { Circle } from "react-native-svg";

import { useThemeColor } from "@/theme/useTheme";

export type AvatarState = "studying" | "idle" | "dim" | "away";

const DISC: Record<AvatarState, string> = {
  studying: "bg-lamp",
  idle: "bg-lamp-soft",
  dim: "bg-lamp-soft opacity-60",
  away: "bg-transparent",
};

const RING_WIDTH = 2.5;
const RING_GAP = 3;

// How much of the study session has gone, drawn clockwise from the top around the disc.
function SessionRing({ size, progress }: { size: number; progress: number }) {
  const lamp = useThemeColor("lamp");
  const track = useThemeColor("lamp-soft");
  const outer = size + 2 * (RING_GAP + RING_WIDTH);
  const radius = (outer - RING_WIDTH) / 2;
  const circumference = 2 * Math.PI * radius;

  return (
    <Svg
      width={outer}
      height={outer}
      style={{ position: "absolute", left: -(RING_GAP + RING_WIDTH), top: -(RING_GAP + RING_WIDTH) }}
    >
      <Circle cx={outer / 2} cy={outer / 2} r={radius} stroke={track} strokeWidth={RING_WIDTH} fill="none" />
      <Circle
        cx={outer / 2}
        cy={outer / 2}
        r={radius}
        stroke={lamp}
        strokeWidth={RING_WIDTH}
        fill="none"
        strokeLinecap="round"
        strokeDasharray={`${circumference * progress} ${circumference}`}
        transform={`rotate(-90 ${outer / 2} ${outer / 2})`}
      />
    </Svg>
  );
}

// The buddy is a desk lamp, not a face: a disc whose light shows whether it's studying.
export function Avatar({
  state,
  size = 36,
  progress = null,
}: {
  state: AvatarState;
  size?: number;
  progress?: number | null;
}) {
  const lampSoft = useThemeColor("lamp-soft");
  const lampInk = useThemeColor("lamp-ink");
  const lineStrong = useThemeColor("line-strong");
  const ring = {
    studying: progress === null ? `0 0 0 4px ${lampSoft}` : undefined,
    idle: `inset 0 0 0 2px ${lampInk}`,
    dim: `inset 0 0 0 2px ${lineStrong}`,
    away: `inset 0 0 0 2px ${lineStrong}`,
  }[state];

  return (
    <View
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
      style={{ width: size, height: size }}
    >
      {progress !== null && <SessionRing size={size} progress={progress} />}
      <View
        className={`rounded-full ${DISC[state]}`}
        style={{ width: size, height: size, boxShadow: ring }}
      >
        {state !== "away" && (
          <View
            className={`absolute right-[22%] top-[22%] h-[30%] w-[30%] rounded-full ${state === "studying" ? "bg-lamp-soft" : "bg-lamp-ink"}`}
          />
        )}
      </View>
    </View>
  );
}
