# Private beta

A few friends use Kindred before the M5 deploy, at no cost. The API runs on this PC, Tailscale Funnel gives it a
public HTTPS address, and friends install a standalone APK.

## How it fits together

| Part | What it is |
| --- | --- |
| API | `make serve`: the `kindred_friends` database on real time (`DEV_MODE` off), at 127.0.0.1:8100 |
| Address | `https://kindred.tail028abe.ts.net`, a Tailscale Funnel on machine `kindred` that proxies to :8100 |
| APK | `make mobile-preview`: package `dev.kindred.app`, built with the EAS `preview` environment, whose `EXPO_PUBLIC_API_URL` is the address above |
| Fixes | `make mobile-update MSG='...'`: JavaScript changes reach installed APKs on the `preview` channel. A native change needs a new APK, since the runtime version follows the native fingerprint |
| Development build | `dev.kindred.app.dev` ("Kindred Dev", scheme `kindred-dev`), installed beside the friends' app |

The address is compiled into the APK, so it must never change. Moving the server means moving the Tailscale node
name, not the URL.

## Running it

1. `make serve`, and leave it running. `make up` can run beside it on :8000 for development.
2. The Funnel starts with Tailscale. `tailscale funnel status` shows it.
3. For a new friend, `make invite ON=friends`, then send them the APK link from the EAS build page and the code.
   Use `make invite ON=friends ARGS='--user N'` for a new phone, and `make revoke ON=friends ARGS='--user N'` to cut
   someone off.

The PC has to be on and awake for friends to reach the buddy. The ticker catches up on missed ticks, so a night the PC
sleeps through runs late rather than never. Messages sent while it's off fail. If `make serve` stops, start it
again; there's no service that restarts it yet.

Keep the PC on its own Wi-Fi or ethernet, not the phone's hotspot. When the hotspot's network changes, Tailscale
reconnects but the Funnel's relays keep the old route, and the public address stops answering (`unexpected eof`)
while the tailnet address still works. `sudo systemctl restart tailscaled` in a terminal fixes it.

To stop everything: stop `make serve`, run `tailscale funnel --https=443 off`, then `make down`. To start again:
`make serve` and `tailscale funnel --bg 8100`.

## Moving to a VM later

On an always-on VM such as Oracle's free tier:
- run the same stack;
- restore a `pg_dump` of `kindred_friends`;
- bring the VM up as Tailscale node `kindred` with the same Funnel, after removing this PC's node.

Friends keep the same APK.
