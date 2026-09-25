import { useQuery } from "@tanstack/react-query";
import { router } from "expo-router";
import { useState } from "react";
import { Text, View } from "react-native";

import { readRoadmapOptions } from "@/api/@tanstack/react-query.gen";
import type { Feeling } from "@/api/types.gen";
import { useBuddy } from "@/buddy";
import { useCheckIn } from "@/checkIn";
import { Button } from "@/components/Button";
import { Sheet } from "@/components/Sheet";
import { StudySeal } from "@/components/StudySeal";
import { TextField } from "@/components/TextField";
import { nextForYou } from "@/roadmapProgress";

const FEELINGS: Feeling[] = ["solid", "okay", "rough"];

// "I studied today", with how it went: the buddy compares it with its own note.
export default function CheckIn() {
  const buddy = useBuddy();
  const roadmap = useQuery(readRoadmapOptions());
  const { checkIn, sealed } = useCheckIn();
  const [feeling, setFeeling] = useState<Feeling | null>(null);
  const [fuzzy, setFuzzy] = useState("");

  const name = buddy.data?.name ?? "Your buddy";
  const next = roadmap.data && nextForYou(roadmap.data);

  if (sealed) {
    return <StudySeal topic={sealed.topic} caption={sealed.caption} onClose={() => router.back()} />;
  }

  return (
    <Sheet onClose={() => router.back()}>
      <Text accessibilityRole="header" className="font-title text-title text-ink">
        {next ? `How did ${next.topic.title} go?` : "Every topic is done"}
      </Text>
      {next && (
        <>
          <View className="flex-row gap-2">
            {FEELINGS.map((option) => (
              <Button
                key={option}
                label={option[0].toUpperCase() + option.slice(1)}
                variant={feeling === option ? "primary" : "quiet"}
                small
                grow
                onPress={() => setFeeling(option)}
              />
            ))}
          </View>
          <TextField
            label="What's still fuzzy? (optional)"
            value={fuzzy}
            onChangeText={setFuzzy}
            placeholder="the bit that didn't click"
            helper={`${name} compares it with its own shaky points.`}
            maxLength={280}
          />
          <Button
            label={checkIn.isPending ? "Sealing…" : "Seal it"}
            variant="primary"
            disabled={feeling === null || checkIn.isPending}
            onPress={() =>
              feeling && checkIn.mutate({ body: { feeling, fuzzy: fuzzy.trim() || null } })
            }
          />
        </>
      )}
      {checkIn.isError && (
        <Text className="font-meta text-meta text-leak">Couldn&apos;t save that check-in. Try again.</Text>
      )}
    </Sheet>
  );
}
