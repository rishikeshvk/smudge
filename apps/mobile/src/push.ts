import { useQueryClient } from "@tanstack/react-query";
import Constants from "expo-constants";
import * as Device from "expo-device";
import * as Notifications from "expo-notifications";
import { router } from "expo-router";
import { useEffect } from "react";

import { listMessagesQueryKey } from "./api/@tanstack/react-query.gen";
import { addPushToken } from "./api/sdk.gen";
import { pushSupport } from "./pushSupport";

// Rituals are texts from a friend: a banner, no sound.
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldPlaySound: false,
    shouldSetBadge: false,
    shouldShowBanner: true,
    shouldShowList: true,
  }),
});

async function register(projectId: string) {
  // Android 13 only asks for permission once a channel exists.
  await Notifications.setNotificationChannelAsync("rituals", {
    name: "Rituals",
    importance: Notifications.AndroidImportance.DEFAULT,
  });
  const { granted } = await Notifications.requestPermissionsAsync();
  if (!granted) return;
  const { data } = await Notifications.getExpoPushTokenAsync({ projectId });
  await addPushToken({ body: { token: data }, throwOnError: true });
}

// Registers this phone for the buddy's rituals, and opens Chat when one is tapped.
export function usePush(ready: boolean) {
  const queryClient = useQueryClient();
  const tapped = Notifications.useLastNotificationResponse();

  useEffect(() => {
    if (!ready) return;
    const support = pushSupport({
      isDevice: Device.isDevice,
      executionEnvironment: Constants.executionEnvironment,
      projectId: Constants.expoConfig?.extra?.eas?.projectId ?? Constants.easConfig?.projectId,
    });
    if (!support.ok) {
      console.info(`No push notifications: ${support.reason}`);
      return;
    }
    register(support.projectId).catch((error: unknown) =>
      console.warn("Couldn't register for push notifications", error),
    );
  }, [ready]);

  useEffect(() => {
    if (!ready || !tapped) return;
    queryClient.invalidateQueries({ queryKey: listMessagesQueryKey() });
    router.navigate("/");
  }, [ready, tapped, queryClient]);

  useEffect(() => {
    const arrived = Notifications.addNotificationReceivedListener(() =>
      queryClient.invalidateQueries({ queryKey: listMessagesQueryKey() }),
    );
    return () => arrived.remove();
  }, [queryClient]);
}
