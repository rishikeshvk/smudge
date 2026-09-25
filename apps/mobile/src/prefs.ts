import AsyncStorage from "@react-native-async-storage/async-storage";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback } from "react";

import type { ThemePreference } from "./theme/preference";

export type CoachId = "onboarding-name" | "xray-badge" | "fog-lift";

// Per-phone conveniences only; anything that must survive a reinstall belongs on the backend.
type Prefs = Record<`coach.${CoachId}`, boolean> & {
  xray: boolean;
  theme: ThemePreference;
  // The first visit on the Kindred Clock: notes written after it arrive fogged.
  "notebook.firstOpened": string;
  // Fogged notes the user has lifted, by note id.
  "notebook.lifted": number[];
  // Small asks put off with "Later", by message id.
  "asks.later": number[];
};

const queryKey = (key: keyof Prefs) => ["pref", key] as const;

export function usePref<K extends keyof Prefs>(key: K) {
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: queryKey(key),
    queryFn: async () => {
      const raw = await AsyncStorage.getItem(key);
      return raw === null ? null : (JSON.parse(raw) as Prefs[K]);
    },
    staleTime: Infinity,
  });

  // Stable, so screens can save from focus effects without re-running them every render.
  const set = useCallback(
    (value: Prefs[K]) => {
      queryClient.setQueryData(queryKey(key), value);
      AsyncStorage.setItem(key, JSON.stringify(value)).catch((error: unknown) =>
        console.warn(`Couldn't save the ${key} preference`, error),
      );
    },
    [queryClient, key],
  );

  return { value: query.data, loaded: query.isSuccess, set };
}
