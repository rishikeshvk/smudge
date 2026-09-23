import { View } from "react-native";
import { useMarkdown } from "react-native-marked";

import { typeStyle } from "@/theme/typeStyles";
import { useThemeColor, useThemeName } from "@/theme/useTheme";

// The Curator writes markdown (headings, lists, bold, code); it's shown in the design's type.
export function NoteBody({ markdown }: { markdown: string }) {
  const ink = useThemeColor("ink");
  const you = useThemeColor("you");
  const sunken = useThemeColor("surface-sunken");
  const heading = { ...typeStyle("title"), color: ink, marginTop: 8 };
  const subheading = { ...typeStyle("body-strong"), color: ink, marginTop: 8 };

  const elements = useMarkdown(markdown, {
    colorScheme: useThemeName(),
    styles: {
      text: { ...typeStyle("body"), color: ink },
      strong: { ...typeStyle("body-strong"), color: ink },
      em: { fontStyle: "italic" },
      paragraph: { marginVertical: 4 },
      h1: heading,
      h2: subheading,
      h3: subheading,
      li: { ...typeStyle("body"), color: ink },
      list: { gap: 4 },
      link: { color: you },
      codespan: { ...typeStyle("code"), color: ink, backgroundColor: sunken },
      code: { backgroundColor: sunken, borderRadius: 10, padding: 12 },
      codeText: { ...typeStyle("code"), color: ink },
    },
  });

  return <View className="gap-1">{elements}</View>;
}
