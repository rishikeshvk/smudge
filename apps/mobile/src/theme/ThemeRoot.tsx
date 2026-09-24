import { DarkTheme, DefaultTheme, ThemeProvider, type Theme } from "expo-router";
import type { ReactNode } from "react";
import { View } from "react-native";

import { themeColors, themeVars, type ThemeName } from "./themeVars";
import { useThemeName } from "./useTheme";

function navigationTheme(theme: ThemeName): Theme {
  const base = theme === "dark" ? DarkTheme : DefaultTheme;
  const color = themeColors[theme];
  return {
    ...base,
    colors: {
      primary: color["--you"],
      background: color["--surface"],
      card: color["--surface-raised"],
      text: color["--ink"],
      border: color["--line"],
      notification: color["--lamp"],
    },
    fonts: {
      regular: { fontFamily: "Onest_400Regular", fontWeight: "400" },
      medium: { fontFamily: "Onest_500Medium", fontWeight: "500" },
      bold: { fontFamily: "Onest_600SemiBold", fontWeight: "600" },
      heavy: { fontFamily: "Parkinsans_700Bold", fontWeight: "700" },
    },
  };
}

export function ThemeRoot({ children }: { children: ReactNode }) {
  const theme = useThemeName();
  return (
    <ThemeProvider value={navigationTheme(theme)}>
      <View style={themeVars[theme]} className="flex-1 bg-surface">
        {children}
      </View>
    </ThemeProvider>
  );
}
