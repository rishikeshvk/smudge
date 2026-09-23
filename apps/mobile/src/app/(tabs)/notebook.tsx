import { useQuery } from "@tanstack/react-query";
import { ScrollView, Text, View } from "react-native";

import { readNotebookOptions } from "@/api/@tanstack/react-query.gen";
import { LoadState } from "@/components/LoadState";
import { Screen } from "@/components/Screen";
import { ScreenHeader } from "@/components/ScreenHeader";

export default function Notebook() {
  const notebook = useQuery(readNotebookOptions());

  return (
    <Screen>
      <ScreenHeader quiet="The " loud="notebook" />
      <LoadState isPending={notebook.isPending} error={notebook.error} />
      <ScrollView contentContainerClassName="gap-6 pb-6">
        {notebook.data?.notes.map((note) => (
          <View key={note.note_id} className="gap-2">
            <Text className="font-title text-title text-ink">{note.topic.title}</Text>
            {note.shaky.map((point) => (
              <Text key={point} className="font-body text-body text-ink">
                <Text className="bg-pencil-soft">{point}</Text>
              </Text>
            ))}
          </View>
        ))}
        {notebook.data?.sealed.map((sealed) => (
          <Text key={sealed.day} className="font-body text-body text-fog-ink">
            {`Day ${sealed.day} · not written yet`}
          </Text>
        ))}
      </ScrollView>
    </Screen>
  );
}
