import type { ConfigContext, ExpoConfig } from "expo/config";

// The development build gets its own package, name and scheme, so it installs beside the
// preview app instead of replacing it.
const isDevelopmentBuild = process.env.APP_VARIANT === "development";

// The Firebase file for push isn't committed. EAS builds get it from the GOOGLE_SERVICES_JSON
// file variable; local builds read it from this folder.
export default ({ config }: ConfigContext): ExpoConfig => ({
  ...config,
  name: isDevelopmentBuild ? "Smudge Dev" : (config.name ?? "Smudge"),
  slug: config.slug ?? "kindred",
  scheme: isDevelopmentBuild ? "kindred-dev" : config.scheme,
  android: {
    ...config.android,
    package: isDevelopmentBuild ? "dev.kindred.app.dev" : config.android?.package,
    googleServicesFile: process.env.GOOGLE_SERVICES_JSON ?? "./google-services.json",
  },
});
