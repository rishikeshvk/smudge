import "../global.css";

import { Stack } from "expo-router";

import { ThemeRoot } from "@/theme/ThemeRoot";

export default function RootLayout() {
  return (
    <ThemeRoot>
      <Stack />
    </ThemeRoot>
  );
}
