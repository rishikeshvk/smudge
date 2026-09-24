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

// "#RRGGBBAA" → an SVG colour and opacity, since stop colours don't take an alpha channel.
function splitAlpha(hex: string): { color: string; opacity: number } {
  return { color: hex.slice(0, 7), opacity: parseInt(hex.slice(7, 9) || "ff", 16) / 255 };
}

// The only gradient in the system, and it always means the lamp is on.
export function LampGlow() {
  const reduced = useReducedMotion();
  const glow = splitAlpha(useThemeColor("lamp-glow"));
  const opacity = useSharedValue(reduced ? 1 : 0);

  useEffect(() => {
    if (!reduced) opacity.value = withTiming(1, { duration: FADE_IN_MS });
  }, [opacity, reduced]);

  const style = useAnimatedStyle(() => ({ opacity: opacity.value }));

  return (
    <Animated.View
      pointerEvents="none"
      style={[{ position: "absolute", left: "-20%", right: "-20%", top: -140, height: 420 }, style]}
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
