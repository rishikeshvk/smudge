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

function Dot({ delay }: { delay: number }) {
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
      style={[{ width: 7, height: 7, borderRadius: 9999, backgroundColor: color }, style]}
    />
  );
}

export function TypingDots() {
  return (
    <View
      accessibilityLabel="Typing"
      className="flex-row items-center gap-[5px] px-4 py-[14px]"
    >
      {DELAYS_MS.map((delay) => (
        <Dot key={delay} delay={delay} />
      ))}
    </View>
  );
}
