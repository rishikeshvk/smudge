# M4 spec: Rituals

2026-09-24 · Status: **in progress**; design changes during build are noted inline

M4 gives the buddy a day of its own. It texts you in the morning, shares what it studied, asks small favours and
checks in at night. A shared streak and the gap between you show on every screen, and you can move the plan. It is
done when **a simulated week feels like a buddy, not a bot**.

Background: [plan.md](plan.md). The API: [m2-spec.md](m2-spec.md). The app: [m3-spec.md](m3-spec.md). The design:
the "Main", "Chat-StudyShare", "Chat-NightReview" and "Roadmap-PullEarlier" boards of the "Kindred Screens" canvas.

## Decisions

| Question | Decision | Rejected |
| --- | --- | --- |
| Who writes rituals | Code templates for the morning message, night review, small ask and the share after a failed study, with 2–3 variants picked by day. The study share after a written note is a `share` field the Curator writes in the same call as the note | LLM-drafted rituals: about 2 more calls a day, and the night review has to report live state anyway |
| Invariant 5 | The study share is part of the note's audit. The ask quotes a shaky point from a note that was audited at its own unlock time, which is before now. The templates hold only public topic titles and are vetted by tests, like the fallbacks. Rituals make no runtime audit calls | Auditing each template at runtime |
| When rituals fire | A Director job in the ticker, after study and memory, catching up against `clock.now()`. Each ritual has a window and is skipped once its window has passed, so a dev jump over three days doesn't send three mornings | Cron or APScheduler triggers (they go wrong when the dev clock jumps, as in M2) |
| Message cap | At most `RITUAL_DAILY_CAP` (default 4) unprompted messages a day, checked in the Director's one send function. The small ask is the first to drop: it only goes out if it leaves room for the night review. Replies don't count | A cap per kind |
| Ritual in the thread | A buddy `Message` with a `card` (JSONB). `ChatMessage.card` is a `RitualCard` union, and `text` carries the prose, so the Persona's history reads rituals as ordinary buddy messages | A separate rituals feed the app merges in |
| Idempotency | A `rituals` row per plan, day and kind (unique), pointing at its message | Querying the cards' JSON |
| Streak | Consecutive local days with at least one check-in, ending today if you've checked in and yesterday otherwise, so today can't break it before midnight | Days you both studied: a failed Curator night would break *your* streak |
| Gap | Topics the buddy has a note for minus topics you've checked in. It's negative when you're ahead. The Persona gets it and names it honestly, without guilt | — |
| Small ask | A shaky point from a note whose topic you've checked in on, so answering is retrieval practice, not a spoiler. It's never asked twice | Asking about the newest note, which you may not have reached |
| Pull earlier | The **slot** is the first topic that is locked and unstudied. The pulled topic takes the slot's day and unlock time. The topics from the slot up to its old day move back one day, so the finish date doesn't change. A pull needs the topic to be locked, unstudied and after the slot, with every prerequisite before the slot day | Swapping two days, which breaks the order of the topics in between |
| Pause and study time | Pausing moves every locked, unstudied topic back N days (1–7). A new study time recomputes the unlock times of locked, unstudied topics only | The Planner replanning in chat, an LLM where a form works |
| Moving topics | `topic_nodes.day` and `unlock_at` may change: they aren't the ledger. Only locked topics with no study session and no note move, so no written note or source changes visibility. `uq(plan_id, day)` becomes deferrable so a shift is one transaction | An append-only schedule log; temporary negative days |
| Push | The app registers an Expo push token. After a ritual commits, the API posts it to Expo's push service with the buddy's name as the title. A failed send is logged and never undoes the message, and a dead token is deleted. Tapping the notification opens Chat. Needs a development build: Expo Go on Android has no remote push since SDK 53 | Local notifications, which only fire while the app runs |
| Schema and contracts | Each is added in the step that first uses it, with its own migration | One migration up front for tables nobody uses yet |

## Rituals

All times are the user's local time. `day` is the plan day.

| Kind | Window | Content |
| --- | --- | --- |
| Morning | `MORNING_RITUAL_TIME` (08:00) until the study time | The buddy's topic for tonight, your next topic, when it studies, and quick replies |
| Study share | From the moment tonight's topic has a study session until midnight | The Curator's `share` and its shaky points, or an honest template if the study failed |
| Small ask | After today's share, until midnight | "Can you check my note on …?" and one shaky point |
| Night review | `NIGHT_REVIEW_TIME` (21:30) until midnight | Where each of you is, the gap and the streak, with "I studied today" and "Not today" |

