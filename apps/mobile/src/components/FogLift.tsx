import { BlurTargetView, BlurView } from "expo-blur";
import * as Haptics from "expo-haptics";
import { type ReactNode, useRef, useState } from "react";
import { Pressable, Text, View } from "react-native";
import Animated, {
  useAnimatedStyle,
  useReducedMotion,
  useSharedValue,
  withTiming,
} from "react-native-reanimated";

const LIFT_MS = 900;
// expo-blur's intensity scale; tokens.json puts fog-blur at about 40 on device.
const FOG_BLUR = 40;

type Props = {
  children: ReactNode;
  label: string;
  onLifted: () => void;
};

// A note the buddy wrote since you last looked arrives fogged; tapping clears it. What's
// revealed is reading, never a prize.
export function FogLift({ children, label, onLifted }: Props) {
  const reduced = useReducedMotion();
  const target = useRef<View>(null);
  const [lifting, setLifting] = useState(false);
  const veil = useSharedValue(1);

  const lift = () => {
    setLifting(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    const duration = reduced ? 0 : LIFT_MS;
    veil.value = withTiming(0, { duration });
    setTimeout(onLifted, duration);
  };

  const style = useAnimatedStyle(() => ({ opacity: veil.value }));

  return (
    <View className="overflow-hidden rounded-md border border-line bg-surface-raised">
      <BlurTargetView ref={target}>{children}</BlurTargetView>
      <Animated.View style={[{ position: "absolute", inset: 0 }, style]}>
        <BlurView
          blurTarget={target}
          blurMethod="dimezisBlurViewSdk31Plus"
          intensity={FOG_BLUR}
          style={{ position: "absolute", inset: 0 }}
        />
        <View className="absolute inset-0 bg-fog opacity-[0.94]" />
        <Pressable
          onPress={lift}
          disabled={lifting}
          accessibilityRole="button"
          accessibilityLabel={`${label}. Tap to read`}
          className="absolute inset-0 flex-row items-center justify-between gap-2 p-4"
        >
          <Text className="flex-1 font-meta text-meta text-fog-ink">{label}</Text>
          <View className="min-h-[36px] justify-center rounded-full bg-ink px-3">
            <Text className="font-body-strong text-[13px] leading-[18px] text-surface-raised">
              Tap to read
            </Text>
          </View>
        </Pressable>
      </Animated.View>
    </View>
  );
}
