# Deploying the Connect Four application

This repository owns the application image and its app-specific deployment
script. Site homepages, proxy configuration, service inventories and the deployment
of other applications belong in a separate infrastructure repository. Actual
server values and credentials must not be committed here.

## Container interface

- Python 3.13 with the optional Gunicorn `server` dependency.
- Non-root execution, two workers, and internal HTTP port 8000.
- `GET /healthz` returns `{"status":"ok"}` when the application is available.
- The trained model, templates and static assets are packaged in the image.
- No database or persistent application volume is required. Game state is
  reconstructed from the move history submitted by the browser.
- Local environments, experimental datasets and the optional external solver
  are excluded from the build context.

Build manually with `docker build -t connect4:latest .`, or use the deployment
script. Neither method configures a proxy or installs a site homepage.

## App-specific deployment script

The script requires Bash, Git, Docker and curl. Export `HOST_PORT` from your
private deployment configuration outside this checkout, then run:

```bash
./deploy.sh
```

There is no host-port default. The script validates the explicit input, requires
a clean tracked working tree, and pulls with `--ff-only`. It builds the image,
checks a temporary container and learned-agent opening, then replaces the named
Connect Four container. It publishes only to loopback, polls health and attempts
to restore the old container if replacement fails. A conflicting port is an error;
no unrelated service is stopped and no alternative port is selected automatically.

Replacement briefly interrupts this application. Rollback is best effort; keep
recovery procedures and the chosen image/version in the private infrastructure
workflow. The script does not migrate or deploy any other application.

Optional overrides:

| Variable | Default | Purpose |
|---|---|---|
| `CONTAINER_NAME` | `connect4` | This application's container name |
| `IMAGE` | `connect4:latest` | Local image tag to build and run |
| `SKIP_PULL` | `0` | Set to `1` for an explicitly chosen local checkout |

After deployment, check the selected endpoint:

```bash
curl --fail "http://127.0.0.1:$HOST_PORT/healthz"
docker logs --tail 50 connect4
```

Use your chosen container name if overridden. Development and its Makefile
virtual-environment default remain unchanged.

## Reverse-proxy integration contract

The private infrastructure configuration controls the domain, network topology,
public path, TLS and routing. When mounting this application at a path prefix,
the trusted proxy must strip that prefix before forwarding requests and overwrite
`X-Forwarded-Prefix` with the public prefix. Forward the original protocol in
`X-Forwarded-Proto` as well. Enable `CONNECT4_BEHIND_PROXY=1` only behind that trusted
proxy. The deployment script enables it for the loopback-published container.

Flask generates the prefixed static and API URLs. Direct local development
ignores forwarded prefixes by default. Test asset loading, API replies, both
starting seats and reset through the proxy as part of your infrastructure checks.
