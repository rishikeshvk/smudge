import { Text } from "react-native";

type Props = {
  quiet: string;
  loud: string;
};

// At most one per screen: a light phrase with one bold part.
export function SplitTitle({ quiet, loud }: Props) {
  return (
    <Text accessibilityRole="header" className="font-display-light text-display text-ink">
      {quiet}
      <Text className="font-display-bold">{loud}</Text>
    </Text>
  );
}
