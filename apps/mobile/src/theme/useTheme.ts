import { useColorScheme } from "react-native";

import { themeColors, type ThemeName } from "./themeVars";

export function useThemeName(): ThemeName {
  return useColorScheme() === "dark" ? "dark" : "light";
}

// For props that take a raw colour (icons, navigation), where className can't reach.
export function useThemeColor(token: string): string {
  const color = themeColors[useThemeName()][`--${token}`];
  if (color === undefined) throw new Error(`Unknown colour token ${token}`);
  return color;
}
