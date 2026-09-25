# Multi-user spec

2026-09-25 · Status: **in progress** on branch `multi-user`

A pass between buddy feel and M5, with no milestone number. Kindred is finished for one person. Before the public
demo, a few friends get to use it. That means three things:
- The backend keeps each person's buddy apart from everyone else's.
- Each friend has a way in.
- The app opens on its own screen, with a real logo instead of Expo's scaffold.

It is done when **two users on one local API each onboard, chat and get their nights, and neither can see anything of
the other's**.

Background: [plan.md](plan.md). Input: [multi-user-brief.md](multi-user-brief.md). Previous module:
[buddy-feel-spec.md](buddy-feel-spec.md).

**Isolation is the new invariant (8 in `AGENTS.md`).** The user comes only from the auth token, never from a path or
a body. Any row fetched by id is checked against that user, and another user's row is a 404. A leak between users is
worse than a leak from the future. The gate doesn't move: retrieval still filters by `plan_id`, and the plan now comes
from the signed-in user.

## Decisions

| Question | Decision | Rejected |
| --- | --- | --- |
| LLM | The free `space-bunny-free` model on the Zen endpoint, for every role and every user, set server-wide | Per-user bring-your-own-key; the Go key with a cap per user |
| Login | Invite codes minted by the owner. A code is redeemed once for a long-lived token, kept in `expo-secure-store` | Email and password; Google sign-in |
| Where users come from | `make invite` creates the user and a one-use code bound to it. `--user N` mints a new code for an existing user (after sign-out, or for the owner's phone). `--owner` creates the owner on a fresh database. Onboarding sets the timezone, as before | Creating the user at redeem, which needs a nullable owner on the invite and a timezone in the redeem body |
| Code format | 8 characters from an alphabet with no 0, O, 1 or I, shown as `ABCD-EFGH` and normalised before hashing. Codes expire after `invite_days` (7). A redeem is one atomic `UPDATE … RETURNING` | No expiry; rate limiting, which isn't needed for a few friends: there are about 10¹² codes and each works once |
| Tokens | `secrets.token_urlsafe(32)`, stored only as a SHA-256 hash. Tokens don't expire. Sign-out deletes the token, and `make revoke` deletes a user's tokens and push tokens | bcrypt or argon2, which only help against guessing low-entropy secrets; a token expiry, which makes friends ask for new codes |
| Auth failures | No token, or a bad one: 401. Owner-only routes: 403 for friends. Another user's row: 404, the same as a missing row | 403 for another user's row, which confirms that the row exists |
| No route missed | Every router except `health` and `auth` is included with a current-user dependency. A test walks `app.routes` and expects 401 without a token | Relying on each handler to take the user |
| Who the app is | `GET /auth/me` returns `Me { is_owner }`, and the app hides LLM settings and Developer for friends | A field on `BuddyStatus`, which 404s before onboarding |
| Push tokens | Each token belongs to a user. Registering upserts and rebinds the token to the caller, so a shared phone follows whoever is signed in. Sign-out also deletes the phone's push token | `on conflict do nothing`, which would leave a phone bound to the previous user |
| Background work | The ticker loops over every user's current plan, each in its own session, so an LLM outage rolls back only that plan. Pushes go only to that user's phones | One session for all plans, where one failure would stop everyone's night |
| Server-wide controls | The LLM settings and `/dev` are owner-only. The dev clock stays global, so fast-forwarding moves every user | A clock per user |
| Source pages | Still fetched per plan, since sharing them would touch the gate | Sharing pages across plans |
| Opening screen | Shows on every cold start, for as long as real start-up takes (token check, `/auth/me`, `/buddy`), with a 600 ms floor so it never just flashes. No tap to skip | First launch only; a fixed 1.5 s |
| Sign-out | In Settings, for everyone | Leaving it out |
| Logo | Three directions grown from the lamp disc, on the Claude Design canvas; the user picks one | Going straight to one mark |

## Steps

Each step is built, tested and committed on its own.

| Step | Delivers |
| --- | --- |
| 1 Spec | This document, and invariant 8 in `AGENTS.md` |
| 2 Design | A "Welcome, sign-in and brand" row on the Kindred Screens canvas: three logo directions, the opening screen, the code screen, and a friend's Settings |
| 3 Invites and tokens | `users.is_owner`, `invites`, `auth_tokens`, `push_tokens.user_id`; `make invite`, `make users`, `make revoke` |
| 4 Auth in the API | `POST /auth/redeem`, `GET /auth/me`, `POST /auth/sign-out`, the current-user dependency on every other router |
| 5 Scope every route | `load_current_plan` takes the user; by-id routes return 404 for another user's rows; onboarding uses the signed-in user |
| 6 Background work per user | The ticker loops over plans, pushes go per user, the turn worker uses the message's user, and the CLIs name their user |
| 7 Owner-only controls | Settings and `/dev` require the owner |
| 8 Isolation tests | Two users, through the public endpoints: neither can read, list or act on the other's rows |
| 9 App sign-in | The code screen, the token in secure store, the auth header, a 401 back to the code screen, sign-out, Settings for friends |
| 10 Brand assets | Icon, adaptive and monochrome icons, splash and notification icon from the chosen mark; a new development build |
| 11 Opening screen | The avatar screen between the splash and the app |
| 12 Phone check | Two users on the local API, with results recorded here |

## Carried over, not in this pass

See the brief's list. It covers the leak follow-ups, the teach-back probe category, the probe re-run on the Go models,
the 7-day simulation, and the deploy and APK. All of them are in M5.
