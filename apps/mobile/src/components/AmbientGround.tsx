import type { ReactNode } from "react";
import Animated, { useAnimatedStyle, useReducedMotion, withTiming } from "react-native-reanimated";

import type { Ambient } from "@/theme/ambient";
import { useThemeColor } from "@/theme/useTheme";

const CROSS_FADE_MS = 2000;

// The chat ground follows the Kindred Clock through the day; only chat changes colour.
export function AmbientGround({ ambient, children }: { ambient: Ambient; children: ReactNode }) {
  const reduced = useReducedMotion();
  const color = useThemeColor(`ambient-${ambient}`);

  const style = useAnimatedStyle(() => ({
    backgroundColor: reduced ? color : withTiming(color, { duration: CROSS_FADE_MS }),
  }));

  return <Animated.View style={[{ flex: 1, overflow: "hidden" }, style]}>{children}</Animated.View>;
}
