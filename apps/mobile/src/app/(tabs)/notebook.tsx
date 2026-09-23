import { ScrollView, Text, View } from "react-native";

import { Screen } from "@/components/Screen";
import { ScreenHeader } from "@/components/ScreenHeader";
import { notes } from "@/mocks/notes";

export default function Notebook() {
  return (
    <Screen>
      <ScreenHeader quiet="The " loud="notebook" />
      <ScrollView contentContainerClassName="gap-6 pb-6">
        {notes.map((note) => (
          <View key={note.note_id} className="gap-2">
            <Text className="font-title text-title text-ink">{note.topic_title}</Text>
            <Text className="font-body text-body text-ink">
              <Text className="bg-pencil-soft">{note.shaky[0]}</Text>
            </Text>
          </View>
        ))}
      </ScrollView>
    </Screen>
  );
}