## Director (step 4)

- `rituals.py` holds the templates. `director.py` decides what is due: each ritual kind has a window, one
  `rituals` row per plan day and kind, and the cap. The ticker calls it after study and memory on every tick.
- Rituals go out even while the model endpoint is down. They're templates plus the share the Curator already
  stored, so an outage shouldn't silence the morning message.
- Days with no topic send nothing: before the plan starts and after it ends.
- The small ask remembers the note and the shaky point it quoted, so it never asks the same thing twice. It picks
  the latest topic the user has checked in on.
- `POST /dev/next-ritual` moves the clock to the next morning, study time or night review and ticks. At study time
  the tick makes the Curator study, which is paid, just like "Run tonight's study now".
- Running the API on a `--reference-notes` database still makes the Curator study. Reference notes write no study
  session, so every unlocked topic still counts as due. Free checks of the Director use `FixedClock` tests, not a
  live server.

## Replanning (step 5)

| Endpoint | Returns | Notes |
| --- | --- | --- |
| `POST /roadmap/pull` `{slug}` | `RoadmapView` | `409` unless `can_pull` |
| `POST /plan/pause` `{days}` | `RoadmapView` | 1–7 days |
| `PUT /plan/study-time` `{study_time}` | `RoadmapView` | Also moves the time the buddy studies from tonight on |

- A topic that moves always gets its unlock time from `plan_moment` and its new day, so every topic still ahead
  unlocks at the plan's study time.
- A topic that can move has no study session, but it can have a note on a `--reference-notes` database. That
  note's `written_at` is its old unlock time, and the gate needs both times to have passed. So a replan can make a
  note appear later than before, never earlier.

## Push (step 6)

- `POST /push/tokens` `{token}` → `204` stores an Expo push token. Registering the same token again is a no-op.
- After the ticker commits a ritual, `Pusher` posts it to `EXPO_PUSH_URL`, one notification per phone. The title is
  the buddy's name, the body is the ritual text, and `data.message_id` is the message.
- Expo accepts push tokens without an access token, so the backend holds no new secret. A failed send is logged. A
  `DeviceNotRegistered` ticket deletes that token.
- The simulation's fresh database has no tokens, so it never pushes.

## App rituals (step 7)

- A buddy message with a `card` is drawn as a ritual card. The band names the ritual and its time.
  - **Morning:** plan rows for both learners, and quick replies sent as ordinary chat messages.
  - **Study share:** a ticket with the shaky points highlighted and a stub leading to the Roadmap.
  - **Small ask:** "Open {name}'s note" and "Later". "Later" is remembered on the phone.
  - **Night review:** "I studied today" checks in, brings up the study seal and posts "I studied today · finished
    {title}" for the buddy to answer. "Not today" posts those words.
- A card's buttons show only while it's the newest message in the thread. Once the user has answered, the buttons
  go, so nobody answers twice.
- The chat header's day chip became the streak chip. The check-in and study seal moved into a `useCheckIn` hook
  shared by the Roadmap and Chat.
- The thread polls every minute while Chat is on screen, so rituals appear without a push notification too.
- Settings → Developer has a "Next ritual" button.

## Steps

Each step is built, tested and committed on its own.

| Step | Delivers |
| --- | --- |
| 1 Spec | This document |
| 2 Streak and gap | `standing.py` (streak and gap together, since the Roadmap and the Persona need both), `RoadmapView.streak` and `gap`, the Persona's context and prompt |
| 3 Study share | `NoteDraft.share`, audited with the note and stored on the study session |
| 4 Director | Ritual templates, the Director's windows, cap and idempotency, the ticker job, `POST /dev/next-ritual` |
| 5 Replanning | Pull earlier, pause and study time; `RoadmapTopic.can_pull` |
| 6 Push backend | Push tokens, `POST /push/tokens`, the Expo sender |
| 7 App rituals | Ritual cards, the streak chip, the "Next ritual" button |
| 8 App replanning | The Pull earlier and Change plan sheets |
| 9 App push | Development build, token registration, notification tap to Chat |
| 10 Wrap-up | A 7-day simulation, a dev-clock week on the phone, results recorded here |
