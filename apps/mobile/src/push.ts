import { useQueryClient } from "@tanstack/react-query";
import Constants from "expo-constants";
import * as Device from "expo-device";
import { router } from "expo-router";
import { useEffect } from "react";

import { addPushToken } from "./api/sdk.gen";
import { pushSupport } from "./pushSupport";

type Notifications = typeof import("expo-notifications");

async function register(notifications: Notifications, projectId: string) {
  // Android 13 only asks for permission once a channel exists.
  await notifications.setNotificationChannelAsync("rituals", {
    name: "Rituals",
    importance: notifications.AndroidImportance.DEFAULT,
  });
  const { granted } = await notifications.requestPermissionsAsync();
  if (!granted) return;
  const { data } = await notifications.getExpoPushTokenAsync({ projectId });
  await addPushToken({ body: { token: data }, throwOnError: true });
}

// Registers this phone for the buddy's rituals, refreshes the thread when one arrives and
// opens Chat when one is tapped.
export function usePush(ready: boolean) {
  const queryClient = useQueryClient();

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

    // A ritual can come with a new note or a new day, so everything is fetched again.
    const refresh = () => queryClient.invalidateQueries();
    const openChat = () => {
      refresh();
      router.navigate("/");
    };
    let stopped = false;
    const subscriptions: { remove: () => void }[] = [];

    // Imported only here: in Expo Go on Android, merely loading the module throws.
    import("expo-notifications")
      .then(async (notifications) => {
        if (stopped) return;
        // Rituals are texts from a friend: a banner, no sound.
        notifications.setNotificationHandler({
          handleNotification: async () => ({
            shouldPlaySound: false,
            shouldSetBadge: false,
            shouldShowBanner: true,
            shouldShowList: true,
          }),
        });
        subscriptions.push(
          notifications.addNotificationReceivedListener(refresh),
          notifications.addNotificationResponseReceivedListener(openChat),
        );
        // A tap that launched the app came before the listener existed.
        if (await notifications.getLastNotificationResponseAsync()) openChat();
        await register(notifications, support.projectId);
      })
      .catch((error: unknown) => console.warn("Couldn't set up push notifications", error));

    return () => {
      stopped = true;
      subscriptions.forEach((subscription) => subscription.remove());
    };
  }, [ready, queryClient]);
}
