import { useQuery } from "@tanstack/react-query";
import { router, useFocusEffect } from "expo-router";
import { useCallback, useEffect, useRef, useState } from "react";
import { ScrollView, Text, View } from "react-native";

import { readNotebookOptions } from "@/api/@tanstack/react-query.gen";
import type { NotebookNote } from "@/api/types.gen";
import { useBuddy } from "@/buddy";
import { CoachMark } from "@/components/CoachMark";
import { FogLift } from "@/components/FogLift";
import { LoadState } from "@/components/LoadState";
import { NoteRow } from "@/components/NoteRow";
import { Screen } from "@/components/Screen";
import { ScreenHeader } from "@/components/ScreenHeader";
import { SealedNote } from "@/components/SealedNote";
import { useKindredNow } from "@/kindredNow";
import { isNew, notebookCaption } from "@/noteFreshness";
import { usePref } from "@/prefs";
import { relativeDay, upcomingDay } from "@/time";

export default function Notebook() {
  const notebook = useQuery(readNotebookOptions());
  const buddy = useBuddy();
  const now = useKindredNow();
  const lastOpened = usePref("notebook.lastOpened");
  const [lifted, setLifted] = useState<number[]>([]);

  // Leaving the notebook sets the baseline that decides which notes arrive fogged next time.
  const nowRef = useRef(now);
  useEffect(() => {
    nowRef.current = now;
  }, [now]);
  const saveVisit = lastOpened.set;
  useFocusEffect(
    useCallback(() => () => saveVisit(nowRef.current.toISOString()), [saveVisit]),
  );

  const name = buddy.data?.name ?? "Your buddy";
  const notes = [...(notebook.data?.notes ?? [])].reverse();
  const sealed = notebook.data?.sealed ?? [];
  const open = (note: NotebookNote) => router.push(`/notebook/${note.note_id}`);
  const fogged = (note: NotebookNote) =>
    isNew(note, lastOpened.value) && !lifted.includes(note.note_id);
  const firstFogged = notes.find(fogged)?.note_id;

  return (
    <Screen>
      <ScreenHeader
        title={`${name}'s notebook`}
        caption={notebook.data && notebookCaption(notebook.data.notes)}
      />
      <LoadState isPending={notebook.isPending} error={notebook.error} />
      {notebook.data && (
        <ScrollView contentContainerClassName="gap-2 pb-6 pt-1">
          {notes.map((note) =>
            fogged(note) ? (
              <View key={note.note_id} className="gap-3">
                <FogLift
                  label={`Day ${note.topic.day} · new since you last looked`}
                  onLifted={() => setLifted((ids) => [...ids, note.note_id])}
                >
                  <NoteRow note={note} when={relativeDay(note.written_at, now)} onOpen={() => open(note)} />
                </FogLift>
                {note.note_id === firstFogged && (
                  <CoachMark
                    id="fog-lift"
                    text={`${name} wrote this since you last looked. Tap to lift the fog.`}
                    pointing="up"
                  />
                )}
              </View>
            ) : (
              <NoteRow
                key={note.note_id}
                note={note}
                when={relativeDay(note.written_at, now)}
                onOpen={() => open(note)}
              />
            ),
          )}
          {notes.length === 0 && sealed[0] && (
            <View className="gap-4 pt-2">
              <SealedNote
                tall
                text={`Day ${sealed[0].day}\n${name} writes this one ${upcomingDay(sealed[0].unlocks_at, now)}`}
              />
              <Text className="font-body text-body text-ink-muted">
                {`${name}'s notes show up here after each study session, shaky parts included. It only ever knows what's in this notebook.`}
              </Text>
            </View>
          )}
          {notes.length > 0 && sealed.length > 0 && (
            <>
              <Text className="pt-2 font-label text-label uppercase text-ink-muted">
                Not written yet
              </Text>
              {sealed.map((day) => (
                <SealedNote
                  key={day.day}
                  text={`Day ${day.day} · ${name} writes this one ${upcomingDay(day.unlocks_at, now)}`}
                />
              ))}
            </>
          )}
        </ScrollView>
      )}
    </Screen>
  );
}
