import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { router } from "expo-router";
import { useState } from "react";
import { Text, View } from "react-native";

import {
  changePlanStudyTimeMutation,
  pausePlanMutation,
  readRoadmapOptions,
} from "@/api/@tanstack/react-query.gen";
import { useBuddy } from "@/buddy";
import { Button } from "@/components/Button";
import { Sheet } from "@/components/Sheet";
import { TextField } from "@/components/TextField";
import { PAUSE_DAYS, parseStudyTime, shortTime } from "@/replanning";

export default function ChangePlan() {
  const queryClient = useQueryClient();
  const buddy = useBuddy();
  const roadmap = useQuery(readRoadmapOptions());
  const [time, setTime] = useState("");
  const [days, setDays] = useState<number | null>(null);
  // Moving the plan changes what every screen may show.
  const done = () => queryClient.invalidateQueries().then(() => router.back());
  const studyTime = useMutation({ ...changePlanStudyTimeMutation(), onSuccess: done });
  const pause = useMutation({ ...pausePlanMutation(), onSuccess: done });

  const name = buddy.data?.name ?? "Your buddy";
  const current = roadmap.data ? shortTime(roadmap.data.study_time) : null;
  const parsed = parseStudyTime(time);
  const busy = studyTime.isPending || pause.isPending;

  return (
    <Sheet onClose={() => router.back()}>
      <Text accessibilityRole="header" className="font-title text-title text-ink">
        Change the plan
      </Text>
      <View className="gap-2">
        <TextField
          label="Study time"
          value={time}
          onChangeText={setTime}
          placeholder={current ?? "19:00"}
          keyboardType="numbers-and-punctuation"
          error={time.trim() && !parsed ? "Use a 24-hour time, like 19:00." : undefined}
          helper={`${name} studies the topics ahead at this time, from tonight on.`}
        />
        <Button
          label={studyTime.isPending ? "Saving…" : "Save study time"}
          disabled={busy || !parsed}
          onPress={() => parsed && studyTime.mutate({ body: { study_time: parsed } })}
        />
      </View>
      <View className="gap-2">
        <Text className="font-body-strong text-[13px] leading-[18px] text-ink">Pause</Text>
        <View className="flex-row flex-wrap gap-2">
          {PAUSE_DAYS.map((option) => (
            <Button
              key={option}
              label={`${option} ${option === 1 ? "day" : "days"}`}
              variant={days === option ? "primary" : "quiet"}
              small
              onPress={() => setDays(option)}
            />
          ))}
        </View>
        <Text className="font-meta text-meta text-ink-muted">
          {`Every topic still ahead moves back. ${name} doesn't study on paused days, and you both finish later.`}
        </Text>
        <Button
          label={pause.isPending ? "Pausing…" : "Pause the plan"}
          disabled={busy || days === null}
          onPress={() => days !== null && pause.mutate({ body: { days } })}
        />
      </View>
      {(studyTime.isError || pause.isError) && (
        <Text className="font-meta text-meta text-leak">Couldn&apos;t change the plan. Try again.</Text>
      )}
    </Sheet>
  );
}
