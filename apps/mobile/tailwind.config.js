const tokens = require("./src/theme/tokens.json");

// expo-google-fonts registers one family per weight; Android can't pick a weight itself.
const FAMILY_PREFIX = { display: "Parkinsans", sans: "Onest", mono: "JetBrainsMono" };
const WEIGHT_SUFFIX = {
  300: "300Light",
  400: "400Regular",
  500: "500Medium",
  600: "600SemiBold",
  700: "700Bold",
};

const px = (value) => parseFloat(value);
const family = (group, weight) => `${FAMILY_PREFIX[group]}_${WEIGHT_SUFFIX[weight]}`;
const typeStyles = tokens.type.groups.flatMap((group) =>
  group.styles.map((style) => ({ ...style, family: group.family })),
);

const colors = Object.fromEntries(
  tokens.color.tokens.map(({ name }) => [name, `var(--${name})`]),
);

const spacing = Object.fromEntries([
  ["0", "0px"],
  ...tokens.spacing.tokens.map(({ name, value }) => [name.replace("space-", ""), value]),
]);

const borderRadius = Object.fromEntries(
  tokens.radius.tokens.map(({ name, value }) => [name.replace("radius-", ""), value]),
);

const fontSize = Object.fromEntries(
  typeStyles.map((style) => [
    style.name,
    [
      style.fontSize,
      {
        lineHeight: style.lineHeight,
        // RN takes letter spacing in points, the tokens give it in em.
        ...(style.letterSpacing && {
          letterSpacing: `${parseFloat(style.letterSpacing) * px(style.fontSize)}px`,
        }),
      },
    ],
  ]),
);

const fontFamily = {
  ...Object.fromEntries(
    typeStyles.map((style) => [style.name, family(style.family, style.fontWeight)]),
  ),
  // The loud half of a split-weight headline.
  "display-bold": family("display", 700),
};

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{ts,tsx}"],
  presets: [require("nativewind/preset")],
  theme: {
    colors: { transparent: "transparent", ...colors },
    spacing,
    borderRadius,
    fontSize,
    fontFamily,
  },
  plugins: [],
};
