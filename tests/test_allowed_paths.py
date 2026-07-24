from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from nightwatch.errors import ValidationError
from nightwatch.models import resolve_allowed_path


class AllowedPathTests(unittest.TestCase):
    def test_resolves_inside_run_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = resolve_allowed_path(root, "workspace/app/result.md", ("workspace/app",))
            self.assertEqual(target, root.resolve() / "workspace" / "app" / "result.md")

    def test_rejects_similar_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValidationError, "outside"):
                resolve_allowed_path(
                    Path(temporary),
                    "workspace/application/result.md",
                    ("workspace/app",),
                )

    def test_rejects_existing_symlink_escape_when_supported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary, tempfile.TemporaryDirectory() as outside:
            root = Path(temporary)
            link = root / "workspace" / "app"
            link.parent.mkdir(parents=True)
            junction = False
            try:
                link.symlink_to(Path(outside), target_is_directory=True)
            except OSError:
                if os.name != "nt":
                    self.skipTest("directory symlinks are unavailable")
                try:
                    result = subprocess.run(
                        ["cmd", "/c", "mklink", "/J", str(link), str(Path(outside))],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=False,
                    )
                except OSError:
                    self.skipTest("directory symlinks and junctions are unavailable")
                if result.returncode != 0:
                    self.skipTest("directory symlinks and junctions are unavailable")
                junction = True
            try:
                with self.assertRaisesRegex(ValidationError, "escapes"):
                    resolve_allowed_path(root, "workspace/app/result.md", ("workspace/app",))
            finally:
                if junction and link.exists():
                    os.rmdir(link)


if __name__ == "__main__":
    unittest.main()
