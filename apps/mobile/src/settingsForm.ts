import type { LlmSettingsUpdateWritable, LlmSettingsView, ModelsPerRole } from "./api/types.gen";

export type SettingsForm = {
  baseUrl: string;
  // Empty unless a new key is being entered: the saved key never comes back to the app.
  apiKey: string;
  models: ModelsPerRole;
};

export const ROLES: { role: keyof ModelsPerRole; label: string }[] = [
  { role: "persona", label: "Persona" },
  { role: "auditor", label: "Auditor" },
  { role: "classifier", label: "Classifier" },
  { role: "planner", label: "Planner" },
  { role: "curator", label: "Curator" },
];

export function formFrom(saved: LlmSettingsView): SettingsForm {
  return { baseUrl: saved.base_url, apiKey: "", models: saved.models };
}

export function formProblem(form: SettingsForm): string | null {
  if (!form.baseUrl.trim()) return "The base URL can't be empty.";
  const empty = ROLES.find(({ role }) => !form.models[role].trim());
  return empty ? `The ${empty.label} model can't be empty.` : null;
}

// Only what changed goes to the server; fields left out keep their saved value.
export function settingsUpdate(
  saved: LlmSettingsView,
  form: SettingsForm,
): LlmSettingsUpdateWritable | null {
  const update: LlmSettingsUpdateWritable = {};
  const baseUrl = form.baseUrl.trim();
  if (baseUrl !== saved.base_url) update.base_url = baseUrl;
  if (form.apiKey.trim()) update.api_key = form.apiKey.trim();
  const models = Object.fromEntries(
    ROLES.map(({ role }) => [role, form.models[role].trim()]),
  ) as ModelsPerRole;
  if (ROLES.some(({ role }) => models[role] !== saved.models[role])) update.models = models;
  return Object.keys(update).length > 0 ? update : null;
}
