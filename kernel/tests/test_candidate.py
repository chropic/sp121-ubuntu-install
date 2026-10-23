# SPDX-License-Identifier: GPL-2.0-or-later
"""Safety checks for ordered candidate preparation; no kernel build required."""

from contextlib import redirect_stdout
import hashlib
from importlib.util import module_from_spec, spec_from_file_location
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

spec = spec_from_file_location("candidate", Path(__file__).resolve().parents[1] / "prepare-candidate.py")
candidate = module_from_spec(spec)
spec.loader.exec_module(candidate)
build_spec = spec_from_file_location("build_candidate", Path(__file__).resolve().parents[1] / "build-candidate.py")
build_candidate = module_from_spec(build_spec)
build_spec.loader.exec_module(build_candidate)


class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        self.source.mkdir()
        self.run_git("init")
        self.run_git("config", "core.autocrlf", "false")
        (self.source / "board.dts").write_bytes(b"gpio = <8>;\n")
        self.run_git("add", "board.dts")
        self.run_git("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "fixture")
        self.patch = self.root / "volume.patch"
        self.patch.write_bytes(b"--- a/board.dts\n+++ b/board.dts\n@@ -1 +1 @@\n-gpio = <8>;\n+gpio = <6>;\n")
        self.seed = self.root / "config"
        self.seed.write_bytes(b"CONFIG_ARM64=y\n")
        self.manifest = {"base_commit": self.run_git("rev-parse", "HEAD"),
                         "config_seed": self.input(self.seed), "series": [self.input(self.patch)]}

    def run_git(self, *args):
        return candidate.git(self.source, *args)

    def input(self, path):
        return {"path": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

    def prepare(self, apply=False):
        with redirect_stdout(io.StringIO()):
            candidate.prepare(self.source, self.manifest, self.root, apply)

    def test_dry_run_preserves_tree_and_real_index(self):
        before = self.run_git("write-tree")
        self.prepare()
        self.assertEqual(before, self.run_git("write-tree"))
        self.assertEqual("", self.run_git("status", "--porcelain"))
        self.assertFalse((self.source / ".config").exists())

    def test_apply_and_refuse_reapplication(self):
        self.prepare(apply=True)
        self.assertEqual(b"gpio = <6>;\n", (self.source / "board.dts").read_bytes())
        self.assertEqual(self.seed.read_bytes(), (self.source / ".config").read_bytes())
        with self.assertRaises(ValueError):
            self.prepare(apply=True)

    def test_wrong_base_and_dirty_tree(self):
        self.manifest["base_commit"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "Wrong base"):
            self.prepare()
        self.manifest["base_commit"] = self.run_git("rev-parse", "HEAD")
        (self.source / "untracked").write_text("user work")
        with self.assertRaisesRegex(ValueError, "not clean"):
            self.prepare()

    def test_hash_mismatch(self):
        self.patch.write_bytes(self.patch.read_bytes() + b"\n")
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            self.prepare(apply=True)
        self.assertEqual("", self.run_git("status", "--porcelain"))

    def test_ignored_config_is_protected(self):
        self.run_git("config", "core.excludesFile", str(self.root / "ignore"))
        (self.root / "ignore").write_text(".config\n")
        (self.source / ".config").write_text("existing configuration")
        with self.assertRaisesRegex(ValueError, "Existing .config"):
            self.prepare(apply=True)

    def test_late_series_failure_does_not_apply_earlier_patch(self):
        self.manifest["series"].append(self.input(self.patch))
        with self.assertRaises(subprocess.CalledProcessError):
            self.prepare(apply=True)
        self.assertEqual("", self.run_git("status", "--porcelain"))
        self.assertFalse((self.source / ".config").exists())

    def test_linked_worktree(self):
        worktree = self.root / "linked"
        self.run_git("worktree", "add", "--detach", str(worktree), "HEAD")
        self.source = worktree
        self.prepare(apply=True)
        self.assertEqual(b"gpio = <6>;\n", (worktree / "board.dts").read_bytes())

    def test_out_of_tree_config_and_read_only_preflight(self):
        output = self.root / "output"
        with redirect_stdout(io.StringIO()):
            candidate.prepare(self.source, self.manifest, self.root, output=output)
        self.assertFalse(output.exists())
        with redirect_stdout(io.StringIO()):
            candidate.prepare(self.source, self.manifest, self.root, apply=True, output=output)
        self.assertEqual(self.seed.read_bytes(), (output / ".config").read_bytes())
        self.assertFalse((self.source / ".config").exists())

    def test_profile_selects_extra_series_and_config(self):
        self.manifest["profiles"] = {
            "platform": {"config": self.input(self.seed)},
            "camera": {"config": self.input(self.seed), "extra_series": [self.input(self.patch)]},
        }
        entries, config = candidate.selected_inputs(self.manifest, "camera")
        self.assertEqual(2, len(entries))
        self.assertEqual(self.input(self.seed), config)

    def test_build_verification_protects_source_config_and_index(self):
        output = self.root / "output"
        with redirect_stdout(io.StringIO()):
            candidate.prepare(self.source, self.manifest, self.root, apply=True, output=output)
        before = self.run_git("write-tree")
        build_candidate.verify(self.source, output, self.manifest, "platform", self.root)
        self.assertEqual(before, self.run_git("write-tree"))
        (self.source / "board.dts").write_text("user source change\n")
        with self.assertRaisesRegex(ValueError, "Source does not match"):
            build_candidate.verify(self.source, output, self.manifest, "platform", self.root)
        (output / ".config").write_text("user config change\n")
        with self.assertRaisesRegex(ValueError, "Build config differs"):
            build_candidate.verify(self.source, output, self.manifest, "platform", self.root)
        self.assertEqual(before, self.run_git("write-tree"))


class ManifestTests(unittest.TestCase):
    def test_all_pinned_repository_inputs(self):
        manifest = json.loads(candidate.MANIFEST.read_text())
        inputs = [manifest["config_seed"], *manifest["series"],
                  *manifest["research_inputs"], *manifest["vendor_dispositions"]]
        for profile in manifest.get("profiles", {}).values():
            inputs.extend([profile["config"], *profile.get("extra_series", [])])
        for item in inputs:
            with self.subTest(path=item["path"]):
                candidate.checked_input(candidate.ROOT, item)
        actual = {p.relative_to(candidate.ROOT).as_posix()
                  for p in (candidate.ROOT / "kernel/patches/vendor/mias").rglob("*.patch")}
        self.assertEqual(actual, {p["path"] for p in manifest["vendor_dispositions"]})


if __name__ == "__main__":
    unittest.main()
