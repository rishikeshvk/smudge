import { Text, TextInput, type TextInputProps, View } from "react-native";

import { useThemeColor } from "@/theme/useTheme";

type Props = Omit<TextInputProps, "className" | "style"> & {
  label: string;
  helper?: string;
  error?: string;
  mono?: boolean;
};

export function TextField({ label, helper, error, mono, ...input }: Props) {
  const inkMuted = useThemeColor("ink-muted");

  return (
    <View className="gap-1">
      <Text className="font-body-strong text-[13px] leading-[18px] text-ink">{label}</Text>
      <View
        className={`min-h-[48px] flex-row items-center rounded-sm border-[1.5px] bg-surface-raised px-3 ${error ? "border-leak" : "border-line-strong"}`}
      >
        <TextInput
          accessibilityLabel={label}
          placeholderTextColor={inkMuted}
          className={`flex-1 text-ink ${mono ? "font-code text-[14px] leading-[20px]" : "font-body text-body"}`}
          {...input}
        />
      </View>
      {(error ?? helper) && (
        <Text className={`font-meta text-meta ${error ? "text-leak" : "text-ink-muted"}`}>
          {error ?? helper}
        </Text>
      )}
    </View>
  );
}
