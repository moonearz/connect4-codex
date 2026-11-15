"""Download and build the optional, evaluation-only Pascal Pons solver.

Upstream source is AGPL-3.0-or-later. Its original notices and license remain in
an ignored cache; neither upstream source nor binaries are vendored in our app.
"""

import argparse
import hashlib
import io
import json
import shutil
import subprocess
import tarfile
import urllib.request
from pathlib import Path

REVISION = "d6ba50d8aaf2308c769d9bf2abd42d90f34baf41"
REPOSITORY = "https://github.com/PascalPons/connect4"
ARCHIVE_URL = f"https://codeload.github.com/PascalPons/connect4/tar.gz/{REVISION}"
ARCHIVE_SHA256 = "48372f74853cdb130b37b1e850a37046ac443da1d311ac7c2a89bb2aca74781e"
ROOT = Path(__file__).resolve().parents[1]


def setup(destination, compiler="g++"):
    destination = Path(destination).resolve()
    executable = shutil.which(compiler)
    if executable is None:
        raise RuntimeError(f"C++ compiler {compiler!r} not found; install g++ first.")
    destination.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(ARCHIVE_URL, timeout=30) as response:
        archive = response.read(2_000_001)
    if len(archive) > 2_000_000:
        raise RuntimeError("Unexpectedly large solver source archive.")
    if hashlib.sha256(archive).hexdigest() != ARCHIVE_SHA256:
        raise RuntimeError("Source archive checksum does not match pinned revision.")
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as bundle:
        if sum(member.size for member in bundle.getmembers()) > 5_000_000:
            raise RuntimeError("Unexpectedly large unpacked solver source.")
        bundle.extractall(destination, filter="data")
    source = destination / f"connect4-{REVISION}"
    binary = destination / "c4solver"
    flags = ["-std=c++11", "-O3", "-DNDEBUG"]
    command = [
        executable,
        *flags,
        str(source / "main.cpp"),
        str(source / "Solver.cpp"),
        "-o",
        str(binary),
    ]
    subprocess.run(command, check=True, timeout=120)
    manifest = dict(
        repository=REPOSITORY,
        revision=REVISION,
        license="AGPL-3.0-or-later",
        opening_book=None,
        archive_sha256=hashlib.sha256(archive).hexdigest(),
        compiler=subprocess.check_output(
            [executable, "--version"], text=True
        ).splitlines()[0],
        compile_flags=flags,
        binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
        source_sha256={
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(source.iterdir())
            if p.is_file()
        },
    )
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return binary, manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, default=ROOT / ".solver")
    parser.add_argument("--compiler", default="g++")
    args = parser.parse_args()
    binary, manifest = setup(args.destination, args.compiler)
    print(f"Built {binary}\nUpstream revision: {manifest['revision']}")
    print("AGPL source and license retained in the cache; no opening book downloaded.")


if __name__ == "__main__":
    main()
