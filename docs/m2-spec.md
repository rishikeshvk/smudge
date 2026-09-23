# M2 spec: Buddy brain

2026-09-23 · Status: **approved**; design changes during build are noted inline

M2 turns the M1 gate into a buddy: it plans with you, studies on its own schedule from real sources, chats in its
own voice, remembers who you are, and serves all of it over a REST API for the M3 app. It is done when **14 simulated
days run end to end via the Clock**.

Background: [plan.md](plan.md). The gate it builds on: [m1-spec.md](m1-spec.md).

## Decisions

| Question | Decision | Rejected |
| --- | --- | --- |
| How far the Planner goes | Tailors a hand-written curriculum from a catalog (`curricula/*.yaml`, only `aws-2week` today): goal, start date, study time, hours a day. Code fills in the topics | Generating topic graphs: model-written audit briefs nobody has vetted would decide the leak rate |
| Sending a message | `POST` returns `202`; the turn runs in the background and records its stage; the app polls | SSE (React Native has no built-in `EventSource`); a blocking `POST` (no real DraftStatus stages) |
| Relationship memory | Written in a nightly batch, one LLM call per day | After every turn: one more call per message |
| Evals | No probe runs in M2; the 14-day simulation is the only paid run | Re-measuring the leak rate with the Persona |

## Where code lives

- `packages/buddy` (`kindred_buddy`): the pure LLM components (Persona, Curator, Planner, memory writer). Each takes a
  typed contract and returns one. None touches the database.
- `apps/api`: orchestration. Routes in `kindred_api/routes/<area>.py`, jobs, repositories and wiring.
- Gated reads stay in `packages/gate/.../retrieval.py`. Invariant 2 is read as **one module and one SQL filter**:
  a single private predicate (`unlock_at <= now AND written_at <= now`) that every gated read builds on — ranked
  retrieval for the Persona, a by-day listing for the Notebook and Roadmap, and source reads for the Curator. The
  architecture test keeps ledger and source table names out of every other module except one ledger writer.
  Rejected: one function with optional modes.

## Time

- `OffsetClock` = system time + an offset, persisted in a single-row `dev_clock` table so restarts keep it.
- It is used only when `DEV_MODE=true`. Otherwise the API uses `SystemClock` and `/dev/*` answers 404.
- Dev controls, matching the Settings → Developer board:
  - advance by hours (the app sends 24 for "+1 day");
  - jump to a plan day at the same local time of day;
  - back to real time.
- Moving the clock backwards is allowed. It stays safe because every gated read and the chat history filter on
  `<= now`.

## Jobs

One asyncio `tick` loop starts with the API and runs every 60 real seconds. Each job is an idempotent catch-up against
`clock.now()`:
- any unlocked topic with no study session → the Curator studies it;
- any finished plan-local day with chat and no memory snapshot → the memory writer summarises it;
- any queued message while the buddy was unavailable → retried.

Rejected: APScheduler, which the plan names. Wall-clock triggers go wrong when the dev clock jumps, and catch-up needs
a tick anyway; one interval loop needs no library.

## Model roles

Settings roles become classifier, persona (replacing `LLM_MODEL_DRAFTER`), auditor, planner, curator and judge. Each is
added in the step that first uses it. `TurnTrace.models.drafter` keeps its name so the app's generated types don't
change.

## Persona (step 2)

- `Persona` in `packages/buddy` is the gate's drafter. Per turn it gets a `PersonaContext`: buddy name, plan title,
  plan day and the user's local time. `StubDrafter` is gone.
- **Ahead rule.** `run_turn` takes the slugs the user has studied. Routing marks unlocked topics outside that set as
  `ahead_topics`, and the Persona says how they went without teaching them. The decision stays in code. Probes pass
  "kept up", so eval behaviour is unchanged. Real check-ins arrive with the chat API in step 3; until then `make
  turn --user-through N` plays a user who is behind.
- **Crisis.** The classifier has a `crisis` category that beats every other one; it routes to a fixed template that
  drops the persona, says it's an AI and points to emergency numbers and findahelpline.com. Like the fallbacks it is
  vetted by tests, not audited at runtime, and no draft is attempted. Rejected: letting the Persona write crisis
  replies, which puts a model's wording between the user and real help.
- `buddies` holds one buddy per user; `make seed` takes `--buddy-name` (default Juno).

## Chat API (step 3)

