import { useEffect } from "react";
import { View } from "react-native";
import Animated, {
  useAnimatedStyle,
  useReducedMotion,
  useSharedValue,
  withDelay,
  withRepeat,
  withTiming,
} from "react-native-reanimated";

import { useThemeColor } from "@/theme/useTheme";

const DELAYS_MS = [0, 150, 300];

function Dot({ delay, size }: { delay: number; size: number }) {
  const reduced = useReducedMotion();
  const color = useThemeColor("lamp-ink");
  const opacity = useSharedValue(reduced ? 0.7 : 0.3);

  useEffect(() => {
    if (reduced) return;
    opacity.value = withDelay(delay, withRepeat(withTiming(1, { duration: 600 }), -1, true));
  }, [delay, opacity, reduced]);

  const style = useAnimatedStyle(() => ({ opacity: opacity.value }));
  return (
    <Animated.View
      style={[{ width: size, height: size, borderRadius: 9999, backgroundColor: color }, style]}
    />
  );
}

// Compact dots sit inline in the drafting status; full-size ones fill a bubble on their own.
export function TypingDots({ compact }: { compact?: boolean }) {
  return (
    <View
      accessibilityLabel="Typing"
      className={`flex-row items-center gap-[5px] ${compact ? "" : "px-4 py-[14px]"}`}
    >
      {DELAYS_MS.map((delay) => (
        <Dot key={delay} delay={delay} size={compact ? 5 : 7} />
      ))}
    </View>
  );
}
