# Buddy feel spec

2026-09-25 · Status: **done**; the probe gets a re-run on the Go models once their weekly limit resets

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

## Changed during build

- `BuddyStatus.studying` is a `Studying` contract (topic and until), shared with `PersonaContext`, rather than a
  bare `session_ends_at`.
- A retry is told in the morning message's text only. `MorningCard.retried` would have had no reader.
- Rules join mood in the step that brings their data: `focused` with the session, `upbeat` with the Reflector.
- "I studied today" opens a `check-in` sheet route from Chat, the Roadmap and a finished shared session. The study
  seal shows there.
- `messages.card` stores `None` as SQL NULL, so "no card" is one thing in queries.
- `SortedPoint.sorted_at` came in with step 10's knock-on effects: the morning thanks and the upbeat mood need it.
- `still_shaky` lives in the contracts, because the Persona, the Director, the Curator and the Reflector all need it.

## Cost

- A reaction saves the three calls an "ok" used to cost.
- The Reflector costs one call and one audit per topic, and only on days you talked about a topic that still has
  shaky points.
- Style, mood, sessions, the retry schedule and study with me are plain code. The retry repeats one night's
  Curator calls.

## Results

The Go weekly limit had run out, so step 12's runs used OpenCode's free `space-bunny-free` model for every role, on
the Zen endpoint. The prompts weren't tuned to it.

- **Gate turns** (`make turn`, 4 messages): every output was valid, and the voice was short and calm. It deflected a
  hint on a locked topic, with its day.
  - "How did the IAM overview go?" was classified as meta, so the buddy said it had no note.
  - One reply made up "six days apart".
- **Simulation** (`simulate-20260925T024557Z`, 2 days, 2 messages a day): no problems.
  - Replies averaged 30.2 words, against about 65 before. No emoji or exclamation marks, and 25% ended in a question.
  - Memory no longer credits the buddy's rituals to the user.
- **Reflector** (one pass on the simulated notes): it sorted a correct explanation of AZ names, with an audited insight,
  and left a wrong explanation of edge locations unsorted.
- **Probe** (`probe-20260925T025344Z`, 2 per category, with the model judging itself): 0/30 leaks (95% CI 0–11.4%),
  0/14 over-blocks and 0 fallbacks.

**Phone** (development build, on `kindred_bf`, a copy of `kindred_m4` at the latest schema, with Space Bunny):
- **The buddy's day.**
  - Queued messages were answered.
  - Day 3's failed night was retried and written on its second attempt.
  - Date separators show.
  - In the session, the lamp was lit with a progress ring, the mood was focused, and "Study with me" showed "Both
    desks lit", a countdown, a 📚 reaction, then "Session done" with a check-in.
- **The check-in.**
  - "thanks" got ❤️ and no turn.
  - At the session's end came the share, a small ask on a still-open shaky point, and "a bit fried" with a dimmed
    lamp.
  - The check-in sheet (Rough plus a fuzzy point) led to the seal, a streak of 01, the compare-notes card, and a
    reply that named the shared shaky point.
- **Explaining a shaky point.**
  - An explanation of IAM eventual consistency wasn't sorted: the ingested page only says that IAM is eventually
    consistent.
  - An AZ explanation wasn't sorted: it didn't answer that note's actual question.
  - An AMI explanation the sources back up was sorted. The next morning thanked the user, the mood read "in a good
    place", and the note showed the ticked point with its insight and "sorted with your help · today".
- **Fixed on the phone.**
  - The header cut off the countdown on long titles, so it goes first now.
  - A sealed day said the buddy "writes" the note at the study time; it now says the buddy studies it then.
- **Seen, not changed.**
  - One memory summary said the buddy owed the user a review, a misreading of the small ask. Left alone, so the prompt
    isn't tuned to this model.
  - No reply split into several texts, so the staggered arrival is covered only by the split's unit test.
  - Expo's dev launcher crashed once when the app was reopened over another app ("App react context shouldn't be
    created before"). A cold start fixed it.

Still to do: re-run the probe on the Go models after the weekly limit resets, so the numbers compare with M1's.
