import type { ReactNode } from "react";
import { useColorScheme, View } from "react-native";

import { themeVars } from "./themeVars";

export function ThemeRoot({ children }: { children: ReactNode }) {
  const theme = useColorScheme() === "dark" ? "dark" : "light";
  return (
    <View style={themeVars[theme]} className="flex-1 bg-surface">
      {children}
    </View>
  );
}
