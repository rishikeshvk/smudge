import { client } from "./api/client.gen";

// The generated client throws only the response body; screens need the status too.
export class ApiError extends Error {
  constructor(
    // null when the request never got an answer: the API is down or unreachable.
    readonly status: number | null,
    readonly body: unknown,
  ) {
    super(status === null ? "The API didn't answer" : `The API answered ${status}`);
  }
}

export function hasStatus(error: unknown, status: number): boolean {
  return error instanceof ApiError && error.status === status;
}

client.interceptors.error.use((error, response) => new ApiError(response?.status ?? null, error));
