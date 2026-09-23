import { useState } from "react";
import { Pressable, Text, View } from "react-native";

import type { PlanProposal } from "@/api/types.gen";
import { planDate, wallTime } from "@/time";

import { Button } from "./Button";
import { Card } from "./Card";

type Props = {
  proposal: PlanProposal;
  // Only the latest proposal can be accepted; earlier ones are shown for the record.
  onAccept?: () => void;
  onChange?: () => void;
};

const PREVIEW_TOPICS = 7;

function hours(perDay: number): string {
  return Number.isInteger(perDay) ? String(perDay) : perDay.toFixed(1);
}

export function ProposalCard({ proposal, onAccept, onChange }: Props) {
  const [expanded, setExpanded] = useState(false);
  const hidden = proposal.topics.length - PREVIEW_TOPICS;
  const shown = expanded ? proposal.topics : proposal.topics.slice(0, PREVIEW_TOPICS);

  return (
    <Card
      band={`Proposed plan · ${proposal.topics.length} days`}
      bandDetail={`${hours(proposal.hours_per_day)} h/day`}
    >
      <Text className="font-title text-title text-ink">{proposal.title}</Text>
      <Text className="font-meta text-meta text-ink-muted">
        {`We both study around ${wallTime(proposal.study_time)} · starts ${planDate(proposal.start_date)}`}
      </Text>
      <View>
        {shown.map((topic) => (
          <View key={topic.slug} className="flex-row gap-3 border-t border-line py-[6px]">
            <Text
              className="w-[20px] font-counter text-[14px] leading-[20px] text-ink-muted"
              style={{ fontVariant: ["tabular-nums"] }}
            >
              {String(topic.day).padStart(2, "0")}
            </Text>
            <Text className="flex-1 font-meta text-[14px] leading-[20px] text-ink">
              {topic.title}
            </Text>
          </View>
        ))}
        {hidden > 0 && (
          // The whole plan stays one tap away: accepting the card means agreeing to all of it.
          <Pressable
            onPress={() => setExpanded(!expanded)}
            accessibilityRole="button"
            accessibilityState={{ expanded }}
            className="min-h-[44px] flex-row items-center gap-2 border-t border-line"
          >
            {!expanded && (
              <Text className="font-meta text-meta text-ink-muted">
                {`+ ${hidden} more ${hidden === 1 ? "day" : "days"}`}
              </Text>
            )}
            <Text className="font-body-strong text-meta text-you">
              {expanded ? "Show fewer" : "Show all"}
            </Text>
          </Pressable>
        )}
      </View>
      {onAccept && onChange && (
        <View className="flex-row flex-wrap gap-2 pt-1">
          <Button label="Looks good" variant="primary" small onPress={onAccept} />
          <Button label="Change something" small onPress={onChange} />
        </View>
      )}
    </Card>
  );
}
