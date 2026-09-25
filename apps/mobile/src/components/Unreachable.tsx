import { Text, View } from "react-native";

import { Button } from "./Button";

export function Unreachable({ onRetry, retrying }: { onRetry: () => void; retrying: boolean }) {
  return (
    <View className="flex-1 justify-center gap-4 bg-surface px-6">
      <Text accessibilityRole="header" className="font-title text-title text-ink">
        Can&apos;t reach Smudge
      </Text>
      <Text className="font-body text-body text-ink-muted">
        The Smudge server isn&apos;t answering. Check that it&apos;s running and that your phone
        is connected to it, then try again.
      </Text>
      <Button label={retrying ? "Trying…" : "Try again"} onPress={onRetry} disabled={retrying} />
    </View>
  );
}
