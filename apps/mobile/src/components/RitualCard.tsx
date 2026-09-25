import { router } from "expo-router";
import { Pressable, Text, View } from "react-native";

import type {
  AskCard,
  MorningCard,
  NightReviewCard,
  StudyShareCard,
  TopicRef,
} from "@/api/types.gen";
import { usePref } from "@/prefs";
import { NOT_TODAY, type Ritual, ritualBand, shareStub, showsActions } from "@/rituals";
import { clockTime } from "@/time";

import { Button } from "./Button";
import { Card } from "./Card";

type Props = {
  card: Ritual;
  text: string;
  at: string;
  messageId: number;
  buddyName: string;
  // Only the newest message's buttons still make sense to press.
  newest: boolean;
  // Live from the roadmap, since the night review's own flag is frozen when it's sent.
  checkedInToday: boolean;
  onSend: (text: string) => void;
  onCheckIn: () => void;
};

export function RitualCard(props: Props) {
  const { card, text, at } = props;
  return (
    <Card band={ritualBand(card)} bandDetail={clockTime(at)}>
      <Text className="font-body text-body text-ink">{text}</Text>
      {card.kind === "morning" && <Morning {...props} card={card} />}
      {card.kind === "study_share" && <Share card={card} />}
      {card.kind === "ask" && <Ask {...props} card={card} />}
      {card.kind === "night_review" && <NightReview {...props} card={card} />}
    </Card>
  );
}

function PlanRow({ who, topic }: { who: string; topic: TopicRef | null }) {
  return (
    <View className="flex-row gap-3">
      <Text className="w-[56px] font-label text-label uppercase text-ink-muted">{who}</Text>
      <Text className="flex-1 font-meta text-meta text-ink">
        {topic ? `${topic.title} · day ${topic.day}` : "every topic done"}
      </Text>
    </View>
  );
}

function Morning({
  card,
  buddyName,
  newest,
  checkedInToday,
  onSend,
}: Props & { card: MorningCard }) {
  return (
    <>
      <View className="gap-1 rounded-sm bg-surface-sunken p-3">
        <PlanRow who="You" topic={card.you} />
        <PlanRow who={buddyName} topic={card.buddy} />
      </View>
      {showsActions(card, newest, checkedInToday) && (
        <View className="flex-row flex-wrap gap-2">
          {card.quick_replies.map((reply) => (
            <Button key={reply} label={reply} small onPress={() => onSend(reply)} />
          ))}
        </View>
      )}
    </>
  );
}

function Share({ card }: { card: StudyShareCard }) {
  return (
    <>
      {card.shaky.length > 0 && (
        // Labelled as well as highlighted, so colour is never the only cue.
        <View className="gap-1">
          <Text className="font-label text-label uppercase text-ink-muted">Still shaky</Text>
          {card.shaky.map((point) => (
            <Text key={point} className="font-body text-body text-ink">
              <Text className="bg-pencil-soft">{point}</Text>
            </Text>
          ))}
        </View>
      )}
      <View className="flex-row items-center justify-between border-t border-dashed border-line-strong pt-3">
        <Text className="font-trace text-[12px] leading-[14px] text-ink-muted">{shareStub(card)}</Text>
        <Pressable
          accessibilityRole="link"
          hitSlop={12}
          onPress={() => router.navigate("/roadmap")}
        >
          <Text className="font-body-strong text-[14px] leading-[20px] text-you">your turn ↗</Text>
        </Pressable>
      </View>
    </>
  );
}

function Ask({ card, messageId, buddyName }: Props & { card: AskCard }) {
  const later = usePref("asks.later");
  if (later.value?.includes(messageId)) return null;

  return (
    <View className="flex-row flex-wrap gap-2">
      <Button
        label={`Open ${buddyName}'s note`}
        variant="primary"
        small
        onPress={() =>
          router.push({ pathname: "/notebook/[noteId]", params: { noteId: card.note_id } })
        }
      />
      <Button
        label="Later"
        variant="text"
        small
        onPress={() => later.set([...(later.value ?? []), messageId])}
      />
    </View>
  );
}

function NightReview({
  card,
  newest,
  checkedInToday,
  onSend,
  onCheckIn,
}: Props & { card: NightReviewCard }) {
  if (!showsActions(card, newest, checkedInToday)) return null;

  return (
    <View className="flex-row flex-wrap gap-2">
      <Button
        label="I studied today"
        variant="primary"
        small
        onPress={onCheckIn}
      />
      <Button label={NOT_TODAY} small onPress={() => onSend(NOT_TODAY)} />
    </View>
  );
}
