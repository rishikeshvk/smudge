import "../global.css";

import { QueryClientProvider } from "@tanstack/react-query";
import { useFonts } from "expo-font";
import { Stack } from "expo-router";
import * as SplashScreen from "expo-splash-screen";
import { useEffect } from "react";

import { queryClient, useRefetchOnAppFocus } from "@/queryClient";
import { fonts } from "@/theme/fonts";
import { ThemeRoot } from "@/theme/ThemeRoot";

SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
  const [loaded, error] = useFonts(fonts);
  useRefetchOnAppFocus();

  useEffect(() => {
    if (loaded || error) SplashScreen.hideAsync();
  }, [loaded, error]);

  // A font load failure falls back to system fonts rather than a stuck splash.
  if (!loaded && !error) return null;

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeRoot>
        <Stack screenOptions={{ headerShown: false }}>
          <Stack.Screen name="(tabs)" />
          <Stack.Screen name="settings" options={{ headerShown: true, title: "Settings" }} />
        </Stack>
      </ThemeRoot>
    </QueryClientProvider>
  );
}
