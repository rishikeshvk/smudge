import { Text } from "react-native";

type Props = {
  isPending: boolean;
  error: unknown;
};

// The plain first-load and can't-reach states; each screen draws its own designed empty view.
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
