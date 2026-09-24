import type { ConfigContext, ExpoConfig } from "expo/config";

// The Firebase file for push isn't committed. EAS builds get it from the GOOGLE_SERVICES_JSON
// file variable; local builds read it from this folder.
export default ({ config }: ConfigContext): ExpoConfig => ({
  ...config,
  name: config.name ?? "Kindred",
  slug: config.slug ?? "kindred",
  android: {
    ...config.android,
    googleServicesFile: process.env.GOOGLE_SERVICES_JSON ?? "./google-services.json",
  },
});
