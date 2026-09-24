import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "expo-router";
import { ChevronRight } from "lucide-react-native";
import { useState } from "react";
import { KeyboardAvoidingView, Pressable, ScrollView, Switch, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import {
  readClockOptions,
  readSettingsOptions,
  readSettingsQueryKey,
  testConnectionMutation,
  updateSettingsMutation,
} from "@/api/@tanstack/react-query.gen";
import type { LlmSettingsView } from "@/api/types.gen";
import { BackHeader } from "@/components/BackHeader";
import { Button } from "@/components/Button";
import { LoadState } from "@/components/LoadState";
import { Pill } from "@/components/Pill";
import { SettingRow } from "@/components/SettingRow";
import { TextField } from "@/components/TextField";
import { usePref } from "@/prefs";
import { formFrom, formProblem, ROLES, settingsUpdate } from "@/settingsForm";
import { useThemeColor } from "@/theme/useTheme";

function Eyebrow({ text }: { text: string }) {
  return <Text className="font-label text-label uppercase text-ink-muted">{text}</Text>;
}

function ConnectionTest({ dirty }: { dirty: boolean }) {
  const test = useMutation(testConnectionMutation());
  const result = test.data;

  return (
    <View className="gap-2">
      <View className="flex-row flex-wrap items-center gap-2">
        <Button
          label={test.isPending ? "Testing…" : "Test connection"}
          small
          disabled={test.isPending}
          onPress={() => test.mutate({})}
        />
        {result?.ok && <Pill tone="ok" text={`connected · ${result.models.length} models`} />}
        {result && !result.ok && <Pill tone="leak" text="can't connect" />}
        {test.isError && <Pill tone="leak" text="couldn't reach Kindred" />}
      </View>
      {result && !result.ok && result.detail && (
        <Text className="font-meta text-meta text-ink-muted">{result.detail}</Text>
      )}
      {dirty && (
        <Text className="font-meta text-meta text-ink-muted">
          This tests the saved settings. Save your changes first to test them.
        </Text>
      )}
    </View>
  );
}

function SettingsForm({ saved }: { saved: LlmSettingsView }) {
  const insets = useSafeAreaInsets();
  const queryClient = useQueryClient();
  const you = useThemeColor("you");
  const lineStrong = useThemeColor("line-strong");
  const raised = useThemeColor("surface-raised");
  const ink = useThemeColor("ink");
  const xray = usePref("xray");
  // Developer controls exist only while the API runs in dev mode; elsewhere it answers 404.
  const devClock = useQuery({ ...readClockOptions(), retry: false });
  const [form, setForm] = useState(() => formFrom(saved));
  const [replacingKey, setReplacingKey] = useState(!saved.api_key_set);

  const save = useMutation({
    ...updateSettingsMutation(),
    onSuccess: (view) => {
      queryClient.setQueryData(readSettingsQueryKey(), view);
      setForm(formFrom(view));
      setReplacingKey(!view.api_key_set);
    },
  });

  const update = settingsUpdate(saved, form);
  const problem = formProblem(form);

  return (
    <KeyboardAvoidingView behavior="padding" className="flex-1">
      <ScrollView contentContainerClassName="gap-6 px-4 pb-4" keyboardShouldPersistTaps="handled">
        <View className="gap-3">
          <Eyebrow text="Model endpoint" />
          <TextField
            label="Base URL"
            mono
            value={form.baseUrl}
            onChangeText={(baseUrl) => setForm({ ...form, baseUrl })}
            autoCapitalize="none"
            autoCorrect={false}
            keyboardType="url"
          />
          {replacingKey ? (
            <TextField
              label="API key"
              mono
              value={form.apiKey}
              onChangeText={(apiKey) => setForm({ ...form, apiKey })}
              secureTextEntry
              autoCapitalize="none"
              autoCorrect={false}
              placeholder={saved.api_key_set ? "Paste the new key" : "Paste your key"}
              helper="Stored on your server only. Kindred never shows it again."
            />
          ) : (
            // The key is write-only: the app is only ever told whether one is saved.
            <View className="gap-1">
              <Text className="font-body-strong text-[13px] leading-[18px] text-ink">API key</Text>
              <View className="min-h-[48px] flex-row items-center justify-between rounded-sm border-[1.5px] border-line-strong bg-surface-raised pl-3">
                <Text className="font-body text-body text-ink">Key saved</Text>
                <Button label="Replace" variant="text" small onPress={() => setReplacingKey(true)} />
              </View>
              <Text className="font-meta text-meta text-ink-muted">
                Stored on your server only. Kindred never shows it again.
              </Text>
            </View>
          )}
          <ConnectionTest dirty={update !== null} />
        </View>
        <View className="gap-3">
          <Eyebrow text="Model per role" />
          <View className="flex-row flex-wrap gap-3">
            {ROLES.map(({ role, label }) => (
              <View key={role} className="min-w-[140px] flex-1 basis-[45%]">
                <TextField
                  label={label}
                  mono
                  value={form.models[role]}
                  onChangeText={(model) =>
                    setForm({ ...form, models: { ...form.models, [role]: model } })
                  }
                  autoCapitalize="none"
                  autoCorrect={false}
                />
              </View>
            ))}
          </View>
        </View>
        <View className="gap-1">
          <Eyebrow text="Display" />
          <SettingRow label="X-ray view">
            <Switch
              value={xray.value === true}
              onValueChange={(on) => xray.set(on)}
              accessibilityLabel="X-ray view"
              trackColor={{ true: you, false: lineStrong }}
              thumbColor={raised}
            />
          </SettingRow>
          {devClock.data && (
            <Link href="/settings/developer" asChild>
              <Pressable accessibilityRole="button">
                <SettingRow label="Developer · time controls">
                  <ChevronRight size={20} strokeWidth={1.75} color={ink} />
                </SettingRow>
              </Pressable>
            </Link>
          )}
        </View>
      </ScrollView>
      <View
        className="gap-2 border-t border-line bg-surface-raised px-4 pt-3"
        style={{ paddingBottom: insets.bottom + 24 }}
      >
        {problem && update && <Text className="font-meta text-meta text-leak">{problem}</Text>}
        {save.isError && (
          <Text className="font-meta text-meta text-leak">Couldn&apos;t save. Try again.</Text>
        )}
        {save.isSuccess && !update && (
          <Text className="font-meta text-meta text-ok">Saved. The next call uses these settings.</Text>
        )}
        <Button
          label={save.isPending ? "Saving…" : "Save settings"}
          variant="primary"
          disabled={!update || problem !== null || save.isPending}
          onPress={() => update && save.mutate({ body: update })}
        />
      </View>
    </KeyboardAvoidingView>
  );
}

export default function Settings() {
  const insets = useSafeAreaInsets();
  const settings = useQuery(readSettingsOptions());

  return (
    <View className="flex-1 bg-surface" style={{ paddingTop: insets.top }}>
      <BackHeader title="Settings" />
      <View className="px-4">
        <LoadState isPending={settings.isPending} error={settings.error} />
      </View>
      {settings.data && <SettingsForm saved={settings.data} />}
    </View>
  );
}
