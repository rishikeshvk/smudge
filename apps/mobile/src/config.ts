// Over `adb reverse`, the PC's API is localhost on the phone too.
export const config = {
  apiUrl: process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000",
};
