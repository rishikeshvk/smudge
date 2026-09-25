import { useEffect } from "react";
import Animated, {
  useAnimatedStyle,
  useReducedMotion,
  useSharedValue,
  withTiming,
} from "react-native-reanimated";
import Svg, { Defs, RadialGradient, Rect, Stop } from "react-native-svg";

import { useThemeColor } from "@/theme/useTheme";

const FADE_IN_MS = 1200;
const FADE_OUT_MS = 800;
export const GLOW_HEIGHT = 420;

// "#RRGGBBAA" → an SVG colour and opacity, since stop colours don't take an alpha channel.
function splitAlpha(hex: string): { color: string; opacity: number } {
  return { color: hex.slice(0, 7), opacity: parseInt(hex.slice(7, 9) || "ff", 16) / 255 };
}

// The only gradient in the system, and it always means the lamp is on. It stays mounted so
// the lamp fades out as well as in. It rises at the top of the chat unless placed elsewhere.
export function LampGlow({ on, top = -140 }: { on: boolean; top?: number }) {
  const reduced = useReducedMotion();
  const glow = splitAlpha(useThemeColor("lamp-glow"));
  const opacity = useSharedValue(0);

  useEffect(() => {
    const target = on ? 1 : 0;
    opacity.value = reduced
      ? target
      : withTiming(target, { duration: on ? FADE_IN_MS : FADE_OUT_MS });
  }, [on, opacity, reduced]);

  const style = useAnimatedStyle(() => ({ opacity: opacity.value }));

  return (
    <Animated.View
      pointerEvents="none"
      style={[{ position: "absolute", left: "-20%", right: "-20%", top, height: GLOW_HEIGHT }, style]}
    >
      <Svg width="100%" height="100%">
        <Defs>
          <RadialGradient id="lamp" cx="50%" cy="50%" rx="50%" ry="50%">
            <Stop offset="0" stopColor={glow.color} stopOpacity={glow.opacity} />
            <Stop offset="1" stopColor={glow.color} stopOpacity={0} />
          </RadialGradient>
        </Defs>
        <Rect width="100%" height="100%" fill="url(#lamp)" />
      </Svg>
    </Animated.View>
  );
}
