import { Pressable, Text, View } from "react-native";

import type { NotebookNote } from "@/api/types.gen";

type Props = {
  note: NotebookNote;
  when: string;
  onOpen: () => void;
};

export function NoteRow({ note, when, onOpen }: Props) {
  const sources = `${note.sources.length} ${note.sources.length === 1 ? "source" : "sources"}`;

  return (
    <Pressable
      onPress={onOpen}
      accessibilityRole="button"
      accessibilityLabel={`Day ${note.topic.day}, ${note.topic.title}. ${note.shaky.length} shaky`}
      className="flex-row items-center gap-3 rounded-sm border border-line bg-surface-raised p-3"
    >
      <Text
        className="w-[40px] text-center font-counter text-counter-sm text-ink-muted"
        style={{ fontVariant: ["tabular-nums"] }}
      >
        {String(note.topic.day).padStart(2, "0")}
      </Text>
      <View className="flex-1">
        <Text className="font-body-strong text-[15px] leading-[20px] text-ink">{note.topic.title}</Text>
        <Text className="font-meta text-meta text-ink-muted">{`${when} · ${sources}`}</Text>
      </View>
      {note.shaky.length > 0 && (
        <Text className="overflow-hidden rounded-xs bg-pencil-soft px-[6px] font-body-strong text-[12px] leading-[18px] text-ink">
          {`${note.shaky.length} shaky`}
        </Text>
      )}
    </Pressable>
  );
}
