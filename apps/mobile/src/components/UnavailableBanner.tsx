import { Text, View } from "react-native";

import { Avatar } from "./Avatar";

// Named by what people recognise: the buddy can't reply, not "LLM endpoint 429".
export function UnavailableBanner({ name }: { name: string }) {
  return (
    <View accessibilityRole="alert" className="flex-row items-start gap-3 bg-fog px-4 py-3">
      <Avatar state="away" size={20} />
      <Text className="flex-1 font-body text-[14px] leading-[20px] text-ink">
        <Text className="font-body-strong">{`${name} can't reply right now.`}</Text>
        {" The model endpoint isn't answering (usage limit or outage). Your messages are saved and get answered when it's back."}
      </Text>
    </View>
  );
}
