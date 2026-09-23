import type { ReactNode } from "react";
import { Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { Avatar, type AvatarState } from "./Avatar";

type Props = {
  name: string;
  status: string;
  avatar: AvatarState;
  // The status turns lamp-coloured only while the lamp is on.
  lampStatus?: boolean;
  children?: ReactNode;
};

export function BuddyHeader({ name, status, avatar, lampStatus, children }: Props) {
  const insets = useSafeAreaInsets();

  return (
    <View
      className="flex-row items-center gap-3 border-b border-line bg-surface-raised px-4 pb-3"
      style={{ paddingTop: insets.top + 12 }}
    >
      <Avatar state={avatar} />
      <View className="min-w-0 flex-1">
        <Text accessibilityRole="header" className="font-name text-name text-ink">
          {name}
        </Text>
        <Text
          numberOfLines={1}
          className={`font-meta text-meta ${lampStatus ? "text-lamp-ink" : "text-ink-muted"}`}
        >
          {status}
        </Text>
      </View>
      {children}
    </View>
  );
}
