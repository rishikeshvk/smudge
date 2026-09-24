import { Pressable, Text, View } from "react-native";

type Props<T extends string> = {
  label: string;
  options: { value: T; label: string }[];
  value: T;
  onChange: (value: T) => void;
};

export function SegmentedControl<T extends string>({ label, options, value, onChange }: Props<T>) {
  return (
    <View
      accessibilityRole="radiogroup"
      accessibilityLabel={label}
      className="flex-row rounded-full border border-line-strong bg-surface p-[3px]"
    >
      {options.map((option) => {
        const selected = option.value === value;
        return (
          <Pressable
            key={option.value}
            onPress={() => onChange(option.value)}
            accessibilityRole="radio"
            accessibilityState={{ checked: selected }}
            hitSlop={{ top: 6, bottom: 6 }}
            className={`rounded-full px-3 py-[6px] ${selected ? "bg-you" : ""}`}
          >
            <Text
              className={`font-body-strong text-[13px] leading-[18px] ${selected ? "text-on-you" : "text-ink-muted"}`}
            >
              {option.label}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );
}
