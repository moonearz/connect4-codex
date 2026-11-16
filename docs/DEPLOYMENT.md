# Deployment template usage

This public repository contains application packaging and reusable templates.
It does not contain a production server inventory or a ready-to-install site
configuration. No script provisions a server, installs proxy configuration or
changes a live homepage automatically.

## Keep actual infrastructure configuration private

Use a private infrastructure repository for actual domains, host-port assignments,
web-root paths, proxy/service definitions, image versions and deployment notes.
Keep credentials and private keys outside Git, in server-only files or a secret
manager. A private repository is not a substitute for secret management.

A possible **example** layout for the private repository is:

```text
infrastructure/
  README.md              # Your server inventory and recovery instructions
  proxy/                 # Your actual site configuration
  services/              # Your service definitions and image versions
  environments/          # Non-secret deployment parameters
```

The application's public Dockerfile and scripts can remain here. The private
repository supplies the inputs and decides when to deploy. Adding these templates
does not require migrating working services or changing their networking.

For local drafting, `deploy/private/` and `deploy/generated/` are excluded from
Git and the Docker build context. Store actual configuration there or outside
this checkout; do not commit it into public docs, progress logs, PR descriptions
or test fixtures. Ignore rules do not remove files already tracked or published.

## Inputs

`deploy/deployment.env.example` documents the interface. Its port/path fields are
intentionally blank. Fill a private copy from your own inspected configuration:

| Input | Purpose |
|---|---|
| `HOST_PORT` | Chosen loopback host port for Connect Four; required by deploy.sh |
| `WORDLE_PORT` | Confirmed host port for the companion service |
| `TICTACTOE_PORT` | Confirmed host port for the companion service |
| `WEB_ROOT` | Absolute path to the intended project-index directory |
| `SITE_URL` | Public site root used by the post-deployment checker |

The container's port is 8000, a generic application interface rather than a
production host-port assignment. The deployment script requires Bash, Git, Docker
and curl. The rendering/checking helpers use standard-library Python 3.

## Use the application deployment script

After reviewing and filling a private environment file, export its parameters in
your deployment shell. For example, with a private local copy:

```bash
set -a
. ./deploy/private/deployment.env
set +a
./deploy.sh
```

Only source a file you control. The script does not load environment files by
itself. It refuses to run without `HOST_PORT` and validates the supplied port.
Optional overrides are `CONTAINER_NAME` (default `connect4`), `IMAGE` (default
`connect4:latest`) and `SKIP_PULL=1` for an explicitly chosen local checkout.

The script requires a clean tracked working tree and pulls with `--ff-only`.
It builds the image, checks a temporary container and learned-agent opening, then
replaces the named container. It polls health and attempts to restore the previous
container if replacement fails. Docker rejects occupied ports; the script does
not stop an unrelated occupant or silently choose another port. Replacement has
a short interruption, and rollback is best effort. Keep your own recovery plan
and configuration backup in the private infrastructure repository.

The image uses Python 3.13, the optional Gunicorn `server` extra, a non-root user,
two workers and a health check. It excludes local environments, experiments and
the optional external solver. Local development and the Makefile defaults are
unchanged. This template assumes a host-based proxy reaching loopback-published
containers; adapt the private configuration if your proxy uses another network.

## Render an example proxy fragment

With parameters exported from your private configuration:

```bash
mkdir -p deploy/generated
python3 scripts/render_caddy.py \
  --tictactoe-port "$TICTACTOE_PORT" \
  --wordle-port "$WORDLE_PORT" \
  --connect4-port "$HOST_PORT" \
  --web-root "$WEB_ROOT" \
  --output deploy/generated/projects.routes
```

Every port and the web root must be explicit. The renderer rejects invalid or
duplicate ports and requires an absolute literal root path. Rendered output is
local/private and ignored; it is not automatically installed.

The fragment is an **example** for a project index with `/tictactoe/`, `/wordle/`
and `/connect4/`. In a private site configuration, placement might look like:

```caddyfile
example.com {
    import /path/to/private/projects.routes
}
```

`example.com` and `/path/to/private/projects.routes` are placeholders. Retain your
actual site/TLS/other settings privately. Do not replace a working server config
with this example or add a duplicate site block. Back up the active configuration,
test the replacement separately, validate the complete candidate configuration,
and use your existing reload mechanism only when those checks pass.

The fragment strips prefixes for Wordle and Connect Four and supplies an explicit
forwarded-prefix header. Enable `CONNECT4_BEHIND_PROXY=1` only behind a trusted
proxy overwriting these headers; the deployment script sets it for the
loopback-published app. Direct local development ignores forwarded prefixes.

The example tic-tac-toe application already owns `/tictactoe/<id>` and its move
and reset endpoints. The template preserves those paths, rewrites only the launch
path, and relaunches expired games. Adjust the private routing if your companion
applications expose different interfaces.

## Project-index example and verification

`deploy/homepage/index.html` is an unbranded static example with inline CSS and
three relative project links. Copy/customize it in the private infrastructure
workflow and install it into the chosen web root yourself. It has no build step.
Adding another project requires a link plus an appropriate private proxy route.

After you perform a deployment, verify the site using its private `SITE_URL`:

```bash
python3 scripts/check_site.py --base-url "$SITE_URL"
```

The checker makes normal test requests for homepage links, canonical slashes,
static assets, both Connect Four seats/all opponents, the companion Wordle API,
and tic-tac-toe launch/move/reset/expired-game behavior. It changes no configuration.
Use it against a separate staging setup before switching live routing. It assumes
the companion apps follow the interfaces represented by the example fragment.

## Public history

Replacing a public file or PR description does not erase previously published
versions. Git objects, PR events or edit history, caches, forks and copies can
remain accessible. These templates contain no server credentials. If credentials
are ever exposed, rotate them and follow the hosting provider's removal process;
simply deleting the text is insufficient.
