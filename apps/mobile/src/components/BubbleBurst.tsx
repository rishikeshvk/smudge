import { useEffect, useState } from "react";
import { View } from "react-native";
import Animated, { FadeInDown, useReducedMotion } from "react-native-reanimated";

import { Bubble } from "./Bubble";
import { TypingDots } from "./TypingDots";

// A pause before each further text, as if typed: longer texts take a little longer.
const BASE_PAUSE_MS = 450;
const PAUSE_PER_CHAR_MS = 18;
const MAX_PAUSE_MS = 1600;

function typingPause(text: string): number {
  return Math.min(BASE_PAUSE_MS + text.length * PAUSE_PER_CHAR_MS, MAX_PAUSE_MS);
}

// A buddy reply of one or more texts. A fresh one arrives text by text, with typing dots
// between; one already read shows whole.
export function BubbleBurst({
  texts,
  fresh,
  onShown,
}: {
  texts: string[];
  fresh: boolean;
  onShown?: () => void;
}) {
  const reduced = useReducedMotion();
  const animate = fresh && !reduced;
  const [shown, setShown] = useState(animate ? 1 : texts.length);

  useEffect(() => {
    if (shown >= texts.length) {
      onShown?.();
      return;
    }
    const timer = setTimeout(() => setShown((count) => count + 1), typingPause(texts[shown]));
    return () => clearTimeout(timer);
  }, [shown, texts, onShown]);

  return (
    <View className="gap-2">
      {texts.slice(0, shown).map((text, index) => (
        <Animated.View key={index} entering={animate ? FadeInDown.duration(220) : undefined}>
          <Bubble kind="buddy" text={text} />
        </Animated.View>
      ))}
      {shown < texts.length && (
        <View className="self-start rounded-bubble rounded-bl-xs border border-line bg-surface-raised">
          <TypingDots />
        </View>
      )}
    </View>
  );
}
