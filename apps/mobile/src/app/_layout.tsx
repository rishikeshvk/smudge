import "../global.css";
import "@/apiErrors";

import { QueryClientProvider } from "@tanstack/react-query";
import { useFonts } from "expo-font";
import { Stack } from "expo-router";
import * as SplashScreen from "expo-splash-screen";
import { useCallback, useEffect, useState } from "react";
import { Appearance } from "react-native";

import { type Gate, gateFor, useBuddy } from "@/buddy";
import { Opening } from "@/components/Opening";
import { Unreachable } from "@/components/Unreachable";
import { queryClient } from "@/queryClient";
import { useRefetchOnAppFocus, useRefetchOnNewDay } from "@/refetch";
import { usePref } from "@/prefs";
import { usePush } from "@/push";
import { loadSession, useSession } from "@/session";
import { fonts } from "@/theme/fonts";
import { colorSchemeFor } from "@/theme/preference";
import { ThemeRoot } from "@/theme/ThemeRoot";

SplashScreen.preventAutoHideAsync();

// Overriding the scheme app-wide also themes native UI: the status bar, keyboard and dialogs.
function useApplyThemePreference() {
  const theme = usePref("theme");
  useEffect(() => {
    if (theme.loaded) Appearance.setColorScheme(colorSchemeFor(theme.value));
  }, [theme.loaded, theme.value]);
}

function AppStack() {
  useApplyThemePreference();
  const session = useSession();
  const buddy = useBuddy();
  const gate = gateFor(session, buddy);
  usePush(gate === "ready");
  useRefetchOnNewDay();
  // Only on a cold start: signing in later goes straight to the next screen.
  const [opening, setOpening] = useState(true);
  const openingGone = useCallback(() => setOpening(false), []);

  return (
    <>
      <Screens gate={gate} onRetry={() => buddy.refetch()} retrying={buddy.isFetching} />
      {opening && <Opening ready={gate !== "loading"} onGone={openingGone} />}
    </>
  );
}

function Screens({
  gate,
  onRetry,
  retrying,
}: {
  gate: Gate;
  onRetry: () => void;
  retrying: boolean;
}) {
  if (gate === "loading") return null;
  if (gate === "unreachable") return <Unreachable onRetry={onRetry} retrying={retrying} />;

  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Protected guard={gate === "ready"}>
        <Stack.Screen name="(tabs)" />
        <Stack.Screen name="notebook/[noteId]" />
        {/* A route, not an RN Modal: Expo Go's modal window clips the bottom 42 dp off a bottom sheet. */}
        <Stack.Screen name="trace/[turnId]" options={{ presentation: "transparentModal", animation: "fade" }} />
        <Stack.Screen name="pull/[slug]" options={{ presentation: "transparentModal", animation: "fade" }} />
        <Stack.Screen name="change-plan" options={{ presentation: "transparentModal", animation: "fade" }} />
        <Stack.Screen name="check-in" options={{ presentation: "transparentModal", animation: "fade" }} />
      </Stack.Protected>
      <Stack.Protected guard={gate === "onboarding"}>
        <Stack.Screen name="onboarding" />
      </Stack.Protected>
      <Stack.Protected guard={gate === "signedOut"}>
        <Stack.Screen name="sign-in" />
      </Stack.Protected>
      {/* Reachable before onboarding too: without a working model key, the Planner can't answer. */}
      <Stack.Protected guard={gate !== "signedOut"}>
        <Stack.Screen name="settings" />
      </Stack.Protected>
    </Stack>
  );
}

export default function RootLayout() {
  const [fontsLoaded, fontError] = useFonts(fonts);
  useRefetchOnAppFocus();
  useEffect(() => {
    void loadSession();
  }, []);

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
