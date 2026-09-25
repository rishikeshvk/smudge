import * as Haptics from "expo-haptics";
import { useEffect } from "react";
import { Text } from "react-native";
import Animated, { useReducedMotion, ZoomIn } from "react-native-reanimated";

// The buddy's emoji on a message it acknowledged instead of replying to.
export function ReactionChip({ emoji, fresh }: { emoji: string; fresh: boolean }) {
  const reduced = useReducedMotion();

  useEffect(() => {
    if (fresh) Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
  }, [fresh]);

  return (
    <Animated.View
      entering={fresh && !reduced ? ZoomIn.springify().damping(12) : undefined}
      accessibilityLabel={`Reacted ${emoji}`}
      className="-mt-3 mr-3 self-end rounded-full border border-line bg-surface-raised px-2 py-[2px]"
    >
      <Text className="text-[14px] leading-[20px]">{emoji}</Text>
    </Animated.View>
  );
}
