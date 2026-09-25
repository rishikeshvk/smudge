# M5 Portfolio spec

2026-09-25 · Status: **in progress** on branch `m5-portfolio`

The last milestone makes Kindred something **someone else can install or watch**, at no cost. Kindred already runs as
an invite-only hosted instance, but its API lives on one PC. M5 adds:
- an always-on free host;
- a landing page that replays a real recorded run;
- a demo video;
- a README;
- a public repo.

It is done when:
- a stranger can open the landing page and watch the replay and the video;
- an invited user can install the APK and chat with a buddy served from the VM while the PC is off;
- the repo is public with its README.

Background: [plan.md](plan.md). Previous module: [multi-user-spec.md](multi-user-spec.md).

## Decisions

| Question | Decision | Rejected |
| --- | --- | --- |
| Backend host | An Oracle Always Free ARM VM (A1.Flex). It takes over the Tailscale node `kindred`, so the Funnel URL compiled into the APK stays the same | The AWS free plan: $100–200 in credits for 6 months, then it's paid, and 1–2 GB is tight for Ollama; staying on the PC |
| Public demo | A static replay of a recorded 7-day run, with each turn's X-ray. Live access stays invite-only | An open live demo, where strangers would spend LLM budget, with companion-chatbot risk |
| Visitors | Watch only. The page says Kindred is invite-only, with no APK link and no request form | A mailto for codes; a public APK |
| Landing host | EAS Hosting (`<name>.expo.app`), deployed from a hand-built static folder | Cloudflare Pages is the fallback. GitHub Pages ties hosting to the repo. An Expo Router web route would mix a marketing page into the Android app's router |
| Leak rate | No new probe runs and no chart yet. The committed numbers are kept, and a way to present them is designed and parked | Leak fixes and a re-run on the Go models, deferred |
| Replay data | A new 7-day `make simulate` on the free Space Bunny model, curated into `replay.json` | The Go models, which spend budget; the owner's real chat, which is private |
| Video | 2–3 minutes of phone capture (scrcpy) edited in Kdenlive, with captions and no voiceover. The full cut goes on YouTube, and a 20–30 s muted loop plays on the landing page | Voiceover; Remotion |
| Name | A new display name chosen on the design canvas. The package `dev.kindred.app` and the Funnel URL stay, so installed apps update in place | Renaming the package, which forces a reinstall |
| Repo | Public at the end, after a secrets scan of the full history | Staying private |
| Design | Claude Design canvas on the Kindred design system (Two Desks) | — |
| Wording | Public and ops text says "invite-only" and "members". The buddy's peer voice keeps its own metaphors | — |

## Design direction

The page is an honest two-desk scene, not a pitch. It shows the mechanism instead of claiming it:
- the replay's X-ray drawer (classification, gated notes, audit verdict);
- a small gate diagram;
- a "what it won't do" section: openly AI, no guilt messages, adults only.

It uses the lamp ambience from dawn to night, `fog` over what the buddy can't see yet, and the notebook's pencil
highlights on shaky points. The copy uses the buddy's understated lowercase voice. No gradient blobs, feature-icon
grids, tilted phone mock-ups, testimonials or stat counters.

Canvas rows:
1. Name candidates.
2. Landing page at 412 and 1440 px, in both themes.
3. The replay's states.
4. The leak-rate presentation (parked).
5. The video storyboard and title cards.

## Steps

1. This spec, the branch and the memories.
2. Leak numbers from the committed probe runs, kept in memory.
3. The design canvas with name candidates; the name is chosen.
4. A 7-day simulation on the free model; the results are committed and copied to `kindred_demo`.
5. `make replay`: a `Replay` contract and a module that exports a curated `apps/site/replay.json` from `kindred_demo`.
6. Design the landing page, the replay states, the parked leak artboard and the video storyboard.
7. `apps/site`: the static landing page, `make site` and `make site-deploy`.
8. The display rename and a new preview APK.
9. The Oracle move, in `docs/deploy.md`: the live database becomes `kindred_live`, and the role "friend" becomes
   "member".
10. The demo video.
11. The README.
12. A secrets scan, then the repo goes public.

## Next, after M5

**Open sign-up with the user's own key.** A visitor installs the APK and signs up without an invite, then enters their
own OpenAI-compatible endpoint and key. It fits "bring your own key" and "cheap by default", and it removes the LLM cost.
It needs:
- self-serve sign-up and an 18+ gate;
- a per-user endpoint and key, encrypted at rest and never returned to the app. Today one owner-only endpoint serves
  everyone;
- Settings for members, with a key check;
- a per-user unavailable state when that user's key runs out;
- capacity limits on the VM, which still runs embeddings, the nightly Curator and the ticker;
- a privacy note and terms.
