import type { ColorSchemeName } from "react-native";

export type ThemePreference = "system" | "light" | "dark";

export const THEME_CHOICES: { value: ThemePreference; label: string }[] = [
  { value: "system", label: "System" },
  { value: "light", label: "Light" },
  { value: "dark", label: "Dark" },
];

export function colorSchemeFor(preference: ThemePreference | null | undefined): ColorSchemeName {
  return preference === "light" || preference === "dark" ? preference : "unspecified";
}
