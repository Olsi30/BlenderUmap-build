"""Build the pinned, experimental BlenderUmap add-on. Python 3.10+."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parent
WORK = ROOT / ".work"
SOURCE = WORK / "source"
LOCK = json.loads((ROOT / "source-lock.json").read_text(encoding="utf-8"))


def run(*args, cwd=None):
    subprocess.run(args, cwd=cwd, check=True)


def prepare():
    if SOURCE.exists():
        raise SystemExit(".work/source already exists. Use --reuse-sources only for a prepared, patched working tree, or remove .work before a clean build.")
    for item in LOCK["sources"]:
        if not re.fullmatch(r"[a-f0-9]{40}", item["commit"]):
            raise ValueError("Source must be pinned to a full commit SHA")
        target = WORK / item["directory"]
        target.mkdir(parents=True, exist_ok=True)
        run("git", "init", str(target))
        run("git", "remote", "add", "origin", item["url"], cwd=target)
        run("git", "fetch", "--depth", "1", "origin", item["commit"], cwd=target)
        run("git", "checkout", "--detach", "FETCH_HEAD", cwd=target)
        actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=target, text=True).strip()
        if actual != item["commit"]:
            raise RuntimeError("Source revision mismatch")
    patch = str(ROOT / "patches" / "modernize.patch")
    run("git", "apply", "--check", patch, cwd=SOURCE)
    run("git", "apply", patch, cwd=SOURCE)


def package(published, rid):
    output = ROOT / "release" / f"BlenderUmap-{LOCK['version']}-{rid}.zip"
    output.parent.mkdir(exist_ok=True)
    files = {}
    for base in (published, SOURCE / "Importers" / "Blender"):
        for path in sorted(base.rglob("*")):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            if base.name == "Blender" and path.suffix != ".py":
                continue
            rel = path.relative_to(base).as_posix()
            if rel in files:
                raise RuntimeError(f"Duplicate ZIP member: {rel}")
            files[rel] = path.read_bytes()
    files["__version__.py"] = b"__version__ = '0.1.0-experimental'\nbranch = 'modern-replay-build'\n"
    files["BUILD-INFO.json"] = json.dumps({**LOCK, "rid": rid, "status": "experimental; Fortnite 42.20 and full map reconstruction unverified"}, indent=2).encode()
    files["README-DE.md"] = (ROOT / "README.md").read_bytes()
    for path in sorted((SOURCE / "CUE4Parse").glob("LICENSE*")):
        if path.is_file():
            files["licenses/CUE4Parse-" + path.name] = path.read_bytes()
    files["licenses/FortniteReplayDecompressor-LICENSE"] = (SOURCE / "FortniteReplayDecompressor" / "LICENSE").read_bytes()
    for path in sorted(ROOT.glob("LICENSE*")):
        files["licenses/" + path.name] = path.read_bytes()
    files["build-source/patches/modernize.patch"] = (ROOT / "patches/modernize.patch").read_bytes()
    for name in ("build.py", "source-lock.json", "README.md"):
        files["build-source/" + name] = (ROOT / name).read_bytes()
    required = {"__init__.py", "main.py", "BlenderUmap.dll", "BlenderUmap.deps.json", "BlenderUmap.runtimeconfig.json"}
    required.add("BlenderUmap.exe" if rid.startswith("win-") else "BlenderUmap")
    if required - files.keys():
        raise RuntimeError(f"Incomplete build: {required - files.keys()}")
    for name, data in files.items():
        if name.endswith(".py"):
            ast.parse(data.decode("utf-8-sig"), filename=name)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo("BlenderUmap/" + name, date_time=(2026, 9, 24, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o755 if name == "BlenderUmap" else 0o644) << 16
            archive.writestr(info, data)
    with zipfile.ZipFile(output) as archive:
        if archive.testzip() is not None:
            raise RuntimeError("ZIP integrity check failed")
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix(".zip.sha256").write_text(f"{digest}  {output.name}\n", encoding="utf-8")
    print(f"Created {output} ({output.stat().st_size:,} bytes)\nSHA256 {digest}")
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rid", choices=("win-x64", "linux-x64"), default="win-x64")
    parser.add_argument("--reuse-sources", action="store_true")
    args = parser.parse_args()
    if not args.reuse_sources:
        prepare()
    publish = WORK / "publish" / args.rid
    if publish.exists():
        shutil.rmtree(publish)
    os.environ.setdefault("DOTNET_CLI_TELEMETRY_OPTOUT", "1")
    # Maps use managed decompression; the optional native ACL library is for animations.
    run("dotnet", "publish", str(SOURCE / "BlenderUmap/BlenderUmap.csproj"),
        "-c", "Release", "-r", args.rid, "--self-contained", "true", "-o", str(publish),
        "-m:1", "-p:BuildInParallel=false", "-p:CUE4PARSE_SKIP_NATIVE=true",
        "-p:DebugType=None", "-p:DebugSymbols=false", "-p:PublishTrimmed=false", "-p:NuGetAudit=false")
    if (args.rid.startswith("win-") and os.name == "nt") or (args.rid.startswith("linux-") and os.name != "nt"):
        executable = publish / ("BlenderUmap.exe" if os.name == "nt" else "BlenderUmap")
        run(str(executable), "--help")
        invalid = WORK / "invalid.replay"
        invalid.write_bytes(b"invalid-replay-test")
        check = subprocess.run([str(executable), "--replay-info", str(invalid)], capture_output=True, text=True, timeout=15)
        if check.returncode != 1:
            raise RuntimeError("Invalid replay smoke test failed")
    package(publish, args.rid)


if __name__ == "__main__":
    main()

