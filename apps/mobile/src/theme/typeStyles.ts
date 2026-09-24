import type { TextStyle } from "react-native";

import tokens from "./tokens.json";

// For libraries that take style objects instead of classes (the markdown renderer). Mirrors
// tailwind.config.js: expo-google-fonts registers one family per weight.
const FAMILY_PREFIX: Record<string, string> = {
  display: "Parkinsans",
  sans: "Onest",
  mono: "JetBrainsMono",
};
const WEIGHT_SUFFIX: Record<number, string> = {
  300: "300Light",
  400: "400Regular",
  500: "500Medium",
  600: "600SemiBold",
  700: "700Bold",
};

const styles = new Map(
  tokens.type.groups.flatMap((group) =>
    group.styles.map((style) => [
      style.name,
      {
        fontFamily: `${FAMILY_PREFIX[group.family]}_${WEIGHT_SUFFIX[style.fontWeight]}`,
        fontSize: parseFloat(style.fontSize),
        lineHeight: parseFloat(style.lineHeight),
      },
    ]),
  ),
);

export function typeStyle(name: string): TextStyle {
  const style = styles.get(name);
  if (!style) throw new Error(`Unknown type style ${name}`);
  return style;
}
