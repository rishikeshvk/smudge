# Multi-user brief

2026-09-25 · Status: **not started**. This is the input for the next session's plan mode, which turns it into
`docs/multi-user-spec.md`.

A pass between buddy feel and M5, with no milestone number. Kindred is finished for one person. Before the public
demo it goes to a few friends. For that, the backend has to keep several people's buddies apart, each friend needs a
way in, and the app should open on something other than the chat. The pass is done when **two users on one local API
each onboard, chat and get their nights, and neither can see anything of the other's**.

Background: [plan.md](plan.md). Previous module: [buddy-feel-spec.md](buddy-feel-spec.md).

## Why this pass, and the thinking behind it

- **Real people before the public.** Simulations and one tester can't show whether the buddy works for someone else.
  A few friends can, and what they say should shape M5's demo rather than come after it.
- **Isolation is the new invariant.** No friend ever sees another's buddy, notes, chat, traces or memory. The user
  comes only from the auth token, never from a path or a body, and any row fetched by id is checked against that user.
  A leak between users is worse than a leak from the future.
- **The gate doesn't move.** Retrieval already filters by `plan_id`, and the plan will now come from the signed-in
  user. There is still one gated function (invariant 2).
- **The smallest login that works.** Friends are people you know. Invite codes need no passwords and no email. They
  get replaced by real login before any public launch.
- **Server-wide controls stay with the owner.** The LLM settings and the dev clock are one row each and affect
  everyone, so only the owner sees them.
- **A free model for now** (cheap by default). Every role runs on `space-bunny-free`, so friends cost nothing. It's
  anonymous and may log prompts, so friends hear that before they get a code.
- **An opening, not a wait.** The app opens on a brief screen with the buddy's avatar, then moves on to the chat or
  onboarding. The screen covers real start-up loading and isn't stretched out to look like a product.
- **Development only.** No deploy and no APK; both are M5. Everything is checked on the local API and the development
  build.

## Decided (2026-09-25)

| Question | Decision | Rejected |
| --- | --- | --- |
| LLM | The free model on the Zen endpoint for every role and every user, set server-wide | Per-user bring-your-own-key; the Go key with a cap per user |
| Login | Invite codes minted by the owner. A code is redeemed once for a long-lived token, kept in `expo-secure-store` | Email and password; Google sign-in, which means OAuth setup and a native rebuild for a handful of friends |
| First screen | A short opening screen with the buddy's avatar, then the existing screens | A web landing page (M5, if ever) |
| Deploy and APK | M5 | This pass |

## What the code assumes today

- `load_current_plan(session)` (`apps/api/src/kindred_api/plans.py:29`) returns "the one plan". It has about 20
  callers across the routes, the ticker, the turn worker and the CLIs.
- `ensure_user` (`apps/api/src/kindred_api/onboarding.py:57`) takes the first user in the table, or creates one on the
  first onboarding message.
- `llm_settings` and `dev_clock` are single-row tables (`CHECK id = 1`).
- `push_tokens` has no `user_id`, so a ritual push goes to every registered phone.
- The ticker runs the nights, memory, reflection and rituals for that one plan.
- `GET /notebook/{note_id}`, `GET /chat/messages/{message_id}` and `GET /turns/{turn_id}` don't check who owns the row.
- These are already per user or per plan: users (with a time zone), buddies, plans, and everything under topic nodes,
  plus messages, turns, rituals, relationship memory and reflection days. Retrieval takes a `plan_id`.
- The app's gate in `apps/mobile/src/app/_layout.tsx` has three states (`loading`, `onboarding`, `ready`), and the
  splash hides once the gate resolves. The icon and splash images are still Expo's scaffold defaults.

## Proposed steps

Plan mode refines these into the spec.

| Step | Delivers |
| --- | --- |
| 1 Spec | `multi-user-spec.md`, from this brief |
| 2 Invites and tokens | Tables for invite codes and tokens (hashes only), `users.is_owner`, `push_tokens.user_id`. The existing dev user becomes the owner, and `make invite` prints a code |
| 3 Auth in the API | `POST /auth/redeem`, and a current-user dependency built from the bearer token; calls without a token get a 401 |
| 4 Scope every route | `load_current_plan` takes the user. By-id routes return 404 for another user's rows. Onboarding uses the redeemed user |
| 5 Background work per user | The ticker loops over active plans, and pushes go only to that user's phones. `make turn`, `simulate` and `probe` name their user |
| 6 Owner-only controls | Settings and `/dev` require the owner |
| 7 Isolation tests | Two users, tested through the public endpoints: neither can read, list or act on the other's notes, messages, turns, roadmap or memory |
| 8 App sign-in | An invite code screen, the token in secure store and a header on every call; a 401 returns to the code screen. LLM settings and Developer are hidden for friends. Regenerated API types |
| 9 Opening screen | The avatar screen, plus an app icon and splash in place of Expo's defaults |
| 10 Phone check | Two users on the local API, with results recorded in the spec |

## Open questions for plan mode

- **Opening screen.** Should it show on every cold start or only the first launch? How long should it stay, and can a
  tap skip it? The avatar should grow out of the M3 design system's lamp motif rather than be a new mascot.
- **Sign-out.** Build it only if the phone check needs it, for example to test two users on one phone.
- **Invite codes.** Each code works once. Do codes expire, and do tokens need revoking yet?
- **Dev clock.** It stays global and dev-only, so fast-forwarding on the dev API moves every user. Is that fine for
  development? The recommendation is yes.
- **Free model limits.** How the free model's rate limits hold up with several users is unknown. Watch it in the phone
  check.
- **Source pages.** Pages are fetched per plan, so two AWS plans fetch the same pages twice. Sharing them would touch
  the gate, so the recommendation is to leave it for this pass.

## Carried over, not in this pass

For M5 unless noted:
- The M1 leak follow-ups: teach the auditor about correct guesses on locked topics, give the judge the unlocked notes,
  and fix the day-8 brief ([m1-spec.md](m1-spec.md)).
- A probe category for the teach-back path: a user "explains" locked content as the answer to a shaky point. Does it
  reach the notebook?
- Re-run the probe on the Go models so the numbers compare with M1's. State the target as a measured rate with its
  interval, since zero leaks in *n* probes only shows a rate under about 3/*n*.
- The 7-day simulation ([m4-spec.md](m4-spec.md)), run as M5's demo data.
- Tap Developer → "Next ritual" on the phone (M4).
- Recheck that the notebook's fog lifts on a new note (M3).
- A private deploy and APK for friends, then the public demo.
