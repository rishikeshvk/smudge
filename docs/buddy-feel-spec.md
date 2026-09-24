# Buddy feel spec

2026-09-24 · Status: **in progress**

A module between M4 and M5. M0–M4 work end to end, but the buddy still reads as a polite bot: every reply is 60–70
upbeat words that end in a question, the rituals repeat full topic titles, its "studying" lasts one LLM call, and
explaining its shaky points to it changes nothing. This module makes it feel like a person studying beside you. It is
done when **a simulated day reads like texts from a peer, and a shaky point you explain gets sorted**.

Background: [plan.md](plan.md). Rituals: [m4-spec.md](m4-spec.md).

**Honest fiction still rules.** The buddy is an AI, so it invents no human life: no gym, no coffee, no sleep. Its mood
comes only from real events in its own day (its study, its session, the hour), never from your gap, streak or
check-ins, so mood can't turn into a guilt lever.

## Decisions

| Question | Decision | Rejected |
| --- | --- | --- |
| Personality | One understated voice for everyone: calm, a bit dry, warm but not bubbly. Mood varies it day to day | A temperament picked at naming; random quirks per buddy |
| Reply length | Code measures your last 5 messages and gives the Persona a word budget, `clamp(2.5 × median, 12, 70)`, and says whether emoji are fine | A length validator on `Draft`: each overshoot would cost a paid retry |
| Mood | Plain code from the buddy's own day: `focused`, `tired`, `flat`, `upbeat`, `fried` or `steady`, with a reason built from public titles | An LLM-written mood; any input from the user's behaviour |
| "ok", "thanks", "gn" | A closed list of acknowledgements of 3 tokens or fewer, when the buddy's last message wasn't a question, gets a fixed emoji reaction and no turn. A reaction is not a message, so invariant 5 is untouched | A classifier category, which would change the gate and the probe baselines |
| Several bubbles | The Persona may split a reply with newlines, into 3 bubbles at most. It stays one message, audited whole; the app splits it | One message row per bubble, which breaks `reply_to_id` and the history |
| Study session | `plans.session_minutes`, from the plan's hours a day. The buddy studies from the study time to its end, the Curator writes at the end, and the share follows. Unlock times don't move | Moving `unlock_at` to the session end, which touches plans, replanning, seed and the gate's SQL for a cosmetic gain |
| Messages mid-session | Answered straight away, briefly and in character | Held until the session ends |
| A failed night | Retried once, after local midnight; the morning message says how it went | Leaving the page empty for good |
| Study with me | A user message with a card, which the buddy reacts to; the app shows both lamps and a countdown | Storing joint sessions nobody reads |
| Check-in | "I studied today" takes a feeling and an optional fuzzy point. The server writes the chat message with a `CheckinCard`, so the Roadmap and Chat check-ins behave the same | The app posting "I studied today · finished X" itself |
| Explaining a shaky point | A nightly Reflector checks what you said against the topic's gated sources. A sorted point, with a short insight, is audited like a note and appended to `shaky_resolutions` | Reflecting on every turn, which costs a paid call per message; storing "still unsure" outcomes nobody reads |
| Sorted points in retrieval | The existing gated functions join `shaky_resolutions` with `written_at <= now` | A second query path |

## Fixes

- **Memory roles.** The memory writer credited the buddy's rituals to the user ("they open the day by posting their
  topic"). The chat is now labelled `{name} (you)` / `them`, and rituals are marked as scheduled messages.
- **The Persona's roadmap.** It said "studied" for every unlocked topic, even with no note. `RoadmapEntry.has_note`
  separates studied, unlocked without a note, and not studied yet.
- **Ritual copy.** Understated variants, each topic named once, and "3 days running" instead of "3 days in a row for
  us".
- **`RoadmapView.last_day` and `checked_in_today`.** The app stops counting topics for the finish day and stops trusting
  the night-review card's frozen `checked_in_today`, which let you check in twice.
- **App.**
  - Roadmap, Notebook and the buddy's status refetch on tab focus and when the day rolls over.
  - Paused days show on the Roadmap.
  - Fog is kept per note.
  - A failed send doesn't overwrite a new draft.
  - Status polling pauses off-screen.
  - The draft pill stays until the reply lands.
  - Chat shows check-in errors.
  - The name screen uses the Kindred clock.
  - LampGlow fades out.

## Steps

Each step is built, tested and committed on its own.

| Step | Delivers |
| --- | --- |
| 1 Spec | This document |
| 2 Backend fixes | Memory roles, `has_note`, ritual copy, `last_day` and `checked_in_today` |
| 3 App fixes | The app list above, with regenerated API types |
| 4 Voice | The Persona prompt rewrite, `reply_style.py`, and style numbers in the simulation report |
| 5 Mood | `mood.py`, in `PersonaContext` and `BuddyStatus` |
| 6 Reactions | The acknowledgement path and `messages.reaction` |
| 7 Study session | `plans.session_minutes`, the Curator at session end, the share and night-review windows, presence, the retry |
| 8 App presence | The header ring and mood line, lamp states, split bubbles arriving one by one, reaction chips, date separators, study with me |
| 9 Check-in reflection | The check-in body, `CheckinCard`, the Persona comparing notes; the app's check-in sheet |
| 10 Reflector | `shaky_resolutions`, the Reflector, gated retrieval with sorted points, the ask and the Curator skipping them, the morning thanks |
| 11 App sorted | Sorted ticks and insights in the notebook |
| 12 Wrap-up | A small probe run and a short simulation (paid, asked first), a phone check, results recorded here |
