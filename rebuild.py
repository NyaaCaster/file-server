#!/usr/bin/env python3
"""AVG file-server: build image → push to NyaaDockerHUB private registry.

Usage:
  python rebuild.py              # build + push + registry cleanup + local cleanup
  python rebuild.py --no-cache   # force full rebuild without Docker layer cache
  python rebuild.py --skip-push  # local build only (offline / debugging)

Reads registry config from the ROOT .env (shared across all three AVG services).
Git SHA is taken from the file-server submodule commit (not the parent repo).
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from urllib import request, error as urllib_error

PROJECT = "adv-file-server"
IMAGE = "adv-file-server"
COMPOSE_FILE = "docker-compose.yml"
RETRY_MAX = 3
RETRY_DELAY = 2  # seconds


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def load_env() -> dict[str, str]:
    """Load ROOT .env into a dict (simple parser, no dotenv dependency).

    Registry config is shared across all three AVG services via the root .env.
    """
    env = {}
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        print("[ERROR] Root .env not found. Cannot proceed without registry config.")
        sys.exit(1)
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            k, v = k.strip(), v.strip()
            if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                v = v[1:-1]
            env[k] = v
    return env


def mask(text: str, secrets: list[str]) -> str:
    """Replace every occurrence of each secret with <PRIVATE_REGISTRY>."""
    for s in secrets:
        if s:
            text = text.replace(s, "<PRIVATE_REGISTRY>")
    return text


def run(cmd: list[str], secrets: list[str], **kwargs) -> subprocess.CompletedProcess:
    """Run a command, printing masked output."""
    print(f"  -> {' '.join(mask(str(x), secrets) for x in cmd)}")
    return subprocess.run(cmd, **kwargs)


def get_git_sha(length: int = 7) -> str:
    """Get git SHA from the file-server submodule."""
    here = Path(__file__).resolve().parent
    cp = subprocess.run(
        ["git", "-C", str(here), "rev-parse", f"--short={length}", "HEAD"],
        capture_output=True, text=True,
    )
    if cp.returncode != 0:
        print("[ERROR] file-server submodule: not a git repository or no commits.")
        print("        Run: git submodule update --init")
        sys.exit(1)
    return cp.stdout.strip()


def registry_health(registry_url: str, secrets: list[str]) -> bool:
    """Check that the private registry is reachable."""
    try:
        req = request.Request(f"{registry_url}/v2/")
        with request.urlopen(req, timeout=5) as resp:
            print(f"Registry OK (status {resp.status})")
            return True
    except Exception as e:
        print(f"[WARN] Registry health check failed: {mask(str(e), secrets)}")
        return False


# ---------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------

def docker_build(host: str, sha: str, no_cache: bool, secrets: list[str]):
    """docker build with double tags (sha + latest)."""
    here = Path(__file__).resolve().parent
    tags = [f"{host}/{IMAGE}:{sha}", f"{host}/{IMAGE}:latest"]
    cmd = ["docker", "build", "-f", str(here / "Dockerfile")]
    if no_cache:
        cmd.append("--no-cache")
    for t in tags:
        cmd += ["-t", t]
    cmd.append(str(here))
    cp = run(cmd, secrets)
    if cp.returncode != 0:
        print("[ERROR] Docker build failed.")
        sys.exit(1)
    print("Build OK")


# ---------------------------------------------------------------------------
# push
# ---------------------------------------------------------------------------

def docker_push(host: str, tag: str, secrets: list[str]):
    """Push a single tag with retry on transient errors."""
    full = f"{host}/{IMAGE}:{tag}"
    for attempt in range(1, RETRY_MAX + 1):
        cp = run(["docker", "push", full], secrets)
        if cp.returncode == 0:
            print(f"Push OK  {tag}")
            return
        print(f"Push failed ({tag}, attempt {attempt}/{RETRY_MAX})")
        if attempt < RETRY_MAX:
            time.sleep(RETRY_DELAY)
    print(f"[ERROR] Push exhausted retries for {tag}")
    sys.exit(1)


# ---------------------------------------------------------------------------
# registry cleanup
# ---------------------------------------------------------------------------

def registry_cleanup(registry_url: str, host: str, sha: str, secrets: list[str]):
    """Delete all remote tags except the current SHA and 'latest'.

    ⚠️ 注册表只接受按 **digest** 删除（按 tag DELETE 返回 DIGEST_INVALID）。**内容完全相同**的重建
    会让新旧 tag 共用同一 manifest digest —— 直接按 digest 删除过期 tag 会连带删掉要保留的
    `latest`/当前 sha tag（2026-09-12 在 adv-tavern-db 上真实发生）。故删除前排除仍被保留 tag
    引用的 digest。
    """
    print("Registry cleanup (keep-only-latest)...")
    try:
        req = request.Request(f"{registry_url}/v2/{IMAGE}/tags/list")
        with request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        all_tags = data.get("tags") or []
    except Exception as e:
        print(f"[WARN] Cannot list registry tags: {mask(str(e), secrets)}")
        return

    keep = {sha, "latest"}

    def manifest_digest(tag: str) -> str:
        head_req = request.Request(
            f"{registry_url}/v2/{IMAGE}/manifests/{tag}",
            method="HEAD",
            headers={"Accept": "application/vnd.docker.distribution.manifest.v2+json"},
        )
        with request.urlopen(head_req, timeout=10) as resp:
            return resp.headers.get("Docker-Content-Digest", "") or ""

    # 内容相同的重建会让保留 tag 与过期 tag 指向同一 digest，先记下来
    protected: set[str] = set()
    for tag in sorted(keep & set(all_tags)):
        try:
            d = manifest_digest(tag)
            if d:
                protected.add(d)
        except Exception as e:
            print(f"  [WARN] cannot resolve digest of kept tag {tag}: {mask(str(e), secrets)}")

    obsolete = [t for t in all_tags if t not in keep]
    if not obsolete:
        print("  No obsolete remote tags.")
        return

    for tag in obsolete:
        try:
            digest = manifest_digest(tag)
            if not digest:
                print(f"  Skip {tag}: no digest")
                continue
            if digest in protected:
                print(f"  SKIP {tag}: shares manifest {digest[7:19]}... with a kept tag"
                      "(digest delete would wipe kept tags)")
                continue
            del_req = request.Request(
                f"{registry_url}/v2/{IMAGE}/manifests/{digest}",
                method="DELETE",
            )
            with request.urlopen(del_req, timeout=10) as resp:
                if resp.status in (200, 202):
                    print(f"  Deleted {tag}")
                else:
                    print(f"  Delete {tag} -> HTTP {resp.status}")
        except Exception as e:
            print(f"  Skip {tag}: {mask(str(e), secrets)}")


# ---------------------------------------------------------------------------
# local cleanup
# ---------------------------------------------------------------------------

def local_cleanup(host: str, sha: str, secrets: list[str]):
    """Remove local obsolete tags and dangling images for this project."""
    cp = subprocess.run(
        ["docker", "images", f"{host}/{IMAGE}", "--format", "{{.Tag}}"],
        capture_output=True, text=True,
    )
    if cp.returncode != 0:
        return
    keep = {sha, "latest"}
    for tag in cp.stdout.strip().splitlines():
        tag = tag.strip()
        if tag and tag not in keep:
            subprocess.run(["docker", "rmi", "-f", f"{host}/{IMAGE}:{tag}"],
                           capture_output=True)

    subprocess.run(
        ["docker", "image", "prune", "-f", "--filter", f"label=project={PROJECT}"],
        capture_output=True,
    )


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=f"Rebuild {PROJECT}")
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--skip-push", action="store_true")
    args = parser.parse_args()

    env = load_env()
    host = env.get("PRIVATE_DOCKER_REGISTRY_HOST", "")
    url = env.get("PRIVATE_DOCKER_REGISTRY_URL", "")
    if not host:
        print("[ERROR] PRIVATE_DOCKER_REGISTRY_HOST not set in root .env")
        sys.exit(1)
    if not url:
        url = f"http://{host}"

    secrets = [host, url]
    sha = get_git_sha()

    print(f"=== {PROJECT} rebuild ===")
    print(f"  SHA:       {sha}")
    print(f"  Registry:  <PRIVATE_REGISTRY>")
    print()

    # 1. registry health check
    if not args.skip_push:
        registry_health(url, secrets)

    # 2. build
    docker_build(host, sha, args.no_cache, secrets)

    if args.skip_push:
        print("--skip-push: done (local build only)")
        return

    # 3. push
    docker_push(host, sha, secrets)
    docker_push(host, "latest", secrets)

    # 4. registry keep-only-latest
    registry_cleanup(url, host, sha, secrets)

    # 5. local cleanup
    local_cleanup(host, sha, secrets)

    print(f"\n=== {PROJECT} rebuild done ===")
    print(f"Image: <PRIVATE_REGISTRY>/{IMAGE}:{sha}")
    print(f"       <PRIVATE_REGISTRY>/{IMAGE}:latest")


if __name__ == "__main__":
    main()
