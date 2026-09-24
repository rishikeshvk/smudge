export type PushSupport = { ok: true; projectId: string } | { ok: false; reason: string };

type Environment = {
  isDevice: boolean;
  // expo-constants' ExecutionEnvironment: "storeClient" is Expo Go.
  executionEnvironment: string;
  projectId: string | undefined;
};

// Remote push needs a real phone, a development or release build, and an EAS project.
export function pushSupport({ isDevice, executionEnvironment, projectId }: Environment): PushSupport {
  if (!isDevice) return { ok: false, reason: "emulators can't get push notifications" };
  if (executionEnvironment === "storeClient") {
    return { ok: false, reason: "Expo Go on Android has no remote push; use the development build" };
  }
  if (!projectId) return { ok: false, reason: "no EAS project ID; run `eas init` in apps/mobile" };
  return { ok: true, projectId };
}
