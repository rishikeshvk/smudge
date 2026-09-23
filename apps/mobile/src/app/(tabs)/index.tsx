import { useQuery } from "@tanstack/react-query";
import { Text, View } from "react-native";

import { listMessagesOptions } from "@/api/@tanstack/react-query.gen";
import { LoadState } from "@/components/LoadState";
import { Screen } from "@/components/Screen";
import { SplitTitle } from "@/components/SplitTitle";
import { ambientBackground, ambientForHour } from "@/theme/ambient";

// Fixed until the chat step reads the Clock's time.
const PLACEHOLDER_HOUR = 8;

export default function Chat() {
  const messages = useQuery(listMessagesOptions());

  return (
    <Screen background={ambientBackground[ambientForHour(PLACEHOLDER_HOUR)]}>
      <View className="gap-2 pt-8">
        <SplitTitle quiet="Chat with " loud="your buddy" />
        <LoadState isPending={messages.isPending} error={messages.error} />
        {messages.data?.map((message) => (
          <Text
            key={message.id}
            className={`font-body text-body ${message.speaker === "user" ? "text-you" : "text-ink"}`}
          >
            {message.text}
          </Text>
        ))}
      </View>
    </Screen>
  );
}
