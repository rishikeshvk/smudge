import { Text, View } from "react-native";

import { Screen } from "@/components/Screen";
import { SplitTitle } from "@/components/SplitTitle";
import { chat } from "@/mocks/chat";
import { ambientBackground, ambientForHour } from "@/theme/ambient";

// Fixed until the app reads the backend Clock.
const MOCK_HOUR = 8;

export default function Chat() {
  return (
    <Screen background={ambientBackground[ambientForHour(MOCK_HOUR)]}>
      <View className="gap-2 pt-8">
        <SplitTitle quiet="Day 9, " loud="together" />
        {chat.map((turn, index) => (
          <Text
            key={index}
            className={`font-body text-body ${turn.speaker === "user" ? "text-you" : "text-ink"}`}
          >
            {turn.text}
          </Text>
        ))}
      </View>
    </Screen>
  );
}
