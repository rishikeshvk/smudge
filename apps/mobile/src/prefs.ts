import AsyncStorage from "@react-native-async-storage/async-storage";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback } from "react";

export type CoachId = "onboarding-name" | "xray-badge" | "fog-lift";

// Per-phone conveniences only; anything that must survive a reinstall belongs on the backend.
type Prefs = Record<`coach.${CoachId}`, boolean> & {
  xray: boolean;
  // An instant on the Kindred Clock, compared with when notes were written.
  "notebook.lastOpened": string;
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
