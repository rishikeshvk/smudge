import { setAudioModeAsync, useAudioPlayer } from "expo-audio";
import * as Haptics from "expo-haptics";
import { router } from "expo-router";
import { useEffect } from "react";
import { Modal, Pressable, Text, View } from "react-native";
import Animated, {
  Easing,
  useAnimatedStyle,
  useReducedMotion,
  useSharedValue,
  withTiming,
} from "react-native-reanimated";
import Svg, { Circle, Defs, G, Mask, Path, RadialGradient, Rect, Stop } from "react-native-svg";

import type { TopicRef } from "@/api/types.gen";
import { shadowSheet } from "@/theme/themeVars";
import { useThemeColor, useThemeName } from "@/theme/useTheme";

import { Button } from "./Button";
import { SEAL_PATH } from "./sealPath";

const STAMP_MS = 480;
// The stamp first reaches full size about a third of the way in: the moment it lands.
const LAND_MS = 150;
const STAMP_SOUND = require("../../assets/sounds/seal-stamp.wav");
const SEAL = 132;
const RAYS = 204;

// Wedges of lamp-soft light every 20°, fading out from the middle.
function Rays() {
  const lampSoft = useThemeColor("lamp-soft");
  const centre = RAYS / 2;
  const wedge = (from: number) => {
    const point = (degrees: number) => {
      const radians = (degrees * Math.PI) / 180;
      return `${centre + centre * Math.sin(radians)},${centre - centre * Math.cos(radians)}`;
    };
    return `M${centre},${centre} L${point(from)} L${point(from + 8)} Z`;
  };

  return (
    <Svg width={RAYS} height={RAYS} style={{ position: "absolute" }}>
      <Defs>
        <RadialGradient id="fade" cx="50%" cy="50%" rx="50%" ry="50%">
          <Stop offset="0.55" stopColor="#fff" stopOpacity={1} />
          <Stop offset="1" stopColor="#fff" stopOpacity={0} />
        </RadialGradient>
        <Mask id="rays">
          <Rect width={RAYS} height={RAYS} fill="url(#fade)" />
        </Mask>
      </Defs>
      <G mask="url(#rays)">
        {Array.from({ length: 18 }, (_, index) => (
          <Path key={index} d={wedge(index * 20)} fill={lampSoft} />
        ))}
      </G>
    </Svg>
  );
}

type Props = {
  topic: TopicRef | null;
  caption: string;
  onClose: () => void;
};

// The study seal: stamped once per check-in, with one thunk you hear and feel as it lands.
// No points, no confetti.
export function StudySeal({ topic, caption, onClose }: Props) {
  const reduced = useReducedMotion();
  const theme = useThemeName();
  const lamp = useThemeColor("lamp");
  const onLamp = useThemeColor("on-lamp");
  const progress = useSharedValue(reduced ? 1 : 0);
  const thunk = useAudioPlayer(STAMP_SOUND);

  // A quarter-second effect shouldn't pause whatever the user is listening to.
  useEffect(() => {
    setAudioModeAsync({ interruptionMode: "mixWithOthers" }).catch((error: unknown) =>
      console.warn("Couldn't set the audio mode", error),
    );
  }, []);

  useEffect(() => {
    if (!topic) return;
    const land = () => {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy);
      thunk.seekTo(0);
      thunk.play();
    };
    if (reduced) {
      land();
      return;
    }
    progress.value = 0;
    progress.value = withTiming(1, {
      duration: STAMP_MS,
      easing: Easing.bezier(0.2, 1.4, 0.4, 1),
    });
    const landing = setTimeout(land, LAND_MS);
    return () => clearTimeout(landing);
  }, [topic, reduced, progress, thunk]);

  const stamp = useAnimatedStyle(() => ({
    opacity: Math.min(progress.value, 1),
    transform: [
      { scale: 1.35 - 0.35 * progress.value },
      { rotate: `${-8 + 4 * progress.value}deg` },
    ],
  }));

  return (
    <Modal
      visible={topic !== null}
      transparent
      animationType="fade"
      statusBarTranslucent
      navigationBarTranslucent
      onRequestClose={onClose}
    >
      <Pressable
        onPress={onClose}
        accessibilityRole="button"
        accessibilityLabel="Close"
        className="absolute inset-0 bg-ink opacity-50"
      />
      {topic && (
        <View className="flex-1 justify-center px-6">
          <View
            className="items-center gap-[28px] rounded-sheet bg-surface-raised px-5 pb-[28px] pt-[44px]"
            style={{ boxShadow: shadowSheet[theme] }}
          >
            <View
              accessibilityRole="image"
              accessibilityLabel={`Day ${topic.day} sealed`}
              className="items-center justify-center"
              style={{ width: RAYS, height: RAYS, marginVertical: -(RAYS - SEAL) / 2 }}
            >
              <Rays />
              <Animated.View style={[{ width: SEAL, height: SEAL }, stamp]}>
                <Svg width={SEAL} height={SEAL} viewBox={`0 0 ${SEAL} ${SEAL}`}>
                  <Path d={SEAL_PATH} fill={lamp} />
                  <Circle
                    cx={66}
                    cy={66}
                    r={44}
                    fill="none"
                    stroke={onLamp}
                    strokeOpacity={0.35}
                    strokeWidth={1.5}
                    strokeDasharray="3 4"
                  />
                </Svg>
                <View className="absolute inset-0 items-center justify-center">
                  <Text
                    className="font-counter text-counter text-on-lamp"
                    style={{ fontVariant: ["tabular-nums"] }}
                  >
                    {String(topic.day).padStart(2, "0")}
                  </Text>
                  <Text className="font-label text-label uppercase text-on-lamp">studied</Text>
                </View>
              </Animated.View>
            </View>
            <View className="items-center gap-2">
              <Text className="text-center font-display-light text-display text-ink">
                {`Day ${topic.day}, `}
                <Text className="font-display-bold">done on your own</Text>
              </Text>
              <Text className="text-center font-meta text-meta text-ink-muted">{caption}</Text>
            </View>
            <Button
              label="See it on the roadmap"
              variant="text"
              onPress={() => {
                onClose();
                // Already there when sealed from the Roadmap; from a night review, it goes there.
                router.navigate("/roadmap");
              }}
            />
          </View>
        </View>
      )}
    </Modal>
  );
}
