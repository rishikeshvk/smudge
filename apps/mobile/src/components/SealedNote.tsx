import { Text, View } from "react-native";

// A note that isn't written yet: fully sealed, since only its day is known.
export function SealedNote({ text, tall }: { text: string; tall?: boolean }) {
  return (
    <View
      className={`items-center justify-center rounded-md bg-fog p-4 ${tall ? "min-h-[160px]" : "min-h-[64px]"}`}
    >
      <Text className="text-center font-meta text-meta text-fog-ink">{text}</Text>
    </View>
  );
}
