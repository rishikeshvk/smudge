import { defineConfig } from "@hey-api/openapi-ts";

export default defineConfig({
  input: "openapi.json",
  output: "src/api",
  plugins: [
    { name: "@hey-api/client-fetch", runtimeConfigPath: "./src/apiClientConfig" },
    "@hey-api/sdk",
    "@tanstack/react-query",
  ],
});
