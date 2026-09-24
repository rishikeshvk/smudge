import { focusManager, QueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
import { AppState } from "react-native";

export const queryClient = new QueryClient();

// React Native has no window focus; the app coming to the foreground stands in for it.
export function useRefetchOnAppFocus() {
  useEffect(() => {
    const subscription = AppState.addEventListener("change", (status) =>
      focusManager.setFocused(status === "active"),
    );
    return () => subscription.remove();
  }, []);
}
