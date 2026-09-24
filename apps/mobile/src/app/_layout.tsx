import "../global.css";
import "@/apiErrors";

import { QueryClientProvider } from "@tanstack/react-query";
import { useFonts } from "expo-font";
import { Stack } from "expo-router";
import * as SplashScreen from "expo-splash-screen";
import { useEffect } from "react";

import { gateFor, useBuddy } from "@/buddy";
import { Unreachable } from "@/components/Unreachable";
import { queryClient, useRefetchOnAppFocus } from "@/queryClient";
import { fonts } from "@/theme/fonts";
import { ThemeRoot } from "@/theme/ThemeRoot";

SplashScreen.preventAutoHideAsync();

function AppStack() {
  const buddy = useBuddy();
  const gate = gateFor(buddy);

  useEffect(() => {
    if (gate !== "loading") SplashScreen.hideAsync();
  }, [gate]);

  if (gate === "loading") return null;
  if (gate === "unreachable") {
    return <Unreachable onRetry={() => buddy.refetch()} retrying={buddy.isFetching} />;
  }

  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Protected guard={gate === "ready"}>
        <Stack.Screen name="(tabs)" />
        <Stack.Screen name="notebook/[noteId]" />
      </Stack.Protected>
      <Stack.Protected guard={gate === "onboarding"}>
        <Stack.Screen name="onboarding" />
      </Stack.Protected>
      {/* Reachable before onboarding too: without a working model key, the Planner can't answer. */}
      <Stack.Screen name="settings" />
    </Stack>
  );
}

export default function RootLayout() {
  const [fontsLoaded, fontError] = useFonts(fonts);
  useRefetchOnAppFocus();

  // A font load failure falls back to system fonts rather than a stuck splash.
  if (!fontsLoaded && !fontError) return null;

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeRoot>
        <AppStack />
      </ThemeRoot>
    </QueryClientProvider>
  );
}
