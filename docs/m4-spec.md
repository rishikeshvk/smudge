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
