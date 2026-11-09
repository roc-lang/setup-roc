"""Execute the action's exact download shell with local release fixtures."""

import copy
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import unittest
import zipfile


ACTION = Path(__file__).resolve().parents[1] / "action.yml"
TAG = "nightly-2099-01-02-deadbee"
PLATFORMS = [
    ("Linux", "x86_64", "linux_x86_64", "tar.gz"),
    ("Linux", "aarch64", "linux_arm64", "tar.gz"),
    ("Darwin", "x86_64", "macos_x86_64", "tar.gz"),
    ("Darwin", "arm64", "macos_apple_silicon", "tar.gz"),
    ("MINGW64_NT-10.0", "x86_64", "windows_x86_64", "zip"),
]


def download_shell():
    lines = ACTION.read_text().splitlines()
    start = lines.index("      run: |") + 1
    end = next(index for index in range(start, len(lines))
               if lines[index] and not lines[index].startswith("        "))
    return "\n".join(line[8:] if line else "" for line in lines[start:end]) + "\n"


class DownloadTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()
        self.runtime = self.root / "runtime"
        self.runtime.mkdir()
        self.calls = self.root / "calls.jsonl"
        self.meta_path = self.root / "release.json"
        self.body_path = self.root / "body"
        self.platform = PLATFORMS[0]
        self.fail = ""
        self.metadata_body = None
        self.set_release()
        self.tool("uname", """#!/usr/bin/env python3
import os,sys
print(os.environ["FAKE_OS"] if sys.argv[1]=="-s" else os.environ["FAKE_ARCH"])
""")
        self.tool("curl", """#!/usr/bin/env python3
import json,os,pathlib,sys
args=sys.argv[1:];url=args[-1]
metadata="/releases/assets/" not in url and "/releases/download/" not in url
credentials=[key for key,value in os.environ.items() if value and (key in ("TOKEN","ROC_SETUP_TOKEN") or key.startswith(("GH_","GITHUB_")))]
safe_args=["[authorization]" if value.startswith("Authorization:") else value for value in args]
with open(os.environ["FAKE_CALLS"],"a") as f:f.write(json.dumps({"args":safe_args,"metadata":metadata,"credentials":credentials})+"\\n")
if os.environ.get("FAKE_FAIL")==("metadata" if metadata else "asset"):
 sys.stderr.write("curl: (22) The requested URL returned error: 504\\n");sys.exit(22)
data=pathlib.Path(os.environ["FAKE_METADATA"] if metadata else os.environ["FAKE_BODY"]).read_bytes()
option="--output" if "--output" in args else "-o" if "-o" in args else None
if option:pathlib.Path(args[args.index(option)+1]).write_bytes(data)
else:sys.stdout.buffer.write(data)
""")

    def tool(self, name, content):
        path = self.bin / name
        path.write_text(content)
        path.chmod(0o755)

    def archive(self, root_name=None, symlink_executable=False):
        _, _, platform, extension = self.platform
        root_name = root_name or f"roc_nightly-{platform}-2099-01-02-deadbee"
        files = {
            ("roc.exe" if extension == "zip" else "roc"): b"compiler fixture",
            "glue/RustGlue.roc": b"rust fixture",
            "glue/ZigGlue.roc": b"zig fixture",
            "glue/CGlue.roc": b"c fixture",
            "glue/env": b"ROC_GLUE_PLATFORM_URL=https://example.invalid/glue\nROC_GLUE_PLATFORM_PACKAGE=fixed\nUNRELATED=value\n",
        }
        data = io.BytesIO()
        if extension == "zip":
            with zipfile.ZipFile(data, "w") as stream:
                for name, body in files.items():
                    stream.writestr(root_name + "/" + name, body)
        else:
            with tarfile.open(fileobj=data, mode="w:gz") as stream:
                for name, body in files.items():
                    entry = tarfile.TarInfo(root_name + "/" + name)
                    entry.size = len(body)
                    entry.mode = 0o755 if name == "roc" else 0o644
                    if symlink_executable and name == "roc":
                        entry.type = tarfile.SYMTYPE
                        entry.linkname = "../other/roc"
                        entry.size = 0
                    stream.addfile(entry, io.BytesIO(body) if entry.isreg() else None)
        return data.getvalue()

    def set_release(self, body=None):
        _, _, platform, extension = self.platform
        name = f"roc_nightly-{platform}-2099-01-02-deadbee.{extension}"
        self.expected_directory = name[:-(len(extension) + 1)]
        body = self.archive() if body is None else body
        self.body_path.write_bytes(body)
        self.metadata = {
            "id": 123, "tag_name": TAG, "draft": False, "immutable": True,
            "assets": [{"id": 456, "name": name, "size": len(body),
                        "digest": "sha256:" + hashlib.sha256(body).hexdigest(),
                        "url": "https://api.github.com/repos/roc-lang/nightlies/releases/assets/456",
                        "browser_download_url": f"https://github.com/roc-lang/nightlies/releases/download/{TAG}/{name}"}],
        }

    def run_action(self, *, version="nightly", tag=TAG, method="asset-api", extra_environment=None):
        self.meta_path.write_bytes(self.metadata_body if self.metadata_body is not None
                                   else json.dumps(self.metadata).encode())
        environment = {
            **os.environ, "PATH": str(self.bin) + os.pathsep + os.environ["PATH"],
            "ROC_SETUP_VERSION": version, "ROC_SETUP_NIGHTLY_TAG": tag,
            "ROC_SETUP_TOKEN": "fixture-private-token", "ROC_SETUP_DOWNLOAD_METHOD": method,
            "GH_TOKEN": "fixture-private-token", "GITHUB_TOKEN": "fixture-private-token",
            "GH_ENTERPRISE_TOKEN": "fixture-private-token", "GITHUB_ENTERPRISE_TOKEN": "fixture-private-token",
            "GH_DEBUG": "api", "GITHUB_WORKSPACE": str(self.workspace),
            "GH_APP_TOKEN": "fixture-private-token",
            "GITHUB_PATH": str(self.root / "github-path"), "GITHUB_ENV": str(self.root / "github-env"),
            "RUNNER_TEMP": str(self.runtime), "FAKE_OS": self.platform[0], "FAKE_ARCH": self.platform[1],
            "FAKE_CALLS": str(self.calls), "FAKE_METADATA": str(self.meta_path),
            "FAKE_BODY": str(self.body_path), "FAKE_FAIL": self.fail,
        }
        if extra_environment:
            environment.update(extra_environment)
        result = subprocess.run(["bash", "-c", download_shell()], cwd=self.workspace,
                                env=environment, text=True, capture_output=True, timeout=15)
        self.assertNotIn("fixture-private-token", result.stdout + result.stderr)
        return result

    def assert_refused(self, **arguments):
        result = self.run_action(**arguments)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse((self.root / "github-path").exists())
        self.assertFalse((self.root / "github-env").exists())
        self.assertFalse(list(self.runtime.glob("setup-roc-api.*")))
        return result

    def recorded_calls(self):
        return [json.loads(line) for line in self.calls.read_text().splitlines()] if self.calls.exists() else []

    def test_api_install_glue_and_token_free_bounded_asset_download(self):
        result = self.run_action()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        installed = (self.root / "github-path").read_text().strip()
        self.assertEqual(installed, str(self.workspace) + "/./" + self.expected_directory)
        exports = (self.root / "github-env").read_text()
        for name in ("ROC_GLUE_DIR", "ROC_RUST_GLUE", "ROC_ZIG_GLUE", "ROC_C_GLUE",
                     "ROC_GLUE_PLATFORM_URL", "ROC_GLUE_PLATFORM_PACKAGE"):
            self.assertIn(name + "=", exports)
        self.assertNotIn("UNRELATED=", exports)
        calls = self.recorded_calls()
        self.assertEqual(len(calls), 2)
        asset = calls[1]
        self.assertEqual(asset["args"][0], "--disable")
        self.assertEqual(asset["args"][-1], "https://api.github.com/repos/roc-lang/nightlies/releases/assets/456")
        self.assertEqual(asset["credentials"], [])
        self.assertNotIn("[authorization]", asset["args"])
        self.assertIn("Accept: application/octet-stream", asset["args"])
        for option, value in (("--max-time", "60"), ("--max-redirs", "3"),
                              ("--max-filesize", str(self.metadata["assets"][0]["size"]))):
            self.assertEqual(asset["args"][asset["args"].index(option) + 1], value)
        self.assertFalse((self.workspace / "roc.tar.gz").exists())
        self.assertFalse(list(self.runtime.iterdir()))

    def test_latest_and_explicit_tag_have_same_asset_route(self):
        result = self.run_action(tag="")
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = self.recorded_calls()
        self.assertTrue(calls[0]["args"][-1].endswith("/releases/latest"))
        self.assertTrue(calls[1]["args"][-1].endswith("/releases/assets/456"))

    def test_historical_alias_uses_new_nightlies(self):
        result = self.run_action(version="nightly-new-compiler")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("repos/roc-lang/nightlies/releases/tags/", self.recorded_calls()[0]["args"][-1])

    def test_browser_default_route_and_unverified_metadata_behavior_stay_compatible(self):
        self.metadata.pop("immutable")
        self.metadata["assets"][0].pop("digest")
        result = self.run_action(method="browser")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.recorded_calls()[1]["args"][-1], self.metadata["assets"][0]["browser_download_url"])

    def test_all_five_platform_selections(self):
        for platform in PLATFORMS:
            with self.subTest(platform=platform):
                self.platform = platform
                self.set_release()
                result = self.run_action()
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertTrue((self.workspace / self.expected_directory).is_dir())
                shutil.rmtree(self.workspace / self.expected_directory)

    def test_bad_method_tag_or_version_cannot_execute_shell_or_download(self):
        for arguments in ({"method": 'asset-api"; touch injected; #'},
                          {"tag": 'nightly-1"; touch injected; #'},
                          {"tag": "nightly-$(touch injected)"},
                          {"tag": "nightly-" + "x" * 129},
                          {"version": 'nightly"; touch injected; #'}):
            with self.subTest(arguments=arguments):
                self.assert_refused(**arguments)
                self.assertEqual(self.recorded_calls(), [])
                self.assertFalse((self.workspace / "injected").exists())

    def test_mutable_draft_mismatched_or_malformed_release_rejected(self):
        original = copy.deepcopy(self.metadata)
        for change in ({"immutable": False}, {"draft": True}, {"tag_name": "nightly-other"},
                       {"tag_name": "nightly-../bad"}, {"id": 0}, {"id": 1.5}, {"tag_name": None}):
            with self.subTest(change=change):
                self.metadata = {**copy.deepcopy(original), **change}
                self.assert_refused()
                self.assertTrue(all(call["metadata"] for call in self.recorded_calls()))

    def test_missing_or_duplicate_asset_rejected(self):
        original = copy.deepcopy(self.metadata["assets"])
        for assets in ([], original + original):
            with self.subTest(count=len(assets)):
                self.metadata["assets"] = assets
                self.assert_refused()

    def test_wrong_asset_identity_size_or_digest_metadata_rejected(self):
        original = copy.deepcopy(self.metadata["assets"][0])
        changes = [
            {"id": 0}, {"id": 1.5}, {"size": 0}, {"size": -1}, {"size": 1.5},
            {"size": 1073741825}, {"digest": None}, {"digest": "sha256:wrong"},
            {"url": "https://api.example.invalid/asset/456"},
            {"browser_download_url": "https://github.com/other/repo/releases/download/x/a"},
            {"name": "roc_nightly-linux_x86_64-../bad.tar.gz"},
        ]
        for change in changes:
            with self.subTest(change=change):
                self.metadata["assets"] = [{**original, **change}]
                self.assert_refused()
                self.assertTrue(all(call["metadata"] for call in self.recorded_calls()))

    def test_wrong_same_size_or_truncated_body_is_rejected_before_extraction(self):
        original = self.body_path.read_bytes()
        for body in (b"x" * len(original), original[:-1], original + b"x"):
            with self.subTest(size=len(body)):
                self.body_path.write_bytes(body)
                self.assert_refused()
                self.assertFalse((self.workspace / self.expected_directory).exists())

    def test_oversized_or_invalid_metadata_rejected(self):
        for body in (b"{" + b"x" * 1048576, b"not json", b"null",
                     json.dumps(self.metadata).encode() + b"\n" + json.dumps(self.metadata).encode()):
            with self.subTest(size=len(body)):
                self.metadata_body = body
                self.assert_refused()

    def test_transport_failure_is_not_fallback_or_partial_install(self):
        for phase in ("metadata", "asset"):
            with self.subTest(phase=phase):
                self.fail = phase
                result = self.assert_refused()
                self.assertIn("504", result.stderr)
                self.assertFalse((self.workspace / self.expected_directory).exists())
                self.assertTrue(all("/releases/download/" not in call["args"][-1] for call in self.recorded_calls()))

    def test_stale_other_nightly_is_not_selected(self):
        stale = self.workspace / "roc_nightly-linux_x86_64-old"
        stale.mkdir()
        (stale / "roc").write_text("unverified stale compiler")
        result = self.run_action()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn(stale.name, (self.root / "github-path").read_text())
        self.assertEqual((stale / "roc").read_text(), "unverified stale compiler")

    def test_existing_exact_destination_is_not_trusted_or_overwritten(self):
        target = self.workspace / self.expected_directory
        target.mkdir()
        (target / "marker").write_text("keep")
        self.assert_refused()
        self.assertEqual((target / "marker").read_text(), "keep")
        self.assertFalse((target / "roc").exists())

    def test_wrong_archive_root_or_executable_symlink_never_reaches_path(self):
        for body in (self.archive("unexpected-root"), self.archive(symlink_executable=True)):
            with self.subTest(body_size=len(body)):
                self.set_release(body)
                self.assert_refused()


if __name__ == "__main__":
    unittest.main()
