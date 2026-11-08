# Persistent worker and watchdog host setup

This runbook is for the owner-controlled Linux host that will run the persistent
SQLite coordinator, worker daemon and independent watchdog. The GitHub-hosted
Docker acceptance workflow is a separate canary; it is not a substitute for
this persistent host.

## Host prerequisites

- A dedicated unprivileged service account: `marketsage-runner` (UID 110 in
  the current host setup).
- A clean checkout of this repository at `main`, owned/readable by that
  account. The daemon refuses to execute tasks unless the checkout branch is
  `main`, the working tree is clean, and HEAD equals the manifest commit.
- Rootless Docker for that service account, with its user namespace and the
  built-in seccomp profile active. Do not add the worker account to the
  rootful `docker` group: membership is effectively root access.
- The worker image built from `infra/worker-image/Dockerfile`. Record its
  immutable local image ID, not its mutable tag.

The current self-hosted Runner service account has no sudo or rootful Docker
group membership. An administrator must install rootless-container prerequisites
and enable lingering for the service account once. The worker itself runs
without sudo, as UID 65532 inside the container, with no network, no secrets,
read-only root/checkout, dropped capabilities, seccomp, user namespaces and
bounded CPU/memory/PIDs/time/output.

## Prepare the checkout and image

Rootless Docker prerequisites are specific to the service account:

- `newuidmap` and `newgidmap` must be installed (normally from package `uidmap`).
- `/etc/subuid` and `/etc/subgid` must each allocate at least 65,536 subordinate IDs to `marketsage-runner`.
- The rootless Docker setup tool and rootless extras must be installed. With Docker CE packages, the setup tool is normally supplied by `docker-ce-rootless-extras`; distributions packaging Docker differently may place it under a distribution-specific path.

Run as an administrator only for initial prerequisites:

```bash
sudo apt-get update
sudo apt-get install -y uidmap dbus-user-session slirp4netns fuse-overlayfs
grep '^marketsage-runner:' /etc/subuid /etc/subgid || true
sudo loginctl enable-linger marketsage-runner
```

If the UID/GID subordinate ranges are absent or shorter than 65,536, allocate unused ranges for this account in both files before continuing. Do not copy another user's ranges or overlap an existing allocation.

Then enter a real login session for `marketsage-runner` (a systemd user manager must be available; on systems where `sudo -iu` does not provide one, use `machinectl shell marketsage-runner@` after installing `systemd-container`) and run as that unprivileged account:

```bash
command -v dockerd-rootless-setuptool.sh
dockerd-rootless-setuptool.sh install --force
systemctl --user enable --now docker
stat -Lc '%u:%g %a %n' /run/user/110/docker.sock
DOCKER_HOST=unix:///run/user/110/docker.sock docker info --format '{{json .SecurityOptions}}'
```

The `--force` option allows rootless setup while the system-wide Docker daemon remains enabled. Confirm that the socket is owned by UID 110 and that Docker reports both `rootless` (or `userns`) and `seccomp`. Do not repair permission errors with world-writable socket modes or by adding the account to the rootful `docker` group.

After the rootless socket is verified, restart the registered Actions Runner service
so the job process reconnects with the service account's correct runtime directory:

```bash
sudo systemctl restart actions.runner.yarsalam-marketsage.marketsage-local-01.service
```

Run as an administrator only for initial directory ownership:


```bash
sudo install -d -o marketsage-runner -g marketsage-runner -m 0750 /srv/marketsage/app
sudo install -d -o marketsage-runner -g marketsage-runner -m 0750 /srv/marketsage/data
sudo loginctl enable-linger marketsage-runner
```

As `marketsage-runner`, clone/update the public repository into
`/srv/marketsage/app`, check out `main`, and ensure the worktree is clean.
Install/configure rootless Docker for this account and start its user service.
Confirm that the Docker socket is available at
`/run/user/110/docker.sock` and that:

```bash
DOCKER_HOST=unix:///run/user/110/docker.sock docker info --format '{{json .SecurityOptions}}'
```

reports both a seccomp profile and `rootless`. The executor also accepts
rootful Docker with userns-remap, but rootless Docker is preferred for this
restricted service account.

Build the pinned worker image as `marketsage-runner`:

```bash
cd /srv/marketsage/app
DOCKER_HOST=unix:///run/user/110/docker.sock docker build \
  --pull --no-cache -f infra/worker-image/Dockerfile \
  -t marketsage-worker:local .
DOCKER_HOST=unix:///run/user/110/docker.sock docker image inspect \
  marketsage-worker:local --format '{{.Id}}'
```

Copy the returned `sha256:<64 hex>` image ID into the environment file below.
Do not use `marketsage-worker:local` as the runtime identity; tags are mutable.

## Configure and install services

Create `/etc/marketsage/worker.env` as root, owned by
`marketsage-runner:marketsage-runner` and mode 0600:

```bash
MARKETSAGE_REPO_DIR=/srv/marketsage/app
MARKETSAGE_DB_PATH=/srv/marketsage/data/control-plane.sqlite3
MARKETSAGE_WORKER_IMAGE_ID=sha256:REPLACE_WITH_LOCAL_IMAGE_ID
MARKETSAGE_WORKER_ID=marketsage-docker-worker-01
```

Create `/etc/marketsage/watchdog.env` with the same repo and database paths.
Then install and start the units:

```bash
sudo install -m 0644 infra/systemd/marketsage-worker-daemon.service /etc/systemd/system/
sudo install -m 0644 infra/systemd/marketsage-watchdog.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now marketsage-worker-daemon.service marketsage-watchdog.service
```

Inspect service state and sanitized logs:

```bash
sudo systemctl status marketsage-worker-daemon marketsage-watchdog --no-pager
sudo journalctl -u marketsage-worker-daemon -u marketsage-watchdog -n 100 --no-pager
```

The worker service includes `--owner-confirmed`, but the worker still verifies
that the current checkout is clean `main` and that its HEAD exactly matches
the task manifest SHA. It executes only fixed handler IDs that are present in
the worker allowlist; unrecognized task definitions are skipped.

## Operational limits and evidence

- SQLite WAL is single-host storage. Keep `control-plane.sqlite3` on local
  persistent storage, not NFS or a shared network filesystem.
- The watchdog recovers expired leases and emits sanitized health codes. It
  does not start another provider attempt; the Outbox remains authoritative.
- Missing provider probes/canaries remain UNKNOWN/DEGRADED. A worker heartbeat
  alone is not evidence that a remote provider is healthy.
- GitHub workflow `MarketSage Docker worker acceptance` is scheduled every
  15 minutes after that workflow is merged to the default branch. Each run
  exercises a fresh ephemeral GitHub-hosted VM; it does not replace the
  persistent host services described here.
- Two independent execution backends and real cross-backend no-duplicate
  failover still require a second independently operated host/runtime and a
  provider-specific idempotency/reconciliation conformance test. Two containers
  on one Docker daemon or two fake adapters do not satisfy that criterion.
