#!/usr/bin/env bash
# SessionStart hook: prepares a Claude Code on the web session (commit
# signing, the Python tools, the help pages indexed). Does nothing on a
# developer's own machine.
set -uo pipefail
[ -n "${CLAUDE_CODE_REMOTE:-}" ] || exit 0
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0

log() { echo "cloud-session-start: $*" >&2; }

# Signs commits with the SSH key in GIT_SIGNING_KEY_B64 (registered on GitHub
# as a signing key), so every commit shows as verified. The key lives outside
# the repository, never in it.
if [ -n "${GIT_SIGNING_KEY_B64:-}" ]; then
    key="$HOME/.ssh/cloud_signing"
    mkdir -p "$HOME/.ssh" && chmod 700 "$HOME/.ssh"
    (umask 077; printf '%s' "$GIT_SIGNING_KEY_B64" | base64 -d >"$key") && chmod 600 "$key"
    git config --local user.name Enriquez-Johnmark
    git config --local user.email enriquezjohnmark15@gmail.com
    git config --local gpg.format ssh
    git config --local gpg.ssh.program ssh-keygen
    git config --local user.signingkey "$key"
    git config --local commit.gpgsign true
fi

# The cloud proxy's certificate is in the system store, which uv reads with this.
export UV_SYSTEM_CERTS=1
unset UV_NATIVE_TLS
command -v uv >/dev/null || pip install -q uv >/dev/null 2>&1 || log "installing uv failed"
uv sync -q || log "uv sync failed; the checks will not run"
uv run -q help-assistant index >/dev/null || log "indexing the help pages failed"
exit 0
