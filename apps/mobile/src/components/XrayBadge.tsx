import { Fragment } from "react";
import { Pressable, Text } from "react-native";

import { type BadgePart, type Tone } from "@/turnSummary";

const TONE: Record<Tone, string> = {
  plain: "text-ink",
  ok: "text-ok",
  leak: "text-leak",
  unsure: "text-unsure",
};

type Props = {
  parts: BadgePart[];
  // Without a handler the badge is a label, as in the trace sheet's own header.
  onPress?: () => void;
};

export function XrayBadge({ parts, onPress }: Props) {
  const summary = parts.map((part) => part.text).join(", ");
  const label = (
    <Text className="font-trace text-trace">
      {parts.map((part, index) => (
        <Fragment key={part.text}>
          {index > 0 && <Text className="text-ink-muted">{" · "}</Text>}
          <Text className={TONE[part.tone]}>{part.text}</Text>
        </Fragment>
      ))}
    </Text>
  );

  const frame = "self-start rounded-xs border border-line bg-surface-sunken px-2 py-[2px]";
  if (!onPress) return <Text className={frame}>{label}</Text>;
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityLabel={`Why this reply: ${summary}`}
      hitSlop={12}
      className={frame}
    >
      {label}
    </Pressable>
  );
}
