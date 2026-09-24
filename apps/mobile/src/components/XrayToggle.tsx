import { Crosshair } from "lucide-react-native";
import { Pressable } from "react-native";

import { useThemeColor } from "@/theme/useTheme";

export function XrayToggle({ on, onToggle }: { on: boolean; onToggle: () => void }) {
  const ink = useThemeColor("ink");
  const surface = useThemeColor("surface");

  return (
    <Pressable
      onPress={onToggle}
      accessibilityRole="button"
      accessibilityLabel="X-ray view"
      accessibilityState={{ selected: on }}
      className={`h-[44px] w-[44px] items-center justify-center rounded-full ${on ? "bg-ink" : ""}`}
    >
      <Crosshair size={22} strokeWidth={1.75} color={on ? surface : ink} />
    </Pressable>
  );
}
