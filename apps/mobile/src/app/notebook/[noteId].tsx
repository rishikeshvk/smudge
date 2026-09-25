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
import { useKindredNow } from "@/kindredNow";
import { stillShaky } from "@/shaky";
import { relativeDay } from "@/time";

function sourceLabel(url: string): string {
  return url.replace(/^https?:\/\//, "").replace(/\/$/, "");
}

export default function NoteDetail() {
  const insets = useSafeAreaInsets();
  const { noteId } = useLocalSearchParams<{ noteId: string }>();
  const note = useQuery(readNoteOptions({ path: { note_id: Number(noteId) } }));
  const buddy = useBuddy();
  const now = useKindredNow();
  const name = buddy.data?.name ?? "Your buddy";

  return (
    <View className="flex-1 bg-surface" style={{ paddingTop: insets.top }}>
      <BackHeader title="Note" />
      <ScrollView showsVerticalScrollIndicator={false} contentContainerClassName="gap-4 px-4" contentContainerStyle={{ paddingBottom: insets.bottom + 24 }}>
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
              {stillShaky(note.data).length > 0 && (
                // Labelled as well as highlighted, so colour is never the only cue.
                <View className="gap-1 rounded-sm bg-surface p-3">
                  <Text className="font-label text-label uppercase text-ink-muted">Still shaky</Text>
                  {stillShaky(note.data).map((point) => (
                    <Text key={point} className="font-body text-body text-ink">
                      <Text className="bg-pencil-soft">{point}</Text>
                    </Text>
                  ))}
                </View>
              )}
              {note.data.sorted.length > 0 && (
                <View className="gap-3 rounded-sm bg-surface p-3">
                  <Text className="font-label text-label uppercase text-ink-muted">Sorted with your help</Text>
                  {note.data.sorted.map((point) => (
                    <View key={point.shaky} className="flex-row gap-2">
                      <Text className="font-body-strong text-body text-you">✓</Text>
                      <View className="flex-1 gap-1">
                        <Text className="font-body text-body text-ink-muted line-through">{point.shaky}</Text>
                        <Text className="font-body text-body text-ink">{point.insight}</Text>
                        <Text className="font-meta text-meta text-ink-muted">
                          {`sorted with your help · ${relativeDay(point.sorted_at, now)}`}
                        </Text>
                      </View>
                    </View>
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
