import { router, useLocalSearchParams } from "expo-router";

import { useBuddy } from "@/buddy";
import { TraceSheet } from "@/components/TraceSheet";

export default function Trace() {
  const { turnId } = useLocalSearchParams<{ turnId: string }>();
  const buddy = useBuddy();
  const name = buddy.data?.name ?? "Your buddy";

  return <TraceSheet turnId={Number(turnId)} buddyName={name} onClose={() => router.back()} />;
}
