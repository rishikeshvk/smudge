import { Text, View } from "react-native";

import { isInFlight } from "@/draftStage";
import type { ThreadRow } from "@/thread";
import { clockTime } from "@/time";

import { Bubble } from "./Bubble";
import { Button } from "./Button";
import { CoachMark } from "./CoachMark";
import { RitualCard } from "./RitualCard";
import { TurnBadge } from "./TurnBadge";

type Props = {
  row: ThreadRow;
  buddyName: string;
  buddyAvailable: boolean;
  onResend: (text: string) => void;
  xray: boolean;
  // Only the newest reply carries the one-time hint, so it's never shown twice on screen.
  xrayHint: boolean;
  onOpenTrace: (turnId: number) => void;
  newest: boolean;
  onCheckIn: () => void;
  checkingIn: boolean;
};

export function ChatRow({
  row,
  buddyName,
  buddyAvailable,
  onResend,
  xray,
  xrayHint,
  onOpenTrace,
  newest,
  onCheckIn,
  checkingIn,
}: Props) {
  const { message, startsRun, endsRun } = row;
  const mine = message.speaker === "user";
  // While the buddy is away nothing moves, so anything unanswered is waiting, whatever
  // stage the list last saw.
  const queued = !buddyAvailable && isInFlight(message);
  const failed = mine && message.stage === "failed";
  const turnId = message.turn_id;

  return (
    <View className={`gap-1 ${startsRun ? "pt-5" : "pt-2"}`}>
      {message.card ? (
        <RitualCard
          card={message.card}
          text={message.text}
          at={message.at}
          messageId={message.id}
          buddyName={buddyName}
          newest={newest}
          onSend={onResend}
          onCheckIn={onCheckIn}
          checkingIn={checkingIn}
        />
      ) : (
        <Bubble kind={mine ? (queued ? "queued" : "you") : "buddy"} text={message.text} />
      )}
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
