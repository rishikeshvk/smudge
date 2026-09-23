import type { BottomTabBarProps } from "expo-router/tabs";
import { Book, MessageSquare, Route, type LucideIcon } from "lucide-react-native";
import { Pressable, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { useThemeColor } from "@/theme/useTheme";
import { useKeyboardOpen } from "@/useKeyboardOpen";

const TABS: Record<string, { label: string; Icon: LucideIcon }> = {
  index: { label: "Chat", Icon: MessageSquare },
  roadmap: { label: "Roadmap", Icon: Route },
  notebook: { label: "Notebook", Icon: Book },
};

export function TabBar({ state, navigation }: BottomTabBarProps) {
  const insets = useSafeAreaInsets();
  const you = useThemeColor("you");
  const inkMuted = useThemeColor("ink-muted");
  const ink = useThemeColor("ink");
  const keyboardOpen = useKeyboardOpen();

  // The composer sits right above the keyboard, so the tab bar steps aside while typing.
  if (keyboardOpen) return null;

  return (
    <View
      className="flex-row border-t border-line bg-surface-raised"
      style={{ paddingBottom: insets.bottom }}
    >
      {state.routes.map((route, index) => {
        const tab = TABS[route.name];
        if (!tab) return null;
        const focused = state.index === index;

        const onPress = () => {
          const event = navigation.emit({
            type: "tabPress",
            target: route.key,
            canPreventDefault: true,
          });
          if (!focused && !event.defaultPrevented) navigation.navigate(route.name, route.params);
        };

        return (
          <Pressable
            key={route.key}
            onPress={onPress}
            accessibilityRole="tab"
            accessibilityState={{ selected: focused }}
            // ink at 12%: the only pressed colour the design allows.
            android_ripple={{ color: `${ink}1F`, borderless: true }}
            className="flex-1 items-center gap-1 pb-3 pt-2"
          >
            <View
              className={`h-[30px] w-[56px] items-center justify-center rounded-full ${focused ? "bg-you-soft" : ""}`}
            >
              <tab.Icon size={22} strokeWidth={1.75} color={focused ? you : inkMuted} />
            </View>
            <Text className={`font-label text-label ${focused ? "text-you" : "text-ink-muted"}`}>
              {tab.label}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );
}
