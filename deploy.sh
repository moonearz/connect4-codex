#!/usr/bin/env bash
# Run on the web server after cloning this repository. No proxy files are changed.
set -euo pipefail
cd "$(dirname "$0")"

CONTAINER_NAME=${CONTAINER_NAME:-connect4}
HOST_PORT=${HOST_PORT:?Set HOST_PORT explicitly from private deployment configuration}
IMAGE=${IMAGE:-connect4:latest}
if [[ ! "$HOST_PORT" =~ ^[0-9]{1,5}$ ]]; then
    echo "HOST_PORT must be numeric (1024–65535)." >&2
    exit 1
fi
HOST_PORT=$((10#$HOST_PORT))
if (( HOST_PORT < 1024 || HOST_PORT > 65535 )); then
    echo "HOST_PORT must be an unprivileged port between 1024 and 65535." >&2
    exit 1
fi
if [[ ! "$CONTAINER_NAME" =~ ^[a-zA-Z0-9][a-zA-Z0-9_.-]*$ ]]; then
    echo "Invalid CONTAINER_NAME." >&2
    exit 1
fi
for tool in git docker curl; do command -v "$tool" >/dev/null; done
docker info >/dev/null
if [[ ${SKIP_PULL:-0} != 1 ]]; then
    if ! git diff --quiet || ! git diff --cached --quiet; then
        echo "Commit or stash local changes before deploying." >&2
        exit 1
    fi
    git pull --ff-only
fi

candidate="${CONTAINER_NAME}-check-$$"
backup="${CONTAINER_NAME}-backup-$$"
old_saved=0
old_address=""
new_attempted=0
committed=0
cleanup() {
    status=$?
    trap - EXIT
    docker rm -f "$candidate" >/dev/null 2>&1 || true
    if (( ! committed )); then
        if (( new_attempted )); then docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true; fi
        if (( old_saved )); then
            echo "Restoring previous container..." >&2
            if docker rename "$backup" "$CONTAINER_NAME" && docker start "$CONTAINER_NAME"; then
                if [[ -n "$old_address" ]]; then
                    wait_for_app "http://$old_address" || echo "Restored container did not become healthy." >&2
                fi
            else
                echo "Restore could not complete; inspect $CONTAINER_NAME and $backup." >&2
            fi
        fi
    fi
    exit "$status"
}
trap cleanup EXIT

wait_for_app() {
    local address=$1
    for (( attempt=0; attempt<30; attempt++ )); do
        if curl --fail --silent --max-time 2 "$address/healthz" >/dev/null; then return 0; fi
        sleep 1
    done
    return 1
}

echo "Building $IMAGE..."
docker build -t "$IMAGE" .
# Verify the new image before stopping the running application.
docker run -d --name "$candidate" -p 127.0.0.1::8000 \
    -e CONNECT4_BEHIND_PROXY=1 "$IMAGE" >/dev/null
candidate_address="http://$(docker port "$candidate" 8000/tcp)"
wait_for_app "$candidate_address"
curl --fail --silent --show-error --max-time 15 \
    -H 'Content-Type: application/json' \
    --data '{"mode":"computer","difficulty":"learned","human_player":1}' \
    "$candidate_address/api/game" >/dev/null

if docker container inspect "$CONTAINER_NAME" >/dev/null 2>&1; then
    old_address=$(docker port "$CONTAINER_NAME" 8000/tcp | head -n 1)
    docker stop "$CONTAINER_NAME" >/dev/null
    if ! docker rename "$CONTAINER_NAME" "$backup"; then
        docker start "$CONTAINER_NAME" >/dev/null
        exit 1
    fi
    old_saved=1
fi
new_attempted=1
docker run -d --name "$CONTAINER_NAME" --restart unless-stopped \
    -p "127.0.0.1:${HOST_PORT}:8000" -e CONNECT4_BEHIND_PROXY=1 "$IMAGE" >/dev/null
wait_for_app "http://127.0.0.1:$HOST_PORT"
committed=1
if (( old_saved )); then
    docker rm "$backup" >/dev/null || echo "Old backup retained as $backup." >&2
fi
echo "Connect Four is running on 127.0.0.1:$HOST_PORT (container port 8000)."
echo "Configure the reverse proxy separately in your infrastructure repository."
