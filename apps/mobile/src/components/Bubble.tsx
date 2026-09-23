import { Text, View } from "react-native";

export type BubbleKind = "you" | "buddy" | "queued";

// The tail corner is the one sharp corner in the system; it points at whoever spoke.
const FRAME: Record<BubbleKind, string> = {
  you: "self-end rounded-br-xs bg-you",
  buddy: "self-start rounded-bl-xs border border-line bg-surface-raised",
  queued: "self-end rounded-br-xs border-[1.5px] border-dashed border-you opacity-60",
};

export function Bubble({ kind, text }: { kind: BubbleKind; text: string }) {
  return (
    <View className={`max-w-[78%] rounded-bubble px-4 py-3 ${FRAME[kind]}`}>
      <Text className={`font-body text-body ${kind === "you" ? "text-on-you" : "text-ink"}`}>
        {text}
      </Text>
    </View>
  );
}
