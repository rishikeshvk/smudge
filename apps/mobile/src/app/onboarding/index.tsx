import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { router } from "expo-router";
import { Fragment, useRef, useState } from "react";
import { KeyboardAvoidingView, ScrollView, Text, type TextInput, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import {
  listOnboardingMessagesOptions,
  listOnboardingMessagesQueryKey,
  readBuddyQueryKey,
  sendOnboardingMessageMutation,
} from "@/api/@tanstack/react-query.gen";
import { hasStatus } from "@/apiErrors";
import { Bubble } from "@/components/Bubble";
import { BuddyHeader } from "@/components/BuddyHeader";
import { Button } from "@/components/Button";
import { Composer } from "@/components/Composer";
import { LoadState } from "@/components/LoadState";
import { ProposalCard } from "@/components/ProposalCard";
import { TypingDots } from "@/components/TypingDots";
import { deviceTimeZone, latestProposalId, sendFailureText } from "@/onboarding";
import { clockTime } from "@/time";

function BuddyTyping() {
  return (
    <View className="self-start rounded-bubble rounded-bl-xs border border-line bg-surface-raised">
      <TypingDots />
    </View>
  );
}

export default function OnboardingChat() {
  const insets = useSafeAreaInsets();
  const queryClient = useQueryClient();
  const transcript = useQuery(listOnboardingMessagesOptions());
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState<string | null>(null);
  const [quickReplies, setQuickReplies] = useState<string[]>([]);
  const inputRef = useRef<TextInput>(null);
  const scrollRef = useRef<ScrollView>(null);

  const send = useMutation({
    ...sendOnboardingMessageMutation(),
    onSuccess: async (reply) => {
      await queryClient.invalidateQueries({ queryKey: listOnboardingMessagesQueryKey() });
      setQuickReplies(reply.quick_replies);
      setSending(null);
    },
    onError: (error) => {
      // A plan already exists (onboarded elsewhere): the gate takes over from here.
      if (hasStatus(error, 409)) queryClient.invalidateQueries({ queryKey: readBuddyQueryKey() });
    },
  });

  const submit = (text: string) => {
    const message = text.trim();
    if (!message) return;
    setSending(message);
    setDraft("");
    setQuickReplies([]);
    send.mutate({ body: { text: message, timezone: deviceTimeZone() } });
  };

  const entries = transcript.data ?? [];
  const acceptable = latestProposalId(entries);

  return (
    <KeyboardAvoidingView behavior="padding" className="flex-1 bg-ambient-day">
      <BuddyHeader name="Your study buddy" status="setting up · openly an AI" avatar="idle" />
      <ScrollView
        ref={scrollRef}
        onContentSizeChange={() => scrollRef.current?.scrollToEnd({ animated: true })}
        keyboardShouldPersistTaps="handled"
        contentContainerClassName="grow justify-end gap-2 p-4"
      >
        <View className="items-center gap-2 pb-2">
          <Text className="font-label text-label uppercase text-ink-muted">Getting started</Text>
          <Text className="text-center font-meta text-meta text-ink-muted">
            Your study buddy is an AI. It learns the same subject as you, on its own schedule, and
            only knows what it has covered so far. Tell it what you want to learn, and by when.
          </Text>
        </View>
        <LoadState isPending={transcript.isPending} error={transcript.error} />
        {entries.map(({ message, proposal }) => (
          <Fragment key={message.id}>
            <Bubble kind={message.speaker === "user" ? "you" : "buddy"} text={message.text} />
            {message.speaker === "user" && (
              <Text className="self-end font-meta text-meta text-ink-muted">
                {clockTime(message.at)}
              </Text>
            )}
            {proposal && (
              <ProposalCard
                proposal={proposal}
                {...(message.id === acceptable && {
                  onAccept: () =>
                    router.push({
                      pathname: "/onboarding/name",
                      params: { proposal: String(message.id) },
                    }),
                  onChange: () => inputRef.current?.focus(),
                })}
              />
            )}
          </Fragment>
        ))}
        {sending && <Bubble kind="you" text={sending} />}
        {send.isPending && <BuddyTyping />}
        {send.isError && sending && (
          <View className="gap-2">
            <Text className="font-meta text-meta text-leak">{sendFailureText(send.error)}</Text>
            <View className="flex-row">
              <Button label="Try again" small onPress={() => submit(sending)} />
            </View>
          </View>
        )}
        {!send.isPending && quickReplies.length > 0 && (
          <View className="flex-row flex-wrap gap-2 pt-1">
            {quickReplies.map((reply) => (
              <Button key={reply} label={reply} small onPress={() => submit(reply)} />
            ))}
          </View>
        )}
      </ScrollView>
      <View className="bg-surface-raised" style={{ paddingBottom: insets.bottom }}>
        <Composer
          inputRef={inputRef}
          value={draft}
          onChangeText={setDraft}
          onSend={() => submit(draft)}
          placeholder={acceptable === null ? "What do you want to learn?" : "Ask for a change"}
          disabled={send.isPending}
        />
      </View>
    </KeyboardAvoidingView>
  );
}