| Endpoint | Returns | Notes |
| --- | --- | --- |
| `POST /chat/messages` `{text}` | `202` `ChatMessage` | Queues the message and wakes the turn worker; `409` without a plan |
| `GET /chat/messages/{id}` | `MessageStatus {message, reply}` | Poll this: `message.stage` is the DraftStatus, `reply` appears once answered |
| `GET /chat/messages?before_id&limit` | `ChatMessage[]` oldest first | Only messages at or before the Clock's now |
| `GET /turns/{id}` | `TurnTrace` | A buddy reply's `turn_id`, for the X-ray view |
| `GET /buddy` | `BuddyStatus {name, available}` | `available` is false while the endpoint fails |
| `POST /progress/checkins` | `TopicRef` | "I studied today": marks the user's next topic, in plan order |

- `TurnStage`: `queued → classifying → writing → checking → answered`, or `failed` for a bug. A redraft goes back
  through `writing` and `checking`. Each stage is committed as it happens, so polling sees it.
- **Turn worker.** One asyncio task answers queued messages oldest first, so each reply sees the one before. It
  wakes on every post and retries every 60 s. An `LLMUnavailableError` (connection, 5xx, bad key or usage limit,
  from the chat model or the embedder) rolls the turn back, leaves the message queued and marks the buddy
  unavailable until a turn succeeds. Anything else marks just that message `failed` and is logged. Turns cut off by
  a restart are queued again at startup.
- **History** for a turn is the last 12 messages up to now: every buddy reply so far plus the user's earlier
  messages. Replies sent after this message was queued count, so the buddy remembers what it just said.
- The chat thread belongs to the user; the OpenCode session ID is `chat-<user id>`, stable per conversation.

## Sources (step 4)

- `source_documents` holds each topic's pages: URL, title, main text (trafilatura) and fetch time.
- A topic's reading list is every page its reference notes cite in the curriculum YAML, anchors dropped. A page
  shared by topics is fetched once and stored for each. `make ingest` skips stored pages and prints failures.
- The Curator reads sources only through `read_sources` in `retrieval.py`, on the same `_unlocked` predicate as the
  notes, so material for a locked topic can't reach it. The architecture test now covers `source_documents` too.
- First run, 2026-09-23: 82 pages stored for 14 topics in 14 s. `calculator.aws` (needs JavaScript) and the
  free-tier billing page failed. Pages average 5–13k characters, up to 34k, so the Curator trims them to a budget.

## Curator and nightly study (step 5)

- **When.** The ticker runs every 60 real seconds. Any topic that has unlocked and has no study session yet gets
  studied, oldest first, with the note `written_at` the Clock's now. A dev jump over three days studies three topics
  in one tick. The buddy shows `studying: true` on `GET /buddy` meanwhile.
- **What the Curator sees** (`StudyBrief`): today's topic and its curriculum brief, the baseline card, earlier notes'
  titles and shaky points, and today's sources through `read_sources`, trimmed to 24,000 characters split evenly
  across pages. It never sees another topic's material.
- **What it writes** (`NoteDraft`): a first-person note of at most 400 words, 1–3 honest shaky points (the seeded
  gaps; never deliberate mistakes) and the pages it used. Citations outside the given pages are dropped.
