import { vars } from "nativewind";

import tokens from "./tokens.json";

export type ThemeName = "light" | "dark";

type TokenValue = string | Record<ThemeName, string>;

const colorTokens: { name: string; value: TokenValue }[] = tokens.color.tokens;
const byName = new Map(colorTokens.map((token) => [token.name, token.value]));

function resolve(value: TokenValue, theme: ThemeName): string {
  const raw = typeof value === "string" ? value : value[theme];
  const reference = raw.match(/^\{(.+)\}$/);
  if (!reference) return raw;
  const target = byName.get(reference[1]);
  if (target === undefined) throw new Error(`Unknown colour token ${raw}`);
  return resolve(target, theme);
}

function colorVars(theme: ThemeName): Record<string, string> {
  return Object.fromEntries(
    colorTokens.map(({ name, value }) => [`--${name}`, resolve(value, theme)]),
  );
}

export const themeColors: Record<ThemeName, Record<string, string>> = {
  light: colorVars("light"),
  dark: colorVars("dark"),
};

export const themeVars = {
  light: vars(themeColors.light),
  dark: vars(themeColors.dark),
};
