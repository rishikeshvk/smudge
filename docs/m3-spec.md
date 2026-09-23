# M3 spec: The app

2026-09-23 · Status: **in progress**; design changes during build are noted inline

M3 turns the M2 API into the Android app: onboarding, chat, roadmap, notebook, the X-ray view, settings and dev
time controls. It is done when **a full day's loop works on an Android phone**.

Background: [plan.md](plan.md). The API it reads: [m2-spec.md](m2-spec.md). The design: the "Kindred" design
system and the "Kindred Screens" canvas (claude.ai artifacts; links in the M3 handoff memory).

## Decisions

| Question | Decision | Rejected |
| --- | --- | --- |
| Styling | NativeWind 4 with a theme built from the design system's `tokens.json`; light and dark from one file via CSS variables | NativeWind 5 (release candidate) |
| API types and calls | Generated from the OpenAPI schema by hey-api: types, fetch SDK and TanStack Query options (`make api-types`) | Hand-written types; a hand-rolled fetch layer |
| Phone ↔ PC in development | USB with `adb reverse` for Metro (8081) and the API (8000) (`make mobile-usb`) | Tunnels (the ngrok tunnel dropped, and the API needs a second one) |
| Local preferences | AsyncStorage behind one typed module: X-ray on, coach marks seen, notebook last opened | `expo-secure-store` (for secrets); `expo-sqlite` kv |
| "Now" in the app | The Kindred Clock (`GET /dev/clock`) in dev builds, device time otherwise | Device time only, which ignores the dev clock |
| Sheets | RN `Modal` with a Reanimated slide | `@gorhom/bottom-sheet` for one sheet |
| Glow and seal | `react-native-svg` shapes | `expo-linear-gradient` (linear only) |
| Fog | `expo-blur` plus a `fog` overlay; the overlay alone if blur misbehaves on the device | — |
| Note bodies | `react-native-marked` with renderers in token styles | `react-native-markdown-display` (unmaintained) |
| Onboarding intro | App copy, not a buddy bubble: every buddy message is audited (invariant 5) | A hard-coded greeting in a buddy bubble |
| Surviving a restart mid-onboarding | `GET /onboarding/messages` returns the onboarding thread with stored proposals | Keeping the transcript in app memory only |
| Tests | `jest-expo` for pure logic modules, one test file each; screens are checked on the phone | Snapshot tests |

## Not in M3

These boards have no backend yet and wait for M4: ritual cards (morning, study share, night review), the streak
count, Pull earlier, push notifications, message caps, and the "Next ritual" dev buttons. Renaming the buddy has no
endpoint. Shaky highlights stay in the notebook; chat replies can't be matched to them reliably. The chat header
shows the plan day where the boards show the streak.

## Steps

Each step is built, checked on the phone and committed on its own.

| Step | Delivers |
| --- | --- |
| 1 Scaffold | Token theme, fonts, tab shell, generated SDK with TanStack Query, USB dev loop |
| 2 Onboarding | `GET /onboarding/messages`, root gate on `GET /buddy`, co-planning chat, proposal card, naming, jest-expo |
| 3 Chat | Thread with paging, send and poll with real turn stages, header status, unavailable state, ambient ground, lamp glow |
| 4 X-ray | Header toggle, a badge per buddy reply, the trace sheet |
| 5 Roadmap | Dual rail with fog and level stations, gap line, topic rows, check-in with the study seal |
| 6 Notebook | Notes and sealed days, fog lift for new notes, note detail with markdown and shaky parts |
| 7 Settings | Bring-your-own-key form with a write-only key, connection test, Developer clock controls |
| 8 Wrap-up | Dark and 360 dp pass, accessibility, one real day's loop on a fresh database, results recorded here |
