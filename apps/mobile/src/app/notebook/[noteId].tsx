import { useQuery } from "@tanstack/react-query";
import { router, useLocalSearchParams } from "expo-router";
import * as WebBrowser from "expo-web-browser";
import { Pressable, ScrollView, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { readNoteOptions } from "@/api/@tanstack/react-query.gen";
import { useBuddy } from "@/buddy";
import { BackHeader } from "@/components/BackHeader";
import { Button } from "@/components/Button";
import { LoadState } from "@/components/LoadState";
import { NoteBody } from "@/components/NoteBody";

function sourceLabel(url: string): string {
  return url.replace(/^https?:\/\//, "").replace(/\/$/, "");
}

export default function NoteDetail() {
  const insets = useSafeAreaInsets();
  const { noteId } = useLocalSearchParams<{ noteId: string }>();
  const note = useQuery(readNoteOptions({ path: { note_id: Number(noteId) } }));
  const buddy = useBuddy();
  const name = buddy.data?.name ?? "Your buddy";

  return (
    <View className="flex-1 bg-surface" style={{ paddingTop: insets.top }}>
      <BackHeader title="Note" />
      <ScrollView contentContainerClassName="gap-4 px-4" contentContainerStyle={{ paddingBottom: insets.bottom + 24 }}>
        <LoadState isPending={note.isPending} error={note.error} />
        {note.data && (
          <>
            <View className="gap-3 rounded-md border border-line bg-surface-raised p-4">
              <View>
                <Text className="font-label text-label uppercase text-ink-muted">
                  {`Day ${note.data.topic.day} · ${name}'s note`}
                </Text>
                <Text className="font-title text-title text-ink">{note.data.topic.title}</Text>
              </View>
              <NoteBody markdown={note.data.body} />
              {note.data.shaky.length > 0 && (
                // Labelled as well as highlighted, so colour is never the only cue.
                <View className="gap-1 rounded-sm bg-surface p-3">
                  <Text className="font-label text-label uppercase text-ink-muted">Still shaky</Text>
                  {note.data.shaky.map((point) => (
                    <Text key={point} className="font-body text-body text-ink">
                      <Text className="bg-pencil-soft">{point}</Text>
                    </Text>
                  ))}
                </View>
              )}
              {note.data.sources.length > 0 && (
                <View className="gap-1">
                  <Text className="font-meta text-meta text-ink-muted">
                    {note.data.sources.length === 1 ? "Source" : "Sources"}
                  </Text>
                  {note.data.sources.map((url) => (
                    <Pressable
                      key={url}
                      onPress={() => WebBrowser.openBrowserAsync(url)}
                      accessibilityRole="link"
                      className="min-h-[44px] justify-center"
                    >
                      <Text className="font-meta text-meta text-you underline">{sourceLabel(url)}</Text>
                    </Pressable>
                  ))}
                </View>
              )}
            </View>
            <Button
              label="Talk about this note"
              onPress={() =>
                router.navigate({
                  pathname: "/",
                  params: { draft: `about your day ${note.data.topic.day} note: ` },
                })
              }
            />
          </>
        )}
      </ScrollView>
    </View>
  );
}