- **Audit, because the Notebook shows notes to the user.** Judged at the topic's own unlock time, so a late study
  can't cover later days:
  1. A code pass flags later topics' specialist vocabulary (`kindred_gate/jargon.py`, the same check the
     curriculum guard test uses). A hit is a sure leak and skips the LLM call.
  2. `LLMAuditor.audit_note` applies the same `LEAK_RULES` as chat.
  3. A leak gets up to two redrafts with feedback. Three leaks, or invalid output, write nothing and record a
     `failed` session: fail closed. (Changed from one redraft after the first 14-day run: day 1's sources mention
     EC2, and one redraft wasn't enough to drop it.) Rejected: falling back to the hand-written note, which would hide Curator failures.
  4. An unavailable endpoint rolls back and waits for the next tick. A topic with no ingested sources waits too.
- **Writes** go through `kindred_api/ledger.py`, the one ledger writer: note plus embedding, then a
  `study_sessions` row with every attempt and verdict.
- **Seeding.** `make seed` no longer stores the hand-written notes; the Curator writes the ledger.
  `--reference-notes` keeps them, and the probe runner uses it so eval results stay comparable with M1.

| Endpoint | Returns |
| --- | --- |
| `GET /roadmap` | `RoadmapView`: plan title, day, and per topic its title, `unlocks_at`, `unlocked`, `buddy_studied`, `user_studied` |
| `GET /notebook` | `NotebookView`: visible notes in plan order, plus `sealed` days (day and unlock time only) |
| `GET /notebook/{id}` | One `NotebookNote`; `404` until it's visible |
| `POST /dev/study-now` | Moves the clock to today's study time if it's earlier, runs a tick, returns `ClockView` |

## Relationship memory (step 6)

- `relationship_memory` holds one snapshot per finished local day: a two-to-three sentence summary in the buddy's
  voice and the full revised list of up to 20 facts. The latest snapshot is the current memory; older ones stay.
- The ticker remembers every finished local day (by the user's timezone) that had chat and has no snapshot, oldest
  first: one LLM call a day, on the Curator's model as part of the nightly batch. Rejected: a separate memory
  model setting, one more knob with no need yet.
- The memory writer is told to keep only facts about the person and the relationship, never subject content.
- The Persona gets the current facts and the last 3 day summaries through `PersonaContext`, as of the Clock's now.
- **Risk.** Memory could still carry subject content the user typed. It never enters the ledger, and the auditor
  checks every reply, so it can shape tone but not get past the gate unaudited.

## Planner onboarding (step 7)

- The catalog is every `curricula/*.yaml` (`CURRICULA_DIR`), shown to the Planner as course titles, day counts,
  topic titles and default study times. Titles are public, so the Planner may name them.
- The Planner (`llm_model_planner`) chats until the course, start date, study time and hours a day are clear, then
  returns a `PlanChoice`. Code builds the `PlanProposal` card from the catalog. It drops a choice naming a course
  that doesn't exist or starting in the past, so the Planner can't invent a plan.
- It pushes back on unsustainable daily time, and says honestly what it has when the goal doesn't match a course.
- **Audit.** Every Planner reply and its quick replies are audited against every catalog topic, all locked:
  onboarding happens before the buddy has studied anything. A leak gets one redraft; a second leak sends a fixed
  fallback (vetted by a test to name nothing from any course) but keeps the card, which code built from public
  titles.
- Messages carry a `thread` (`chat` or `onboarding`), so the chat history, the worker and the Persona never see
  onboarding, and a buddy reply can store its `proposal` for accepting later.

| Endpoint | Returns | Notes |
| --- | --- | --- |
| `POST /onboarding/messages` `{text, timezone}` | `OnboardingReply {message, quick_replies, proposal}` | Blocks for the audited reply; creates the single user; `409` once a plan exists; `422` for an unknown timezone |
| `POST /onboarding/accept` `{proposal_message_id, buddy_name}` | `201` `RoadmapView` | Creates the plan from the card (its start date and study time) and names the buddy |

## Bring-your-own-key settings (step 8)

- `llm_settings` is one row of overrides saved from the app: base URL, API key and a model per role (classifier,
  persona, auditor, planner, curator). Each saved field wins over `.env`; the rest keep their `.env` value.
- The key is stored in plaintext in the local database, the same exposure as `.env`. Rejected: encrypting it with a
  server secret, which is speculative for one local user.
- `LLMRuntime` holds the settings in effect. The worker, ticker and onboarding build their components from it on
  each use, so a save applies to the next call without a restart.

| Endpoint | Returns | Notes |
| --- | --- | --- |
| `GET /settings` | `LLMSettingsView {base_url, api_key_set, models}` | Never the key, not even its last four characters (invariant 7) |
| `PUT /settings` | `LLMSettingsView` | Fields left out keep their value; `api_key` is write-only |
| `POST /settings/test` | `ConnectionCheck {ok, models, detail}` | Lists the endpoint's models, which costs nothing; errors come back generic |

## Steps

Each step is built, reviewed and committed on its own.

| Step | Delivers |
| --- | --- |
| 1 Foundations | This spec, `DEV_MODE`, `OffsetClock` + `dev_clock`, FastAPI lifespan and dependencies, `GET/POST /dev/clock` |
| 2 Persona | Persona drafter with a per-turn context, crisis route, "ahead" rule from user check-ins, one buddy per user |
| 3 Chat API | Persisted chat thread, turn worker with stages, buddy-unavailable queueing, chat/turn/buddy/progress endpoints |
| 4 Sources | `source_documents`, `make ingest` (trafilatura), gated source reads |
| 5 Curator | Nightly notes from sources with seeded gaps, note audit (vocabulary check + LLM), study job, Notebook and Roadmap |
| 6 Memory | Nightly relationship-memory snapshots, fed to the Persona |
| 7 Planner | Catalog-based onboarding chat with an audited plan proposal; accepting creates the plan and the buddy |
| 8 Wrap-up | Bring-your-own-key settings endpoints, `make simulate` over 14 days, results recorded here |

**Deferred:** Curator-drafted ritual messages, pull-forward, streaks and message caps (M4, with the Director);
generated topic graphs; the Persona reading sources directly (it sees only its notes); probe runs.
