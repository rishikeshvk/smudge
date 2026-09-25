import type { CreateClientConfig } from "./api/client.gen";
import { config } from "./config";
import { currentToken } from "./session";

export const createClientConfig: CreateClientConfig = (clientConfig) => ({
  ...clientConfig,
  baseUrl: config.apiUrl,
  // Sent only on the operations the API marks as needing a signed-in user.
  auth: () => currentToken(),
});
