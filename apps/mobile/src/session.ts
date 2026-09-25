import * as SecureStore from "expo-secure-store";
import { useSyncExternalStore } from "react";

import { queryClient } from "./queryClient";

const TOKEN_KEY = "kindred.token";

export type Session = { loaded: boolean; token: string | null };

let current: Session = { loaded: false, token: null };
const listeners = new Set<() => void>();

function set(next: Session) {
  current = next;
  listeners.forEach((listener) => listener());
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

// Read once at start-up; everything after goes through signIn and forgetSession.
export async function loadSession() {
  let token: string | null = null;
  try {
    token = await SecureStore.getItemAsync(TOKEN_KEY);
  } catch (error) {
    // An unreadable keystore means signing in again, not a stuck app.
    console.warn("Couldn't read the saved sign-in", error);
  }
  set({ loaded: true, token });
}

// Another user's cached answers must never outlive a change of who is signed in.
export async function signIn(token: string) {
  await SecureStore.setItemAsync(TOKEN_KEY, token);
  queryClient.clear();
  set({ loaded: true, token });
}

export async function forgetSession() {
  if (current.token === null) return;
  set({ loaded: true, token: null });
  queryClient.clear();
  await SecureStore.deleteItemAsync(TOKEN_KEY);
}

export function currentToken(): string | undefined {
  return current.token ?? undefined;
}

export function useSession(): Session {
  return useSyncExternalStore(subscribe, () => current);
}
