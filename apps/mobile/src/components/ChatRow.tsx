import { Text, View } from "react-native";

import { isInFlight } from "@/draftStage";
import type { ThreadRow } from "@/thread";
import { clockTime } from "@/time";

import { Bubble } from "./Bubble";
import { Button } from "./Button";

type Props = {
  row: ThreadRow;
  buddyName: string;
  buddyAvailable: boolean;
  onResend: (text: string) => void;
};

export function ChatRow({ row, buddyName, buddyAvailable, onResend }: Props) {
  const { message, startsRun, endsRun } = row;
  const mine = message.speaker === "user";
  // While the buddy is away nothing moves, so anything unanswered is waiting, whatever
  // stage the list last saw.
  const queued = !buddyAvailable && isInFlight(message);
  const failed = mine && message.stage === "failed";

  return (
    <View className={`gap-1 ${startsRun ? "pt-5" : "pt-2"}`}>
      <Bubble kind={mine ? (queued ? "queued" : "you") : "buddy"} text={message.text} />
      {failed && (
        <View className="flex-row items-center gap-1 self-end">
          <Text className="font-meta text-meta text-leak">{`${buddyName} couldn't answer that one`}</Text>
          <Button label="Resend" variant="text" small onPress={() => onResend(message.text)} />
        </View>
      )}
      {endsRun && (
        <Text className={`font-meta text-meta text-ink-muted ${mine ? "self-end" : "self-start"}`}>
          {queued ? `queued · ${buddyName} will answer when it's back` : clockTime(message.at)}
        </Text>
      )}
    </View>
  );
}
