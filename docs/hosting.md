# Hosting

Smudge runs as a small, invite-only service at no cost. The API runs on an always-on Oracle Cloud VM, Tailscale
Funnel gives it a public HTTPS address, and members install a standalone APK. The landing page is separate, on EAS
Hosting at https://smudge.expo.app (`make site-deploy`).

## How it fits together

| Part | What it is |
| --- | --- |
| VM | Oracle Cloud A1.Flex (Arm, 1 OCPU, 6 GB, 50 GB boot volume), Ubuntu 26.04, on a pay-as-you-go account kept inside the Always Free limits. SSH is the only open port; `ssh kindred-vm` reaches it |
| API | The `kindred-api` systemd unit ([`deploy/kindred-api.service`](../deploy/kindred-api.service)) runs `make serve`: Postgres and Ollama in Docker, migrations, then the API on the `kindred_live` database on real time (`DEV_MODE` off), at 127.0.0.1:8100. It starts at boot and restarts on a crash |
| Address | `https://kindred.<tailnet>.ts.net`, a Tailscale Funnel on machine `kindred` (the VM) that proxies to :8100. The Funnel only dials out, so the VM needs no inbound rule for it |
| Backups | The `kindred-backup` timer ([`deploy/kindred-backup.timer`](../deploy/kindred-backup.timer)) dumps `kindred_live` to `~/backups` at 03:30 UTC and keeps 7 days |
| APK | `make mobile-preview`: package `dev.kindred.app`, shown as Smudge, built with the EAS `preview` environment, whose `EXPO_PUBLIC_API_URL` is the address above. Members download it from the repo's latest GitHub Release |
| Fixes | `make mobile-update MSG='...'`: JavaScript changes reach installed APKs on the `preview` channel. A native change needs a new APK, since the runtime version follows the native fingerprint |
| Development build | `dev.kindred.app.dev` ("Smudge Dev", scheme `kindred-dev`), installed beside the preview app |

The address is compiled into the APK, so it must never change. Moving the server means moving the Tailscale node
name, not the URL.

## Running it

Everything on the VM starts by itself. From the repo at `~/smudge`:
- For a new member, `make invite ON=live`, then send them the code. Use `make invite ON=live ARGS='--user N'` for a
  new phone, and `make revoke ON=live ARGS='--user N'` to sign someone out everywhere. `make users ON=live` lists
  everyone.
- `systemctl status kindred-api` and `journalctl -u kindred-api -f` show the API; `tailscale funnel status` shows the
  Funnel.
- The ticker catches up on missed ticks, so a night the VM is down runs late rather than never. Messages sent while
  it's down fail.

## Deploying a change

The VM's repo accepts pushes into its checked-out branch (`receive.denyCurrentBranch updateInstead`), so a change
goes straight from the PC, with a remote `vm` at `kindred-vm:smudge`:

1. `git push vm main`, or `git pull` on the VM once `main` is on GitHub.
2. On the VM: `uv sync --all-packages` if dependencies changed, then `sudo systemctl restart kindred-api`, which
   also runs any new migrations.
3. A changed unit file needs `sudo cp deploy/*.service deploy/*.timer /etc/systemd/system/` and
   `sudo systemctl daemon-reload` first.

## Restoring a backup

```sh
cd ~/smudge
sudo systemctl stop kindred-api
docker compose exec -T db dropdb -U kindred kindred_live
docker compose exec -T db createdb -U kindred kindred_live
docker compose exec -T db pg_restore -U kindred -d kindred_live --no-owner < ~/backups/kindred_live-YYYY-MM-DD.dump
sudo systemctl start kindred-api
```

The backups live on the VM's own disk, so they cover a bad change or a broken database, not losing the VM. Copy one
off the VM (`scp kindred-vm:backups/… .`) before anything risky.

## Setting up a new VM

How this VM was built, for the next move:
1. Allow SSH in (TCP 22) and route `0.0.0.0/0` to an Internet Gateway; without the route, SSH times out.
2. Update the system, add a 2 GB swap file, and check that the clock is synchronised (`chronyc tracking`), since the
   rituals run on real time.
3. Install `docker.io`, `docker-compose-v2`, `make` and uv, and add the user to the `docker` group.
4. Clone the repo, copy `.env` over with `scp` (mode 600), run `uv sync --all-packages` and `make embed-model`.
5. Restore a `pg_dump` of the live database as `kindred_live`, and install and enable both units.
6. In the Tailscale admin console, rename the old machine away from `kindred`. Then, on the VM,
   `sudo tailscale up --hostname=kindred` and `sudo tailscale funnel --bg 8100`. The public DNS record can take a
   few minutes to appear.

Members keep the same APK. Before this VM, the API ran on the owner's PC (`kindred-pc` on the tailnet), and the VM's
`~/backups` now hold the only copies of the live database.
