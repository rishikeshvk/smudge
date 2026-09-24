import { Text, View } from "react-native";

import type { Studying, StudyTogetherCard } from "@/api/types.gen";
import { clockTime, minutesUntil } from "@/time";

import { Button } from "./Button";

function Lamp({ who }: { who: "you" | "buddy" }) {
  return (
    <View className={`h-[14px] w-[14px] rounded-full ${who === "you" ? "bg-you" : "bg-lamp"}`} />
  );
}

// While the buddy studies, an open invitation to study alongside it: body doubling.
export function StudyAlongBar({
  studying,
  joining,
  onJoin,
}: {
  studying: Studying;
  joining: boolean;
  onJoin: () => void;
}) {
  return (
    <View className="flex-row items-center justify-between gap-3 border-b border-line bg-lamp-soft px-4 py-2">
      <Text className="flex-1 font-meta text-meta text-lamp-ink">
        {`Studying ${studying.topic.title} until ${clockTime(studying.until)}`}
      </Text>
      <Button label={joining ? "Joining…" : "Study with me"} small disabled={joining} onPress={onJoin} />
    </View>
  );
}

// The user's side of a shared session: both lamps on and the time left, then a check-in.
export function StudyTogetherNote({
  card,
  buddyName,
  now,
  checkedInToday,
  checkingIn,
  onCheckIn,
}: {
  card: StudyTogetherCard;
  buddyName: string;
  now: Date;
  checkedInToday: boolean;
  checkingIn: boolean;
  onCheckIn: () => void;
}) {
  const left = minutesUntil(card.until, now);
  return (
    <View className="w-[78%] gap-2 self-end rounded-md border border-line bg-surface-raised p-3">
      <View className="flex-row items-center gap-2">
        <Lamp who="you" />
        <Lamp who="buddy" />
        <Text className="flex-1 font-body-strong text-[15px] leading-[20px] text-ink">
          {left > 0 ? "Both desks lit" : "Session done"}
        </Text>
      </View>
      <Text className="font-meta text-meta text-ink-muted">
        {left > 0
          ? `You and ${buddyName}, ${card.topic.title} · ${left} min left`
          : `${buddyName} finished ${card.topic.title}. How did yours go?`}
      </Text>
      {left === 0 && !checkedInToday && (
        <Button
          label={checkingIn ? "Sealing…" : "I studied today"}
          variant="primary"
          small
          disabled={checkingIn}
          onPress={onCheckIn}
        />
      )}
    </View>
  );
}
