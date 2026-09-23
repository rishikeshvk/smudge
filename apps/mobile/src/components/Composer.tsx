import { ArrowRight } from "lucide-react-native";
import type { Ref } from "react";
import { Pressable, TextInput, View } from "react-native";

import { useThemeColor } from "@/theme/useTheme";

type Props = {
  value: string;
  onChangeText: (text: string) => void;
  onSend: () => void;
  placeholder: string;
  disabled?: boolean;
  inputRef?: Ref<TextInput>;
};

export function Composer({ value, onChangeText, onSend, placeholder, disabled, inputRef }: Props) {
  const inkMuted = useThemeColor("ink-muted");
  const onYou = useThemeColor("on-you");
  const canSend = !disabled && value.trim().length > 0;

  return (
    <View className="flex-row items-center gap-2 border-t border-line bg-surface-raised px-3 py-[10px]">
      <TextInput
        ref={inputRef}
        value={value}
        onChangeText={onChangeText}
        onSubmitEditing={canSend ? onSend : undefined}
        placeholder={placeholder}
        placeholderTextColor={inkMuted}
        editable={!disabled}
        multiline
        accessibilityLabel="Message"
        className="max-h-[120px] min-h-[44px] flex-1 rounded-[22px] border-[1.5px] border-line-strong bg-surface-sunken px-4 py-[10px] font-body text-body text-ink"
      />
      <Pressable
        onPress={onSend}
        disabled={!canSend}
        accessibilityRole="button"
        accessibilityLabel="Send"
        accessibilityState={{ disabled: !canSend }}
        className={`h-[44px] w-[44px] items-center justify-center rounded-full bg-you ${canSend ? "" : "opacity-[0.45]"}`}
      >
        <ArrowRight size={22} strokeWidth={1.75} color={onYou} />
      </Pressable>
    </View>
  );
}
