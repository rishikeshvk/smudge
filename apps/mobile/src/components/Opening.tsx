import * as SplashScreen from "expo-splash-screen";
import { useEffect, useRef, useState } from "react";
import { type LayoutChangeEvent, Text, View } from "react-native";
import Animated, {
  runOnJS,
  useAnimatedStyle,
  useReducedMotion,
  useSharedValue,
  withTiming,
} from "react-native-reanimated";

import { Avatar } from "./Avatar";
import { GLOW_HEIGHT, LampGlow } from "./LampGlow";

// Long enough to read as a beat rather than a flicker; never longer than real start-up.
const FLOOR_MS = 600;
const FADE_OUT_MS = 300;
const AVATAR = 96;

// The native splash hands over to this screen with the mark in the same place, then the
// lamp comes on while the app finds out who is signed in.
export function Opening({ ready, onGone }: { ready: boolean; onGone: () => void }) {
  const reduced = useReducedMotion();
  // When the splash handed over; the floor counts from there.
  const shownAt = useRef<number | null>(null);
  const [height, setHeight] = useState<number | null>(null);
  const [lampOn, setLampOn] = useState(false);
  const opacity = useSharedValue(1);

  const onLayout = (event: LayoutChangeEvent) => {
    setHeight(event.nativeEvent.layout.height);
    if (shownAt.current !== null) return;
    shownAt.current = Date.now();
    SplashScreen.hideAsync();
    setLampOn(true);
  };

  useEffect(() => {
    if (!ready) return;
    const shown = shownAt.current ?? Date.now();
    const wait = Math.max(0, FLOOR_MS - (Date.now() - shown));
    const timer = setTimeout(() => {
      if (reduced) {
        onGone();
        return;
      }
      opacity.value = withTiming(0, { duration: FADE_OUT_MS }, (finished) => {
        if (finished) runOnJS(onGone)();
      });
    }, wait);
    return () => clearTimeout(timer);
  }, [ready, reduced, opacity, onGone]);

  const fade = useAnimatedStyle(() => ({ opacity: opacity.value }));
  const center = height === null ? null : height / 2;

  return (
    <Animated.View
      pointerEvents="none"
      onLayout={onLayout}
      className="absolute inset-0 overflow-hidden bg-surface"
      style={fade}
    >
      {center !== null && (
        <>
          <LampGlow on={lampOn} top={center - GLOW_HEIGHT / 2} />
          <View className="absolute self-center" style={{ top: center - AVATAR / 2 }}>
            <Avatar state="studying" size={AVATAR} />
          </View>
          <View className="absolute inset-x-0 items-center gap-[6px]" style={{ top: center + 80 }}>
            <Text
              accessibilityRole="header"
              className="font-display-bold text-[34px] leading-[40px] text-ink"
            >
              <Text className="bg-pencil-soft">smu</Text>dge<Text className="text-lamp-ink">.</Text>
            </Text>
            <Text className="font-body text-body text-ink-muted">a study buddy who&apos;s on day one too</Text>
          </View>
        </>
      )}
    </Animated.View>
  );
}
