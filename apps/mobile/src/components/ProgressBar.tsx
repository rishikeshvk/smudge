import { View } from "react-native";

import { useThemeColor } from "@/theme/useTheme";

type Props = {
  steps: number;
  // 1-based: the step the person is on now.
  current: number;
  label: string;
};

export function ProgressBar({ steps, current, label }: Props) {
  const you = useThemeColor("you");

  return (
    <View
      accessibilityRole="progressbar"
      accessibilityLabel={label}
      accessibilityValue={{ min: 1, max: steps, now: current }}
      className="flex-row gap-[6px]"
    >
      {Array.from({ length: steps }, (_, index) => {
        const step = index + 1;
        return (
          <View
            key={step}
            className={`h-[6px] flex-1 rounded-full ${step < current ? "bg-you" : "bg-you-soft"}`}
            style={step === current ? { boxShadow: `inset 0 0 0 1.5px ${you}` } : undefined}
          />
        );
      })}
    </View>
  );
}
