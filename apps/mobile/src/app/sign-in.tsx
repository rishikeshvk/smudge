import { useMutation } from "@tanstack/react-query";
import { Info } from "lucide-react-native";
import { useState } from "react";
import { KeyboardAvoidingView, ScrollView, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { redeemInviteMutation } from "@/api/@tanstack/react-query.gen";
import { hasStatus } from "@/apiErrors";
import { Avatar } from "@/components/Avatar";
import { Button } from "@/components/Button";
import { TextField } from "@/components/TextField";
import { formatCode, isComplete } from "@/inviteCode";
import { signIn } from "@/session";
import { useThemeColor } from "@/theme/useTheme";

function problemWith(error: unknown): string {
  if (hasStatus(error, 404)) {
    return "That code doesn't work. It may be used or expired, so ask for a new one.";
  }
  return "Couldn't reach Smudge. Check your connection and try again.";
}

export default function SignIn() {
  const insets = useSafeAreaInsets();
  const inkMuted = useThemeColor("ink-muted");
  const [code, setCode] = useState("");

  const redeem = useMutation({
    ...redeemInviteMutation(),
    // With a token saved, the root gate moves on to onboarding or the app.
    onSuccess: ({ token }) => signIn(token),
  });

  const submit = () => {
    if (isComplete(code)) redeem.mutate({ body: { code } });
  };

  return (
    <KeyboardAvoidingView
      behavior="padding"
      className="flex-1 bg-surface"
      style={{ paddingTop: insets.top, paddingBottom: insets.bottom }}
    >
      <ScrollView
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
        contentContainerClassName="grow justify-center gap-[28px] px-6 py-8"
      >
        <View className="items-center">
          <Avatar state="idle" size={72} />
        </View>
        <View className="gap-2">
          <Text accessibilityRole="header" className="text-center text-ink">
            <Text className="font-display-light text-display">Got an </Text>
            <Text className="font-display-bold text-display">invite code?</Text>
          </Text>
          <Text className="text-center font-body text-body text-ink-muted">
            Smudge is invite-only for now. Ask the person who sent you here for a code.
          </Text>
        </View>
        <TextField
          label="Invite code"
          mono
          value={code}
          onChangeText={(typed) => {
            setCode(formatCode(typed));
            redeem.reset();
          }}
          onSubmitEditing={submit}
          placeholder="ABCD-EFGH"
          autoCapitalize="characters"
          autoCorrect={false}
          autoComplete="off"
          returnKeyType="go"
          helper="Eight letters and numbers. Dashes and spaces don't matter."
          error={redeem.isError ? problemWith(redeem.error) : undefined}
        />
      </ScrollView>
      <View className="gap-4 px-6 pb-[28px] pt-4">
        <View className="flex-row gap-3 rounded-md border border-line bg-surface-raised px-[14px] py-3">
          <Info size={20} strokeWidth={1.75} color={inkMuted} style={{ marginTop: 2 }} />
          <Text className="flex-1 font-meta text-[14px] leading-[20px] text-ink-muted">
            Your buddy is an AI. For now it runs on a free model that may keep what you write, so
            leave out anything private.
          </Text>
        </View>
        <Button
          label={redeem.isPending ? "Checking the code…" : "Continue"}
          variant="primary"
          disabled={!isComplete(code) || redeem.isPending}
          onPress={submit}
        />
      </View>
    </KeyboardAvoidingView>
  );
}
