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
