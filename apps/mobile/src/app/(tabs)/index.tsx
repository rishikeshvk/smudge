import { Screen } from "@/components/Screen";
import { SplitTitle } from "@/components/SplitTitle";
import { ambientBackground, ambientForHour } from "@/theme/ambient";

// Fixed until the app reads the backend Clock.
const MOCK_HOUR = 8;

export default function Chat() {
  return (
    <Screen background={ambientBackground[ambientForHour(MOCK_HOUR)]}>
      <SplitTitle quiet="Day 9, " loud="together" />
    </Screen>
  );
}
