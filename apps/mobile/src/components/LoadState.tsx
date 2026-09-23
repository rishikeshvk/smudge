import { Text } from "react-native";

type Props = {
  isPending: boolean;
  error: unknown;
};

// Placeholder states until each screen gets its designed empty and unavailable views.
export function LoadState({ isPending, error }: Props) {
  if (error) {
    return (
      <Text className="font-body text-body text-ink-muted">
        Can&apos;t reach Kindred right now.
      </Text>
    );
  }
  if (isPending) return <Text className="font-meta text-meta text-ink-muted">Loading…</Text>;
  return null;
}
