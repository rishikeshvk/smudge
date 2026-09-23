import AsyncStorage from "@react-native-async-storage/async-storage";
import { useQuery, useQueryClient } from "@tanstack/react-query";

export type CoachId = "onboarding-name";

// Per-phone conveniences only; anything that must survive a reinstall belongs on the backend.
type Prefs = Record<`coach.${CoachId}`, boolean>;

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

  const set = (value: Prefs[K]) => {
    queryClient.setQueryData(queryKey(key), value);
    AsyncStorage.setItem(key, JSON.stringify(value)).catch((error: unknown) =>
      console.warn(`Couldn't save the ${key} preference`, error),
    );
  };

  return { value: query.data, loaded: query.isSuccess, set };
}
