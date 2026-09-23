import type { CreateClientConfig } from "./api/client.gen";
import { config } from "./config";

export const createClientConfig: CreateClientConfig = (clientConfig) => ({
  ...clientConfig,
  baseUrl: config.apiUrl,
});
