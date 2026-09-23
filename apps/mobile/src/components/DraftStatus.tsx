import { Text, View } from "react-native";

import type { DraftSteps } from "@/draftStage";

import { TypingDots } from "./TypingDots";

function Step({ label, state }: { label: string; state: "now" | "done" | "todo" }) {
  if (state === "done") {
    return (
      <Text className="font-meta text-meta text-ink-muted line-through decoration-line-strong">
        {label}
      </Text>
    );
  }
  return (
    <View className="flex-row items-center gap-[6px]">
      {state === "now" && <TypingDots compact />}
      <Text className={`font-meta text-meta ${state === "now" ? "text-ink" : "text-ink-muted"}`}>
        {label}
      </Text>
    </View>
  );
}

// The real pipeline from the API, never a timer: drafting, then the spoiler audit.
export function DraftStatus({ steps }: { steps: DraftSteps }) {
  return (
    <View
      accessibilityLiveRegion="polite"
      accessibilityLabel={steps.checking === "now" ? "Checking it's not a spoiler" : "Writing"}
      className="flex-row items-center gap-2 self-start rounded-bubble rounded-bl-xs border border-line bg-surface-raised px-3 py-2"
    >
      <Step label="writing" state={steps.writing} />
      <View className="h-[1.5px] w-[14px] bg-line-strong" />
      <Step label="checking it's not a spoiler" state={steps.checking} />
    </View>
  );
}
