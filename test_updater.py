# -*- coding: utf-8 -*-
"""Tests for the auto-update module (network is mocked)."""

import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import updater
import version


class FakeResponse:
    def __init__(self, data, headers=None):
        self._data = data
        self.headers = headers or {}

    def __init__(self, data, headers=None):
        self._data = data
        self.headers = headers or {}
        self._done = False

    def read(self, n=-1):
        if self._done:
            return b""
        self._done = True
        return self._data

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class VersionTest(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(updater.parse_version("1.2.1"), (1, 2, 1))
        self.assertEqual(updater.parse_version("1.2"), (1, 2, 0))
        self.assertEqual(updater.parse_version("1.2.1-rc1"), (1, 2, 1))
        self.assertEqual(updater.parse_version(""), (0, 0, 0))

    def test_newer(self):
        self.assertTrue(updater.is_newer("1.2.1", "1.2.0"))
        self.assertFalse(updater.is_newer("1.2.0", "1.2.1"))
        self.assertFalse(updater.is_newer("1.2.1", "1.2.1"))
        self.assertTrue(updater.is_newer("2.0.0", "1.9.9"))


class CheckTest(unittest.TestCase):
    def test_available(self):
        man = {"version": "99.0.0", "url": "http://x/Setup.exe", "notes": "n"}
        with mock.patch.object(updater, "fetch_manifest", return_value=man):
            r = updater.check_for_update()
        self.assertTrue(r["available"])
        self.assertEqual(r["version"], "99.0.0")
        self.assertEqual(r["current"], version.__version__)
        self.assertIsNone(r["error"])

    def test_uptodate(self):
        man = {"version": version.__version__, "url": "http://x/Setup.exe"}
        with mock.patch.object(updater, "fetch_manifest", return_value=man):
            r = updater.check_for_update()
        self.assertFalse(r["available"])
        self.assertIsNone(r["error"])

    def test_error(self):
        with mock.patch.object(updater, "fetch_manifest", side_effect=OSError("boom")):
            r = updater.check_for_update()
        self.assertFalse(r["available"])
        self.assertIn("boom", r["error"])


class DownloadTest(unittest.TestCase):
    def test_download(self):
        data = b"fake-installer-bytes"
        def fake_open(req, timeout=None):
            return FakeResponse(data, headers={"Content-Length": str(len(data))})
        with mock.patch.object(updater.urllib.request, "urlopen", side_effect=fake_open):
            with tempfile.TemporaryDirectory() as d:
                path = updater.download_installer("http://x/Setup.exe", dest_dir=d)
                self.assertTrue(os.path.isfile(path))
                with open(path, "rb") as f:
                    self.assertEqual(f.read(), data)

    def test_download_progress(self):
        data = b"x" * 200000
        def fake_open(req, timeout=None):
            return FakeResponse(data, headers={"Content-Length": str(len(data))})
        seen = []
        with mock.patch.object(updater.urllib.request, "urlopen", side_effect=fake_open):
            with tempfile.TemporaryDirectory() as d:
                updater.download_installer("http://x/Setup.exe", dest_dir=d,
                                           progress=lambda g, t: seen.append((g, t)))
        self.assertTrue(seen)
        self.assertEqual(seen[-1][0], len(data))
        self.assertEqual(seen[-1][1], len(data))


class ApplyTest(unittest.TestCase):
    def test_apply_update_writes_bat(self):
        exe = r"C:\Games\SheriffOfNottingham.exe"
        with mock.patch.object(updater, "_launch_bat", return_value=True) as launch:
            with tempfile.TemporaryDirectory() as d:
                inst = os.path.join(d, "Setup.exe")
                with open(inst, "wb") as f:
                    f.write(b"x")
                ok = updater.apply_update(inst, exe_path=exe)
                self.assertTrue(ok)
                bat = os.path.join(updater.download_dir(), "run_update.bat")
                with open(bat, encoding="ascii", errors="replace") as f:
                    content = f.read()
                self.assertIn("VERYSILENT", content)
                self.assertIn(exe, content)
                launch.assert_called_once()

    def test_apply_update_no_exe(self):
        with mock.patch.object(updater, "_exe_path", return_value=None):
            self.assertFalse(updater.apply_update(r"C:\tmp\Setup.exe"))


class ManifestTest(unittest.TestCase):
    def test_repo_manifest_is_valid(self):
        """update.json in the repo must parse and reference the current version."""
        root = os.path.dirname(os.path.abspath(__file__))
        p = os.path.join(root, "update.json")
        self.assertTrue(os.path.isfile(p), "update.json missing")
        import json
        with open(p, encoding="utf-8") as f:
            man = json.load(f)
        self.assertEqual(man["version"], version.__version__)
        self.assertIn(man["version"], man["url"])


if __name__ == "__main__":
    unittest.main(verbosity=2)