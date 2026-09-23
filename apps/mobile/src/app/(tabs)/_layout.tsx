import { Tabs } from "expo-router";

import { TabBar } from "@/components/TabBar";

export default function TabsLayout() {
  return (
    <Tabs tabBar={(props) => <TabBar {...props} />} screenOptions={{ headerShown: false }}>
      <Tabs.Screen name="index" />
      <Tabs.Screen name="roadmap" />
      <Tabs.Screen name="notebook" />
    </Tabs>
  );
}
