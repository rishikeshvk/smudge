import { useQuery } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { ScrollView, Text, View } from "react-native";

import { readTurnOptions } from "@/api/@tanstack/react-query.gen";
import type { Category, DraftAttempt, Route, TopicRef, TurnTrace } from "@/api/types.gen";
import { clockTime } from "@/time";
import { badgeParts, markEvidence, routeLabel } from "@/turnSummary";

import { LoadState } from "./LoadState";
import { Pill, type PillTone } from "./Pill";
import { Sheet } from "./Sheet";
import { TraceFields, TraceSection } from "./TraceSection";
import { XrayBadge } from "./XrayBadge";

const CATEGORY_TONE: Record<Category, PillTone> = {
  curriculum: "you",
  out_of_plan: "lamp",
  off_topic: "you",
  meta: "you",
  crisis: "leak",
  unsure: "unsure",
};

const ROUTE_TONE: Record<Route, PillTone> = {
  answer: "you",
  deflect: "lamp",
  deflect_out_of_plan: "lamp",
  general: "you",
  crisis: "leak",
};

function topics(refs: TopicRef[]): string {
  return refs.map((ref) => `${ref.title} · day ${ref.day}`).join("\n");
}

function Attempt({ attempt, index, sent }: { attempt: DraftAttempt; index: number; sent: boolean }) {
  const leak = attempt.audit.verdict === "leak";
  const note = leak ? attempt.audit.leaked_topic_slugs.join(", ") : sent ? "sent" : "passed";
  return (
    <View className="gap-2 rounded-sm border border-line p-3">
      <View className="flex-row items-center gap-2">
        <Pill tone={leak ? "leak" : "ok"} text={attempt.audit.verdict} />
        <Text className="font-meta text-meta text-ink-muted">{`attempt ${index + 1} · ${note}`}</Text>
      </View>
      <Text className={`font-body text-[14px] leading-[20px] ${leak ? "text-ink-muted" : "text-ink"}`}>
        {markEvidence(attempt.reply, attempt.audit.evidence).map((segment, at) =>
          segment.marked ? (
            <Text key={at} className="rounded-[3px] bg-leak-soft text-leak">
              {segment.text}
            </Text>
          ) : (
            segment.text
          ),
        )}
      </Text>
    </View>
  );
}

function Trace({ trace, buddyName }: { trace: TurnTrace; buddyName: string }) {
  const { classification, directive, models } = trace;
  const directiveRows: [string, ReactNode][] = [
    ["route", <Pill key="route" tone={ROUTE_TONE[directive.route]} text={routeLabel(directive.route)} />],
  ];
  if (directive.answer_topics.length) directiveRows.push(["answer", topics(directive.answer_topics)]);
  if (directive.deflect_topics.length) directiveRows.push(["locked", topics(directive.deflect_topics)]);
  if (directive.ahead_topics.length) directiveRows.push(["ahead", topics(directive.ahead_topics)]);

  return (
    <>
      <TraceSection title="You asked" detail={clockTime(trace.at)}>
        <Text className="font-body text-body text-ink">{trace.message}</Text>
      </TraceSection>
      <TraceSection title="Classified" detail={models.classifier}>
        <TraceFields
          rows={[
            [
              "category",
              <Pill
                key="category"
                tone={CATEGORY_TONE[classification.category]}
                text={classification.category.replaceAll("_", " ")}
              />,
            ],
            ["topics", classification.topic_slugs.join(", ") || "none"],
            ["why", classification.rationale],
          ]}
        />
      </TraceSection>
      <TraceSection title="Directive">
        <TraceFields rows={directiveRows} />
      </TraceSection>
      <TraceSection title={`Notes ${buddyName} could see`} detail={`${trace.retrieved.length} retrieved`}>
        <TraceFields
          rows={
            trace.retrieved.length
              ? trace.retrieved.map((note) => [
                  `day ${note.day}`,
                  `${note.topic_title} · d=${note.distance.toFixed(2)}`,
                ])
              : [["notes", "none"]]
          }
        />
      </TraceSection>
      <TraceSection title="Drafts" detail={`${models.drafter} · ${models.auditor}`}>
        {trace.attempts.map((attempt, index) => (
          <Attempt
            key={index}
            attempt={attempt}
            index={index}
            sent={!trace.fell_back && index === trace.attempts.length - 1}
          />
        ))}
        {trace.fell_back && (
          <View className="gap-2 rounded-sm border border-line p-3">
            <Pill
              tone={directive.route === "crisis" ? "leak" : "lamp"}
              text={directive.route === "crisis" ? "help template" : "fallback"}
            />
            <Text className="font-body text-[14px] leading-[20px] text-ink">{trace.final_reply}</Text>
          </View>
        )}
      </TraceSection>
      <Text className="font-meta text-meta text-ink-muted">
        {`${models.classifier} · ${models.drafter} · ${models.auditor} · ${(trace.latency_ms / 1000).toFixed(1)} s total`}
      </Text>
    </>
  );
}

type Props = {
  turnId: number;
  buddyName: string;
  onClose: () => void;
};

// "Why <buddy> said that": the whole turn, from classification to the audited reply.
export function TraceSheet({ turnId, buddyName, onClose }: Props) {
  // A finished turn never changes.
  const trace = useQuery({ ...readTurnOptions({ path: { turn_id: turnId } }), staleTime: Infinity });

  return (
    <Sheet onClose={onClose}>
      <View className="flex-row flex-wrap items-baseline justify-between gap-3">
        <Text accessibilityRole="header" className="font-title text-title text-ink">
          {`Why ${buddyName} said that`}
        </Text>
        {trace.data && <XrayBadge parts={badgeParts(trace.data)} />}
      </View>
      <ScrollView contentContainerClassName="gap-4 pb-2">
        <LoadState isPending={trace.isPending} error={trace.error} />
        {trace.data && <Trace trace={trace.data} buddyName={buddyName} />}
      </ScrollView>
    </Sheet>
  );
}
