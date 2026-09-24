import { Pressable, Text } from "react-native";

import { useThemeColor } from "@/theme/useTheme";

type Variant = "primary" | "quiet" | "text";

type Props = {
  label: string;
  onPress: () => void;
  variant?: Variant;
  small?: boolean;
  disabled?: boolean;
  grow?: boolean;
};

const FRAME: Record<Variant, string> = {
  primary: "border-you bg-you",
  quiet: "border-line-strong bg-transparent",
  text: "border-transparent bg-transparent",
};

const LABEL: Record<Variant, string> = {
  primary: "text-on-you",
  quiet: "text-ink",
  text: "text-you",
};

export function Button({ label, onPress, variant = "quiet", small, disabled, grow }: Props) {
  const ink = useThemeColor("ink");
  const size = small ? "min-h-[36px] px-3" : "min-h-[44px] px-4";

  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      accessibilityRole="button"
      accessibilityState={{ disabled }}
      // ink at 12%: the only pressed colour the design allows.
      android_ripple={{ color: `${ink}1F` }}
      // Small buttons are 36 px to the eye but still 44 px to the finger.
      hitSlop={small ? 4 : undefined}
      className={`items-center justify-center overflow-hidden rounded-sm border-[1.5px] ${FRAME[variant]} ${size} ${variant === "text" ? "px-2" : ""} ${grow ? "flex-1" : ""} ${disabled ? "opacity-[0.45]" : ""}`}
    >
      <Text
        className={`font-body-strong ${small ? "text-[14px]" : "text-[15px]"} leading-[20px] ${LABEL[variant]}`}
      >
        {label}
      </Text>
    </Pressable>
  );
}
