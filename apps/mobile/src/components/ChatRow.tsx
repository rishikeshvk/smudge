import { useCallback, useMemo } from "react";
import { Text, View } from "react-native";

import { isInFlight } from "@/draftStage";
import { bubbles, type ThreadRow } from "@/thread";
import { clockTime, dayLabel } from "@/time";

import { Bubble } from "./Bubble";
import { BubbleBurst } from "./BubbleBurst";
import { Button } from "./Button";
import { CoachMark } from "./CoachMark";
import { CompareNotes } from "./CompareNotes";
import { DaySeparator } from "./DaySeparator";
import { ReactionChip } from "./ReactionChip";
import { RitualCard } from "./RitualCard";
import { StudyTogetherNote } from "./StudyTogether";
import { TurnBadge } from "./TurnBadge";

type Props = {
  row: ThreadRow;
  buddyName: string;
  buddyAvailable: boolean;
  now: Date;
  // Arrived while Chat was open: a reply comes in text by text, a reaction pops in.
  fresh: boolean;
  onShown: (messageId: number) => void;
  onResend: (text: string) => void;
  xray: boolean;
  // Only the newest reply carries the one-time hint, so it's never shown twice on screen.
  xrayHint: boolean;
  onOpenTrace: (turnId: number) => void;
  newest: boolean;
  checkedInToday: boolean;
  onCheckIn: () => void;
};

export function ChatRow({
  row,
  buddyName,
  buddyAvailable,
  now,
  fresh,
  onShown,
  onResend,
  xray,
  xrayHint,
  onOpenTrace,
  newest,
  checkedInToday,
  onCheckIn,
}: Props) {
  const { message, startsDay, startsRun, endsRun } = row;
  const mine = message.speaker === "user";
  // While the buddy is away nothing moves, so anything unanswered is waiting, whatever
  // stage the list last saw.
  const queued = !buddyAvailable && isInFlight(message);
  const failed = mine && message.stage === "failed";
  const turnId = message.turn_id;
  const texts = useMemo(() => bubbles(message.text), [message.text]);
  const shown = useCallback(() => onShown(message.id), [onShown, message.id]);

  let body;
  if (message.card?.kind === "study_together") {
    body = (
      <StudyTogetherNote
        card={message.card}
        buddyName={buddyName}
        now={now}
        checkedInToday={checkedInToday}
        onCheckIn={onCheckIn}
      />
    );
  } else if (message.card?.kind === "checkin") {
    body = <CompareNotes card={message.card} buddyName={buddyName} />;
  } else if (message.card) {
    body = (
      <RitualCard
        card={message.card}
        text={message.text}
        at={message.at}
        messageId={message.id}
        buddyName={buddyName}
        newest={newest}
        checkedInToday={checkedInToday}
        onSend={onResend}
        onCheckIn={onCheckIn}
      />
    );
  } else if (mine) {
    body = <Bubble kind={queued ? "queued" : "you"} text={message.text} />;
  } else {
    body = <BubbleBurst texts={texts} fresh={fresh} onShown={shown} />;
  }

  return (
    <View className={`gap-1 ${startsRun ? "pt-5" : "pt-2"}`}>
      {startsDay && <DaySeparator label={dayLabel(message.at, now)} />}
      {body}
      {message.reaction && <ReactionChip emoji={message.reaction} fresh={fresh} />}
      {failed && (
        <View className="flex-row items-center gap-1 self-end">
          <Text className="font-meta text-meta text-leak">{`${buddyName} couldn't answer that one`}</Text>
          <Button label="Resend" variant="text" small onPress={() => onResend(message.text)} />
        </View>
      )}
      {xray && turnId !== null && (
        <View className="gap-3 pt-1">
          <TurnBadge turnId={turnId} onOpen={() => onOpenTrace(turnId)} />
          {xrayHint && (
            <CoachMark
              id="xray-badge"
              text={`Tap a badge to see why ${buddyName} said that`}
              pointing="up"
            />
          )}
        </View>
      )}
      {endsRun && !message.card && (
        <Text className={`font-meta text-meta text-ink-muted ${mine ? "self-end" : "self-start"}`}>
          {queued ? `queued · ${buddyName} will answer when it's back` : clockTime(message.at)}
        </Text>
      )}
    </View>
  );
}
