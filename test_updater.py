# -*- coding: utf-8 -*-
"""Tests for the auto-update module (network is mocked)."""

import json
import os
import socket
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


def _single_source():
    patcher = mock.patch.object(
        updater, "MANIFEST_SOURCES",
        [("raw", "http://fake/manifest.json")])
    patcher.start()
    updater._MANIFEST_PATCH = patcher
    return patcher


def _stop_sources():
    p = getattr(updater, "_MANIFEST_PATCH", None)
    if p is not None:
        p.stop()
        updater._MANIFEST_PATCH = None


class VersionTest(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(updater.parse_version("1.2.2"), (1, 2, 2))
        self.assertEqual(updater.parse_version("1.2"), (1, 2, 0))
        self.assertEqual(updater.parse_version("1.2.2-rc1"), (1, 2, 2))
        self.assertEqual(updater.parse_version(""), (0, 0, 0))

    def test_newer(self):
        self.assertTrue(updater.is_newer("1.2.2", "1.2.1"))
        self.assertFalse(updater.is_newer("1.2.1", "1.2.2"))
        self.assertFalse(updater.is_newer("1.2.2", "1.2.2"))
        self.assertTrue(updater.is_newer("2.0.0", "1.9.9"))

    def test_error_code(self):
        self.assertEqual(updater.error_code(TimeoutError("x")), "timeout")
        self.assertEqual(updater.error_code(socket.timeout("x")), "timeout")
        self.assertEqual(updater.error_code(OSError("conn reset")), "network")
        self.assertEqual(updater.error_code(ValueError("boom")), "unknown")


class CheckTest(unittest.TestCase):
    def tearDown(self):
        _stop_sources()

    def test_available(self):
        _single_source()
        man = {"version": "99.0.0", "url": "http://x/Setup.exe", "notes": "n"}
        with mock.patch.object(updater, "fetch_manifest", return_value=man):
            r = updater.check_for_update()
        self.assertTrue(r["available"])
        self.assertEqual(r["version"], "99.0.0")
        self.assertEqual(r["current"], version.__version__)
        self.assertIsNone(r["error"])

    def test_uptodate(self):
        _single_source()
        man = {"version": version.__version__, "url": "http://x/Setup.exe"}
        with mock.patch.object(updater, "fetch_manifest", return_value=man):
            r = updater.check_for_update()
        self.assertFalse(r["available"])
        self.assertIsNone(r["error"])

    def test_fallback_to_next_source(self):
        sources = [("raw", "http://fake/a.json"), ("cdn", "http://fake/b.json")]
        with mock.patch.object(updater, "MANIFEST_SOURCES", sources):
            man = {"version": "99.0.0", "url": "http://x/Setup.exe"}
            with mock.patch.object(updater, "fetch_manifest",
                                   side_effect=[OSError("first dead"), man]):
                r = updater.check_for_update()
        self.assertTrue(r["available"])
        self.assertIsNone(r["error"])

    def test_all_fail_timeout(self):
        _single_source()
        with mock.patch.object(updater, "fetch_manifest",
                               side_effect=TimeoutError("slow")):
            r = updater.check_for_update()
        self.assertFalse(r["available"])
        self.assertEqual(r["error"], "timeout")
        self.assertIn("slow", r["detail"])

    def test_all_fail_network(self):
        _single_source()
        with mock.patch.object(updater, "fetch_manifest",
                               side_effect=OSError("conn refused")):
            r = updater.check_for_update()
        self.assertEqual(r["error"], "network")

    def test_release_api_fallback(self):
        api = ("api", "http://fake/api/releases/latest")
        with mock.patch.object(updater, "MANIFEST_SOURCES", [api]):
            payload = {
                "tag_name": "v99.0.0",
                "body": "notes here",
                "assets": [
                    {"browser_download_url": "http://x/not-an-exe.txt"},
                    {"browser_download_url": "http://x/Setup-99.0.0.exe"},
                ],
            }
            with mock.patch.object(updater, "_fetch",
                                   return_value=json.dumps(payload).encode()):
                r = updater.check_for_update()
        self.assertTrue(r["available"])
        self.assertEqual(r["version"], "99.0.0")
        self.assertEqual(r["url"], "http://x/Setup-99.0.0.exe")
        self.assertIn("notes", r["notes"])
        self.assertIsNone(r["error"])


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

    def test_download_retry_then_success(self):
        data = b"ok"
        def fake_open(req, timeout=None):
            return FakeResponse(data, headers={"Content-Length": str(len(data))})
        calls = {"n": 0}
        def flaky(req, timeout=None):
            calls["n"] += 1
            if calls["n"] == 1:
                raise TimeoutError("first attempt slow")
            return fake_open(req, timeout=timeout)
        with mock.patch.object(updater.urllib.request, "urlopen", side_effect=flaky):
            with tempfile.TemporaryDirectory() as d:
                path = updater.download_installer("http://x/Setup.exe", dest_dir=d)
                with open(path, "rb") as f:
                    self.assertEqual(f.read(), data)
        self.assertEqual(calls["n"], 2)


class ApplyTest(unittest.TestCase):
    def setUp(self):
        self._flag = updater._pending_flag()
        if os.path.exists(self._flag):
            os.remove(self._flag)

    def tearDown(self):
        if os.path.exists(self._flag):
            os.remove(self._flag)

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

    def test_apply_update_guard_flag(self):
        """A second apply_update while one is pending must not double-schedule."""
        exe = r"C:\Games\SheriffOfNottingham.exe"
        with mock.patch.object(updater, "_launch_bat", return_value=True) as launch:
            with tempfile.TemporaryDirectory() as d:
                inst = os.path.join(d, "Setup.exe")
                with open(inst, "wb") as f:
                    f.write(b"x")
                self.assertTrue(updater.apply_update(inst, exe_path=exe))
                self.assertTrue(os.path.exists(updater._pending_flag()))
                self.assertTrue(updater.apply_update(inst, exe_path=exe))
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
        with open(p, encoding="utf-8") as f:
            man = json.load(f)
        self.assertEqual(man["version"], version.__version__)
        self.assertIn(man["version"], man["url"])


if __name__ == "__main__":
    unittest.main(verbosity=2)