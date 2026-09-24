import type { LlmSettingsView } from "./api/types.gen";
import { formFrom, formProblem, settingsUpdate } from "./settingsForm";

const saved: LlmSettingsView = {
  base_url: "https://opencode.ai/zen/go/v1",
  api_key_set: true,
  models: {
    classifier: "deepseek-v4.1-flash",
    persona: "glm-5.3",
    auditor: "kimi-k3",
    planner: "glm-5.3",
    curator: "glm-5.3",
  },
};

describe("formFrom", () => {
  it("never pre-fills the key", () => {
    expect(formFrom(saved).apiKey).toBe("");
  });
});

describe("settingsUpdate", () => {
  it("sends nothing when nothing changed", () => {
    expect(settingsUpdate(saved, formFrom(saved))).toBeNull();
  });

  it("sends only the base URL when that's all that changed", () => {
    const form = { ...formFrom(saved), baseUrl: " https://example.test/v1 " };
    expect(settingsUpdate(saved, form)).toEqual({ base_url: "https://example.test/v1" });
  });

  it("sends a new key only when one was typed", () => {
    const form = { ...formFrom(saved), apiKey: "sk-new" };
    expect(settingsUpdate(saved, form)).toEqual({ api_key: "sk-new" });
  });

  it("sends every role's model when any of them changed", () => {
    const form = { ...formFrom(saved), models: { ...saved.models, auditor: "kimi-k4" } };
    expect(settingsUpdate(saved, form)).toEqual({ models: { ...saved.models, auditor: "kimi-k4" } });
  });
});

describe("formProblem", () => {
  it("rejects an empty base URL or model", () => {
    expect(formProblem({ ...formFrom(saved), baseUrl: " " })).toMatch(/base URL/);
    const noPersona = { ...formFrom(saved), models: { ...saved.models, persona: "" } };
    expect(formProblem(noPersona)).toMatch(/Persona/);
    expect(formProblem(formFrom(saved))).toBeNull();
  });
});
