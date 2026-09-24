import { pushSupport } from "./pushSupport";

const phone = { isDevice: true, executionEnvironment: "standalone", projectId: "abc" };

test("a build on a phone with an EAS project can register", () => {
  expect(pushSupport(phone)).toEqual({ ok: true, projectId: "abc" });
});

test("Expo Go, emulators and unlinked projects can't", () => {
  expect(pushSupport({ ...phone, executionEnvironment: "storeClient" }).ok).toBe(false);
  expect(pushSupport({ ...phone, isDevice: false }).ok).toBe(false);
  expect(pushSupport({ ...phone, projectId: undefined }).ok).toBe(false);
});
