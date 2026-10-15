"""Exercise hash-based release packaging against isolated local Git repositories."""
from pathlib import Path
import importlib.util
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("release", ROOT / "release.py")
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class ReleasePackaging(unittest.TestCase):
    def setUp(self):
        (ROOT / "dist").mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix="release-test-", dir=ROOT / "dist")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.git("init", "-q")
        self.write(".gitignore", "/dist/\n/ignored.txt\n")
        self.write("UFO.toc", "## Version: 12.1.5\nui.xml\n")
        self.write("ui.xml", '<Ui><Script file="main.lua"/></Ui>\n')
        self.write("main.lua", "return true\n")
        self.write("ui/ActiveBorder.tga", "fixture asset")
        self.write("tests/test_example.py", "excluded test")
        self.write("release.py", "excluded build script")
        self.commit()
        self.patcher = patch.object(release, "ROOT", self.root)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def git(self, *args):
        return subprocess.check_output(
            ["git", "-c", "user.name=Release Test", "-c", "user.email=test@example.invalid",
             "-c", "commit.gpgsign=false", *args], cwd=self.root, stderr=subprocess.PIPE,
            text=True).strip()

    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def commit(self):
        self.git("add", "-A")
        self.git("-c", "core.hooksPath=disabled-hooks", "commit", "-qm", "Fixture")

    def test_hash_names_zip_and_packaged_version_without_editing_source(self):
        source = (self.root / "UFO.toc").read_bytes()
        revision = self.git("rev-parse", "--short", "HEAD")
        self.write("ignored.txt", "not part of this commit")
        release.main()
        archive = self.root / "dist" / f"UFO-12.1.5-{revision}.zip"
        with ZipFile(archive) as zip_file:
            self.assertIsNone(zip_file.testzip())
            self.assertIn(f"## Version: 12.1.5-{revision}\n",
                          zip_file.read("UFO/UFO.toc").decode())
            self.assertIn("UFO/ui/ActiveBorder.tga", zip_file.namelist())
            self.assertNotIn("UFO/ignored.txt", zip_file.namelist())
            self.assertNotIn("UFO/release.py", zip_file.namelist())
            self.assertFalse(any(name.startswith("UFO/tests/") for name in zip_file.namelist()))
        self.assertEqual((self.root / "UFO.toc").read_bytes(), source)
        self.assertEqual(self.git("status", "--porcelain"), "")
        release.main()  # Rebuilding replaces this commit's ZIP.
        self.assertEqual(list((self.root / "dist").glob("*.zip")), [archive])

    def test_modified_tracked_file_cannot_be_released_under_old_hash(self):
        self.write("main.lua", "return false\n")
        with self.assertRaisesRegex(ValueError, "Commit or stash"):
            release.main()

    def test_untracked_file_cannot_silently_enter_release(self):
        self.write("new.lua", "return 1\n")
        with self.assertRaisesRegex(ValueError, "Commit or stash"):
            release.main()

    def test_missing_dependency_prevents_archive_creation(self):
        self.write("ui.xml", '<Ui><Script file="missing.lua"/></Ui>\n')
        self.commit()
        with self.assertRaises(FileNotFoundError):
            release.main()
        self.assertFalse((self.root / "dist").exists())


if __name__ == "__main__":
    unittest.main()
