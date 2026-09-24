import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Clock } from "lucide-react-native";
import { useState } from "react";
import { KeyboardAvoidingView, ScrollView, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import {
  changeClockMutation,
  readClockOptions,
  readRoadmapOptions,
  studyNowMutation,
} from "@/api/@tanstack/react-query.gen";
import { hasStatus } from "@/apiErrors";
import { BackHeader } from "@/components/BackHeader";
import { Button } from "@/components/Button";
import { LoadState } from "@/components/LoadState";
import { TextField } from "@/components/TextField";
import { clockCaption, DAY_HOURS, HOUR, jumpTarget } from "@/devClock";
import { useThemeColor } from "@/theme/useTheme";
import { clockTime } from "@/time";

export default function Developer() {
  const insets = useSafeAreaInsets();
  const queryClient = useQueryClient();
  const inkMuted = useThemeColor("ink-muted");
  const clock = useQuery({ ...readClockOptions(), retry: false, refetchInterval: 60_000 });
  const roadmap = useQuery({ ...readRoadmapOptions(), retry: false });
  const [jump, setJump] = useState("");

  // Moving the Clock changes what every screen may show, so everything is fetched again.
  const refreshAll = () => queryClient.invalidateQueries();
  const change = useMutation({ ...changeClockMutation(), onSuccess: refreshAll });
  const studyNow = useMutation({ ...studyNowMutation(), onSuccess: refreshAll });

  const planDays = roadmap.data?.topics.length ?? null;
  const target = planDays === null ? null : jumpTarget(jump, planDays);
  const busy = change.isPending || studyNow.isPending;

  return (
    <KeyboardAvoidingView
      behavior="padding"
      className="flex-1 bg-surface"
      style={{ paddingTop: insets.top }}
    >
      <BackHeader
        title="Developer"
        caption="Dev builds only. Moves Kindred's Clock, not your phone's."
      />
      <ScrollView
        contentContainerClassName="gap-4 px-4"
        contentContainerStyle={{ paddingBottom: insets.bottom + 24 }}
        keyboardShouldPersistTaps="handled"
      >
        {hasStatus(clock.error, 404) ? (
          <Text className="font-body text-body text-ink-muted">
            Time controls only work while the API runs in dev mode (DEV_MODE=true).
          </Text>
        ) : (
          <LoadState isPending={clock.isPending} error={clock.error} />
        )}
        {clock.data && (
          <>
            <View className="gap-3 rounded-md border border-line bg-surface-raised p-4">
              <View className="flex-row items-center gap-2">
                <Clock size={18} strokeWidth={1.75} color={inkMuted} />
                <Text className="font-label text-label uppercase text-ink-muted">Kindred clock</Text>
              </View>
              <Text
                className="font-counter text-counter text-ink"
                style={{ fontVariant: ["tabular-nums"] }}
              >
                {clockTime(clock.data.now)}
              </Text>
              <Text className="font-meta text-meta text-ink-muted">
                {`${clockCaption(clock.data, planDays)}${clock.data.real_time ? " · real time" : ""}`}
              </Text>
              <View className="flex-row gap-2">
                <Button
                  label="+1 hour"
                  small
                  grow
                  disabled={busy}
                  onPress={() => change.mutate({ body: { kind: "advance", hours: HOUR } })}
                />
                <Button
                  label="+1 day"
                  small
                  grow
                  disabled={busy}
                  onPress={() => change.mutate({ body: { kind: "advance", hours: DAY_HOURS } })}
                />
              </View>
              {planDays !== null && (
                <View className="flex-row items-end gap-2">
                  <View className="flex-1">
                    <TextField
                      label="Jump to day"
                      mono
                      value={jump}
                      onChangeText={setJump}
                      keyboardType="number-pad"
                      placeholder={`1–${planDays}`}
                    />
                  </View>
                  <Button
                    label="Jump"
                    disabled={busy || target === null}
                    onPress={() =>
                      target !== null &&
                      change.mutate({ body: { kind: "jump_to_day", day: target } })
                    }
                  />
                </View>
              )}
              <View className="flex-row">
                <Button
                  label="Back to real time"
                  variant="text"
                  disabled={busy || clock.data.real_time}
                  onPress={() => change.mutate({ body: { kind: "real_time" } })}
                />
              </View>
              {change.isError && (
                <Text className="font-meta text-meta text-leak">
                  {hasStatus(change.error, 409)
                    ? "There's no plan to jump through yet."
                    : "Couldn't move the clock. Try again."}
                </Text>
              )}
            </View>
            <View className="gap-2">
              <Text className="font-label text-label uppercase text-ink-muted">Jobs</Text>
              <Button
                label={studyNow.isPending ? "Studying…" : "Run tonight's study now"}
                disabled={busy}
                onPress={() => studyNow.mutate({})}
              />
              <Text className="font-meta text-meta text-ink-muted">
                Moves the clock to today&apos;s study time if it&apos;s earlier, then lets the
                Curator study every unlocked topic. That calls your model, so it uses your budget.
              </Text>
              {studyNow.isError && (
                <Text className="font-meta text-meta text-leak">
                  {hasStatus(studyNow.error, 409)
                    ? "There's no plan to study yet."
                    : "The study run didn't finish. Try again."}
                </Text>
              )}
            </View>
          </>
        )}
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
