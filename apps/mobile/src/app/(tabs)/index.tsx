import { useQuery } from "@tanstack/react-query";
import { router, useIsFocused, useLocalSearchParams } from "expo-router";
import { useEffect, useState } from "react";
import { FlatList, KeyboardAvoidingView, Text, View } from "react-native";

import { readRoadmapOptions } from "@/api/@tanstack/react-query.gen";
import { useBuddy } from "@/buddy";
import { buddyStatusLine } from "@/buddyStatus";
import { useChatPages, useSendMessage, useTurnStage } from "@/chat";
import { useCheckIn } from "@/checkIn";
import { AmbientGround } from "@/components/AmbientGround";
import { Bubble } from "@/components/Bubble";
import { BuddyHeader } from "@/components/BuddyHeader";
import { ChatRow } from "@/components/ChatRow";
import { Composer } from "@/components/Composer";
import { DraftStatus } from "@/components/DraftStatus";
import { LampGlow } from "@/components/LampGlow";
import { LoadState } from "@/components/LoadState";
import { StreakChip } from "@/components/StreakChip";
import { StudySeal } from "@/components/StudySeal";
import { UnavailableBanner } from "@/components/UnavailableBanner";
import { XrayToggle } from "@/components/XrayToggle";
import { draftSteps, isInFlight } from "@/draftStage";
import { useKindredNow } from "@/kindredNow";
import { usePref } from "@/prefs";
import { useRefetchOnScreenFocus } from "@/queryClient";
import { checkInMessage } from "@/rituals";
import { ambientForHour } from "@/theme/ambient";
import { chronological, threadRows } from "@/thread";
import { localHour } from "@/time";

const BUDDY_POLL_MS = 60_000;

export default function Chat() {
  const focused = useIsFocused();
  const buddy = useBuddy({ pollMs: focused ? BUDDY_POLL_MS : undefined });
  // Its study time, the streak and today's check-in move with the buddy's day.
  const roadmap = useQuery({
    ...readRoadmapOptions(),
    refetchInterval: focused ? BUDDY_POLL_MS : false,
  });
  const pages = useChatPages({ pollMs: focused ? BUDDY_POLL_MS : undefined });
  useRefetchOnScreenFocus(buddy.refetch);
  useRefetchOnScreenFocus(roadmap.refetch);
  const now = useKindredNow();
  const [draft, setDraft] = useState("");
  // A failed message comes back to the composer, unless something new is being typed there.
  const send = useSendMessage({
    onFailed: (text) => setDraft((current) => (current.trim() ? current : text)),
  });
  const { checkIn, sealed, closeSeal } = useCheckIn({
    onCheckedIn: (topic) => send.mutate({ body: { text: checkInMessage(topic) } }),
  });
  const { draft: prefill } = useLocalSearchParams<{ draft?: string }>();
  const [appliedPrefill, setAppliedPrefill] = useState<string | undefined>();

  // "Talk about this note" opens chat with a started message: taken once, then cleared.
  if (prefill !== appliedPrefill) {
    setAppliedPrefill(prefill);
    if (prefill) setDraft(prefill);
  }
  useEffect(() => {
    if (prefill) router.setParams({ draft: undefined });
  }, [prefill]);

  const xray = usePref("xray");

  const available = buddy.data?.available ?? true;
  const messages = chronological(pages.data?.pages ?? []);
  const working = messages.find(isInFlight);
  const stage = useTurnStage(working, available, focused);

  // The root gate only shows the tabs once there is a buddy.
  if (!buddy.data) return null;
  const { name, studying } = buddy.data;
  const status = buddyStatusLine(buddy.data, roadmap.data);
  const steps = available && working ? draftSteps(stage) : null;
  // Newest first, because the list is inverted to open at the latest message.
  const rows = threadRows(messages).reverse();
  const newestReplyId = rows.find((row) => row.message.turn_id !== null)?.message.id;

  const submit = (text: string) => {
    const message = text.trim();
    if (!message) return;
    setDraft("");
    send.mutate({ body: { text: message } });
  };

  // The inverted list's own padding lands at the top, so the gap above the composer lives here.
  const latest = (
    <View className="gap-2 pb-4 pt-2">
      {send.isPending && <Bubble kind="you" text={send.variables.body.text} />}
      {steps && <DraftStatus steps={steps} />}
    </View>
  );

  return (
    <AmbientGround ambient={ambientForHour(localHour(now))}>
      <LampGlow on={studying !== null} />
      <BuddyHeader name={name} status={status.text} avatar={status.avatar} lampStatus={status.lamp}>
        {roadmap.data && roadmap.data.day >= 1 && <StreakChip streak={roadmap.data.streak} />}
        <XrayToggle on={xray.value === true} onToggle={() => xray.set(!xray.value)} />
      </BuddyHeader>
      {!available && <UnavailableBanner name={name} />}
      <KeyboardAvoidingView behavior="padding" className="flex-1">
        {messages.length === 0 && !send.isPending ? (
          <View className="flex-1 justify-end gap-2 p-4">
            <LoadState isPending={pages.isPending} error={pages.error} />
            {pages.isSuccess && (
              <Text className="text-center font-meta text-meta text-ink-muted">
                {`Say hi to ${name}. It's working through the same plan as you.`}
              </Text>
            )}
          </View>
        ) : (
          <FlatList
            inverted
            data={rows}
            keyExtractor={(row) => String(row.message.id)}
            renderItem={({ item }) => (
              <ChatRow
                row={item}
                buddyName={name}
                buddyAvailable={available}
                onResend={submit}
                xray={xray.value === true}
                xrayHint={item.message.id === newestReplyId}
                onOpenTrace={(turnId) => router.push({ pathname: "/trace/[turnId]", params: { turnId } })}
                newest={item.message.id === rows[0]?.message.id && !send.isPending}
                checkedInToday={roadmap.data?.checked_in_today ?? false}
                onCheckIn={() => checkIn.mutate({})}
                checkingIn={checkIn.isPending}
              />
            )}
            ListHeaderComponent={latest}
            onEndReached={() => pages.hasNextPage && pages.fetchNextPage()}
            keyboardShouldPersistTaps="handled"
            contentContainerClassName="px-4"
          />
        )}
        {send.isError && (
          <Text className="px-4 pb-2 font-meta text-meta text-leak">
            Couldn&apos;t send that. Check the connection and try again.
          </Text>
        )}
        {checkIn.isError && (
          <Text className="px-4 pb-2 font-meta text-meta text-leak">
            Couldn&apos;t save that check-in. Try again.
          </Text>
        )}
        <Composer
          value={draft}
          onChangeText={setDraft}
          onSend={() => submit(draft)}
          placeholder={available ? `Message ${name}` : `Messages wait until ${name}'s back`}
        />
      </KeyboardAvoidingView>
      <StudySeal topic={sealed?.topic ?? null} caption={sealed?.caption ?? ""} onClose={closeSeal} />
    </AmbientGround>
  );
}
