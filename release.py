"""Build dist/UFO-<TOC version>-<short Git hash>.zip with the standard library."""
from pathlib import Path
import re
import subprocess
from tempfile import NamedTemporaryFile
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parent


def git(*args):
    result = subprocess.run(["git", *args], cwd=ROOT, check=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.stdout.decode("utf-8")


def verify(path, visited):
    if not path.is_file():
        raise FileNotFoundError(f"Missing addon dependency: {path}")
    if path in visited:
        return
    visited.add(path)
    if path.suffix.lower() == ".toc":
        children = [line.strip() for line in path.read_text(encoding="utf-8-sig").splitlines()
                    if line.strip() and not line.lstrip().startswith("#")]
    elif path.suffix.lower() == ".xml":
        xml = re.sub(r'<!--.*?-->', '', path.read_text(encoding="utf-8-sig"), flags=re.S)
        children = re.findall(r'<(?:Script|Include)\s+file="([^"]+)"', xml)
    else:
        return
    for child in children:
        verify(path.parent / child.replace("\\", "/"), visited)


def main():
    if git("status", "--porcelain", "--untracked-files=normal", "--ignore-submodules=none").strip():
        raise ValueError("Commit or stash working changes before making a hash-identified release")
    revision = git("rev-parse", "--short", "HEAD").strip()
    if not re.fullmatch(r'[0-9a-f]{4,64}', revision):
        raise ValueError("Git did not return a valid short commit hash")
    toc = ROOT / "UFO.toc"
    source = toc.read_text(encoding="utf-8-sig")
    match = re.search(r'^## Version:[ \t]*(\S+)[ \t]*$', source, re.M)
    if not match or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', match[1]):
        raise ValueError("UFO.toc must contain a filename-safe ## Version value")
    version = f"{match[1]}-{revision}"
    packaged_toc = source[:match.start(1)] + version + source[match.end(1):]

    visited = set()
    verify(toc, visited)
    files = []
    # Include committed files, including initialized submodule contents, rather
    # than unrelated ignored files which happen to exist in the checkout.
    for name in sorted(git("ls-files", "--recurse-submodules", "-z").split("\0")):
        if not name:
            continue
        rel = Path(name)
        path = ROOT / rel
        if not path.is_file() or any(part.startswith(".") for part in rel.parts):
            continue
        if rel.parts[0] in {"tests", "dist", "__pycache__"}:
            continue
        if path.name in {"release.py", "pkgmeta.yaml"} or path.suffix.lower() in {".zip", ".pyc"}:
            continue
        files.append(path)
    missing = visited.difference(files)
    if missing:
        raise ValueError(f"Required dependencies excluded from package: {missing}")

    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    destination = dist / f"UFO-{version}.zip"
    # Validate a temporary archive before replacing an existing release.
    with NamedTemporaryFile(dir=dist, suffix=".zip", delete=False) as handle:
        temporary = Path(handle.name)
    try:
        with ZipFile(temporary, "w", ZIP_DEFLATED) as archive:
            for path in files:
                name = "UFO/" + path.relative_to(ROOT).as_posix()
                if path == toc:
                    archive.writestr(name, packaged_toc.encode("utf-8"))
                else:
                    archive.write(path, name)
        with ZipFile(temporary) as archive:
            corrupt = archive.testzip()
            if corrupt:
                raise ValueError(f"Corrupt archive member: {corrupt}")
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Verified {len(visited)} TOC/XML dependencies; packaged {len(files)} files.")
    print(f"Created {destination} ({destination.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
