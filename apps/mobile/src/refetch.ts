import { focusManager, useQueryClient } from "@tanstack/react-query";
import { useFocusEffect } from "expo-router";
import { useCallback, useEffect, useRef } from "react";
import { AppState } from "react-native";

import { useKindredNow } from "./kindredNow";
import { localDate } from "./time";

// React Native has no window focus; the app coming to the foreground stands in for it.
export function useRefetchOnAppFocus() {
  useEffect(() => {
    const subscription = AppState.addEventListener("change", (status) =>
      focusManager.setFocused(status === "active"),
    );
    return () => subscription.remove();
  }, []);
}

// Tab screens stay mounted, so switching back to one refetches nothing on its own.
export function useRefetchOnScreenFocus(refetch: () => unknown) {
  const firstFocus = useRef(true);
  useFocusEffect(
    useCallback(() => {
      if (firstFocus.current) {
        firstFocus.current = false;
        return;
      }
      refetch();
    }, [refetch]),
  );
}

// The streak, rituals and notes all turn over with the day, even while the app stays open.
export function useRefetchOnNewDay() {
  const client = useQueryClient();
  const today = localDate(useKindredNow());
  const seen = useRef(today);
  useEffect(() => {
    if (seen.current === today) return;
    seen.current = today;
    client.invalidateQueries();
  }, [today, client]);
}
