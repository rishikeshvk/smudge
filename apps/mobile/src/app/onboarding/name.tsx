import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useLocalSearchParams } from "expo-router";
import { useState } from "react";
import { KeyboardAvoidingView, ScrollView, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import {
  acceptMutation,
  listOnboardingMessagesOptions,
  readBuddyQueryKey,
} from "@/api/@tanstack/react-query.gen";
import { hasStatus } from "@/apiErrors";
import { Avatar } from "@/components/Avatar";
import { Button } from "@/components/Button";
import { CoachMark } from "@/components/CoachMark";
import { ProgressBar } from "@/components/ProgressBar";
import { TextField } from "@/components/TextField";
import { useKindredNow } from "@/kindredNow";
import { localDate, planDate, wallTime } from "@/time";

const SUGGESTIONS = ["Juno", "Sol", "Kit", "Wren"];
const MAX_NAME = 40;

export default function NameBuddy() {
  const insets = useSafeAreaInsets();
  const queryClient = useQueryClient();
  const now = useKindredNow();
  const { proposal: proposalId } = useLocalSearchParams<{ proposal: string }>();
  const transcript = useQuery(listOnboardingMessagesOptions());
  const proposal = transcript.data?.find((entry) => entry.message.id === Number(proposalId))
    ?.proposal;
  const [name, setName] = useState("Juno");

  const accept = useMutation({
    ...acceptMutation(),
    // With a buddy in place, the root gate swaps onboarding for the app.
    onSuccess: () => queryClient.invalidateQueries({ queryKey: readBuddyQueryKey() }),
    onError: (error) => {
      if (hasStatus(error, 409)) queryClient.invalidateQueries({ queryKey: readBuddyQueryKey() });
    },
  });

  const chosen = name.trim();
  const when =
    proposal && proposal.start_date === localDate(now)
      ? "tonight"
      : proposal && `on ${planDate(proposal.start_date)}`;

  return (
    <KeyboardAvoidingView
      behavior="padding"
      className="flex-1 bg-surface"
      style={{ paddingTop: insets.top + 20, paddingBottom: insets.bottom }}
    >
      <View className="gap-[10px] px-6">
        <ProgressBar steps={3} current={3} label="Setup progress" />
        <View className="mr-6 self-end">
          <CoachMark id="onboarding-name" text="Just the name left" pointing="up" />
        </View>
      </View>
      <ScrollView
        keyboardShouldPersistTaps="handled"
        contentContainerClassName="grow justify-center gap-[28px] px-6 py-8"
      >
        <View className="items-center">
          <Avatar state="studying" size={96} />
        </View>
        <View className="gap-2">
          <Text accessibilityRole="header" className="text-center font-display text-display text-ink">
            Name your study buddy
          </Text>
          <Text className="text-center font-body text-body text-ink-muted">
            It keeps this name for every goal you take on together. It&apos;s an AI, and it will
            always say so.
          </Text>
        </View>
        <TextField
          label="Buddy's name"
          value={name}
          onChangeText={setName}
          maxLength={MAX_NAME}
          autoCapitalize="words"
          autoCorrect={false}
        />
        <View className="flex-row flex-wrap justify-center gap-2">
          {SUGGESTIONS.map((suggestion) => (
            <Button key={suggestion} label={suggestion} small onPress={() => setName(suggestion)} />
          ))}
        </View>
      </ScrollView>
      <View className="gap-[10px] px-6 pb-[28px] pt-4">
        <Button
          label={accept.isPending ? "Starting…" : "Start day 1 together"}
          variant="primary"
          disabled={!chosen || !proposal || accept.isPending}
          onPress={() =>
            accept.mutate({
              body: { proposal_message_id: Number(proposalId), buddy_name: chosen },
            })
          }
        />
        {accept.isError ? (
          <Text className="text-center font-meta text-meta text-leak">
            {hasStatus(accept.error, 404)
              ? "That plan isn't available any more. Go back and ask for it again."
              : "Couldn't start the plan. Try again in a bit."}
          </Text>
        ) : (
          proposal && (
            <Text className="text-center font-meta text-meta text-ink-muted">
              {`${chosen || "Your buddy"} studies its first topic ${when} around ${wallTime(proposal.study_time)}.`}
            </Text>
          )
        )}
      </View>
    </KeyboardAvoidingView>
  );
}
