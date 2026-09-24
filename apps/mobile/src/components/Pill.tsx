import { Text } from "react-native";

export type PillTone = "ok" | "leak" | "unsure" | "lamp" | "you";

const TONE: Record<PillTone, string> = {
  ok: "bg-ok-soft text-ok",
  leak: "bg-leak-soft text-leak",
  unsure: "bg-unsure-soft text-unsure",
  lamp: "bg-lamp-soft text-lamp-ink",
  you: "bg-you-soft text-ink",
};

// X-ray signals always carry their word; the colour only backs it up.
export function Pill({ tone, text }: { tone: PillTone; text: string }) {
  return (
    <Text
      className={`self-start overflow-hidden rounded-xs px-[6px] font-trace text-[12px] leading-[18px] ${TONE[tone]}`}
    >
      {text}
    </Text>
  );
}
