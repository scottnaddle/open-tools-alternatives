"""비-GitHub 호스트 403이 일일 검증 전체를 중단하지 않는지 확인.

네트워크 없이 urllib를 흉내 낸다.
  python3 scripts/test_daily_verifier_host.py
"""
import io
import json
import os
import sys
import tempfile
import unittest
import urllib.error
from email.message import EmailMessage
from unittest import mock

sys.path.insert(0, os.path.dirname(__file__))
import daily_verifier as dv

KDE_URL = "https://invent.kde.org/api/v4/projects/graphics%2Fkrita?license=true"


def http_error(url, code):
    return urllib.error.HTTPError(url, code, "err", EmailMessage(), io.BytesIO(b""))


class Resp(io.BytesIO):
    def __init__(self, payload, headers=None):
        super().__init__(json.dumps(payload).encode())
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def tool_doc():
    return {
        "license": {"value": "GPL-3.0", "status": "verified", "lastVerified": "2026-10-12T22:35:34+00:00"},
        "github": {
            "repo": "KDE/krita",
            "stars": 10536,
            "lastPush": "2026-10-12",
            "archived": False,
            "latestRelease": None,
            "fetchedAt": "2026-10-12",
            "official": {"host": "https://invent.kde.org/graphics/krita", "license": "gpl-3.0"},
        },
        "health": "active",
    }


class NonGithubRateLimitTests(unittest.TestCase):
    def test_get_non_github_403_retries_then_returns_none(self):
        calls = {"n": 0}

        def urlopen(req, timeout=20):
            calls["n"] += 1
            raise http_error(req.full_url, 403)

        with mock.patch.object(dv.urllib.request, "urlopen", urlopen), \
             mock.patch.object(dv.time, "sleep") as sleep:
            result = dv.get(KDE_URL, gh=False)
        self.assertIsNone(result)
        self.assertEqual(calls["n"], 1 + dv.NON_GITHUB_RATE_RETRIES)
        self.assertEqual(sleep.call_count, dv.NON_GITHUB_RATE_RETRIES)
        self.assertEqual(sleep.call_args_list[0].args[0], dv.NON_GITHUB_RATE_BACKOFF)

    def test_get_github_403_still_exits_without_retry(self):
        def urlopen(req, timeout=20):
            raise http_error(req.full_url, 403)

        with mock.patch.object(dv.urllib.request, "urlopen", urlopen), \
             mock.patch.object(dv.time, "sleep") as sleep:
            with self.assertRaises(SystemExit) as ctx:
                dv.get("https://api.github.com/repos/KDE/krita", gh=True)
        self.assertIn("403", str(ctx.exception))
        sleep.assert_not_called()

    def test_github_remaining_zero_exits(self):
        def urlopen(req, timeout=20):
            return Resp({}, headers={"X-RateLimit-Remaining": "0"})

        with mock.patch.object(dv.urllib.request, "urlopen", urlopen):
            with self.assertRaises(SystemExit) as ctx:
                dv.get("https://api.github.com/rate_limit", gh=True)
        self.assertIn("한도", str(ctx.exception))

    def test_gitlab_403_returns_none(self):
        def urlopen(req, timeout=20):
            raise http_error(req.full_url, 403)

        with mock.patch.object(dv.urllib.request, "urlopen", urlopen), \
             mock.patch.object(dv.time, "sleep"):
            self.assertIsNone(dv.gitlab("https://invent.kde.org", "graphics/krita"))

    def _github_then_kde_403(self, req, timeout=20):
        url = req.full_url
        if "/releases/" in url:
            raise http_error(url, 404)
        if "api.github.com" in url:
            return Resp({
                "stargazers_count": 10536,
                "pushed_at": "2026-10-12T12:00:00Z",
                "archived": False,
            })
        if "invent.kde.org" in url:
            raise http_error(url, 403)
        raise AssertionError(url)

    def test_mirror_403_records_skip_without_changing_status(self):
        doc = tool_doc()
        raw = json.dumps(doc, ensure_ascii=False, indent=2)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "krita.json")
            with open(path, "w") as fp:
                fp.write(raw)
            before_changes = set(os.listdir(dv.CHG)) if os.path.isdir(dv.CHG) else set()
            with mock.patch.object(dv.urllib.request, "urlopen", self._github_then_kde_403), \
                 mock.patch.object(dv.time, "sleep"):
                result = dv.process_tool(path)
            with open(path) as fp:
                after = fp.read()
        self.assertEqual(after, raw)
        self.assertEqual(result.get("mirror"), "skipped/unverified")
        self.assertFalse(result.get("modified"))
        self.assertEqual(result.get("changes"), [])
        saved = json.loads(after)
        self.assertEqual(saved["license"]["status"], "verified")
        self.assertEqual(saved["health"], "active")
        self.assertEqual(saved["github"]["official"]["license"], "gpl-3.0")
        after_changes = set(os.listdir(dv.CHG)) if os.path.isdir(dv.CHG) else set()
        self.assertEqual(before_changes, after_changes)

    def test_mirror_does_not_swallow_github_systemexit(self):
        doc = tool_doc()
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "krita.json")
            with open(path, "w") as fp:
                json.dump(doc, fp)
            with mock.patch.object(dv.urllib.request, "urlopen", self._github_then_kde_403), \
                 mock.patch.object(dv, "gitlab", side_effect=SystemExit("GitHub 요청 한도 소진 — 중단")), \
                 mock.patch.object(dv.time, "sleep"):
                with self.assertRaises(SystemExit):
                    dv.process_tool(path)
            with open(path) as fp:
                saved = json.load(fp)
        self.assertEqual(saved["health"], "active")
        self.assertEqual(saved["license"]["status"], "verified")


if __name__ == "__main__":
    unittest.main()
