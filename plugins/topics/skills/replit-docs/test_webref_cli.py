import contextlib
import importlib.util
import io
import json
import socket
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "replit_webref", Path(__file__).with_name("webref_cli.py")
)
web = importlib.util.module_from_spec(spec)
spec.loader.exec_module(web)


class ReplitTests(unittest.TestCase):
    def run_cli(self, directory, *args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with (
            patch.object(web, "OUTPUT", Path(directory)),
            patch("sys.argv", ["webref_cli.py", *args]),
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            result = web.main()
        return result, stdout.getvalue(), stderr.getvalue()

    def test_freshness_boundaries(self):
        now = datetime(2026, 1, 2, tzinfo=timezone.utc)

        class Clock(datetime):
            @classmethod
            def now(cls, tz=None):
                return now

        with patch.object(web, "datetime", Clock):
            for age, expected in (
                (timedelta(0), True),
                (timedelta(hours=24) - timedelta(microseconds=1), True),
                (timedelta(hours=24), False),
                (timedelta(seconds=-1), False),
            ):
                with self.subTest(age=age):
                    self.assertEqual(web.fresh({"fetched_at": (now - age).isoformat()}), expected)
            for invalid in ({}, {"fetched_at": "bad"}, {"fetched_at": "2026-01-01T00:00:00"}):
                self.assertFalse(web.fresh(invalid))

    def test_update_cache_force_and_index_only_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "snapshot.json"
            data = {"fetched_at": web.now(), "pages": [], "full": {"sections": []}}
            web.atomic_json(path, data)
            with patch.object(web, "build_snapshot", return_value=data) as build:
                self.assertEqual(self.run_cli(directory, "update")[0], 0)
                build.assert_not_called()
                self.assertEqual(self.run_cli(directory, "update", "--force")[0], 0)
                build.assert_called_once_with(allow_index_only=False)
                build.reset_mock()
                data["full"]["error"] = "invalid"
                web.atomic_json(path, data)
                self.assertEqual(self.run_cli(directory, "update")[0], 0)
                build.assert_called_once_with(allow_index_only=False)

    def test_initial_offline_missing_cache_and_write_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(web, "build_snapshot", side_effect=OSError("offline")):
                code, _, err = self.run_cli(directory, "update")
                self.assertEqual(code, 1)
                self.assertIn("offline", err)
            self.assertEqual(self.run_cli(directory, "search", "agent")[0], 1)
            with (
                patch.object(web, "build_snapshot", return_value={}),
                patch.object(web, "atomic_json", side_effect=PermissionError("read-only")),
            ):
                code, _, err = self.run_cli(directory, "update")
                self.assertEqual(code, 1)
                self.assertIn("read-only", err)
            self.assertFalse((Path(directory) / "snapshot.json").exists())

    def test_search_index_extract_and_index_only_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            data = {
                "fetched_at": "index time",
                "pages": [
                    {
                        "title": "Agent",
                        "url": web.BASE + "fr/agent.md",
                        "hierarchy": "French",
                        "index": web.ROOT,
                    }
                ],
                "full": {
                    "fetched_at": "full time",
                    "last_modified": None,
                    "sections": [
                        {"title": "English", "url": web.BASE + "agent", "body": "AGENTS.md content"}
                    ],
                },
            }
            web.atomic_json(Path(directory) / "snapshot.json", data)
            code, out, _ = self.run_cli(directory, "index", "FR/AGENT")
            self.assertEqual(code, 0)
            self.assertIn("French | Agent", out)
            code, out, _ = self.run_cli(directory, "search", "agents.MD")
            self.assertEqual(code, 0)
            self.assertIn(web.BASE + "agent", out)
            self.assertEqual(self.run_cli(directory, "extract", web.BASE + "agent.md")[0], 0)
            code, out, _ = self.run_cli(directory, "search", "not-present")
            self.assertEqual(code, 0)
            self.assertIn("Matches: 0", out)
            data["full"]["error"] = "bad format"
            web.atomic_json(Path(directory) / "snapshot.json", data)
            for command in ("search", "extract"):
                code, _, err = self.run_cli(directory, command, "agent")
                self.assertEqual(code, 1)
                self.assertIn("use index and page", err)

    def test_deleted_page_uses_cache_and_reports_staleness(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(web, "fetch", return_value=("old body", web.BASE + "a.md", None)):
                self.assertEqual(self.run_cli(directory, "page", "a")[0], 0)
            with patch.object(web, "fetch", side_effect=ValueError("HTTP 404")):
                code, out, err = self.run_cli(directory, "page", "a.md")
            self.assertEqual(code, 0)
            self.assertIn("stale cache", err)
            self.assertIn("HTTP 404", err)
            self.assertIn("fetched_at", err)
            self.assertIn("Full text:", out)

    def test_fetch_rejects_invalid_responses(self):
        class Response:
            status = 200

            def __init__(self, status, headers, body):
                self.status, self.headers, self.body = status, headers, body

            def getheader(self, name, default=None):
                return self.headers.get(name, default)

            def read(self, size):
                return self.body[:size]

        class Connection:
            def __init__(self, *args, **kwargs):
                pass

            def request(self, *args, **kwargs):
                pass

            def getresponse(self):
                return response

            def close(self):
                pass

        cases = [
            (404, {}, b"missing"),
            (200, {"Content-Length": "bad"}, b"x"),
            (200, {"Content-Length": "11"}, b"x"),
            (200, {"Content-Length": "4"}, b"abc"),
            (200, {}, b"01234567890"),
            (200, {"Content-Encoding": "gzip"}, b"x"),
            (200, {}, b"\xff"),
            (200, {}, b"<html>error"),
            (200, {}, b" "),
        ]
        with patch.object(web, "PinnedHTTPS", Connection):
            for status, headers, body in cases:
                response = Response(status, headers, body)
                with (
                    self.subTest(status=status, headers=headers, body=body),
                    self.assertRaises(ValueError),
                ):
                    web.fetch(web.ROOT, 10)
            response = Response(200, {"Content-Length": "10"}, b"0123456789")
            self.assertEqual(web.fetch(web.ROOT, 10)[0], "0123456789")

    def test_index_limits_and_failed_refresh_protection(self):
        root = f"# Root\n- [A]({web.BASE}a.md)\n- [Child]({web.BASE}_llms/en/child.txt)\n"
        child = f"# Child\n- [B]({web.BASE}b.md)\n"

        def retrieve(url, limit):
            return (root if url == web.ROOT else child), url, None

        for name, value in (
            ("MAX_DEPTH", 0),
            ("MAX_INDEXES", 1),
            ("MAX_PAGES", 1),
            ("MAX_TOTAL_INDEX_BYTES", len(root.encode()) - 1),
        ):
            with (
                self.subTest(limit=name),
                patch.object(web, name, value),
                patch.object(web, "fetch", side_effect=retrieve),
            ):
                with self.assertRaises(ValueError):
                    web.build_snapshot()
                with tempfile.TemporaryDirectory() as directory:
                    original = {"fetched_at": "old", "full": {"sections": []}}
                    path = Path(directory) / "snapshot.json"
                    web.atomic_json(path, original)
                    code, _, err = self.run_cli(directory, "update", "--force")
                    self.assertEqual(code, 0)
                    self.assertIn("stale cache", err)
                    self.assertEqual(json.loads(path.read_text()), original)

    def test_atomic_replace_failure_preserves_old_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "snapshot.json"
            path.write_text("old", encoding="utf-8")
            with (
                patch.object(web.os, "replace", side_effect=OSError("disk failure")),
                self.assertRaises(OSError),
            ):
                web.atomic_text(path, "new")
            self.assertEqual(path.read_text(), "old")
            self.assertEqual(list(Path(directory).iterdir()), [path])

    def test_redirect_limit_and_private_destination(self):
        class Response:
            status = 302

            def getheader(self, name, default=None):
                return "/again" if name == "Location" else default

        class Connection:
            def __init__(self, *args, **kwargs):
                pass

            def request(self, *args, **kwargs):
                pass

            def getresponse(self):
                return Response()

            def close(self):
                pass

        with (
            patch.object(web, "PinnedHTTPS", Connection),
            patch.object(web, "MAX_REDIRECTS", 2),
            self.assertRaisesRegex(ValueError, "redirect limit"),
        ):
            web.fetch(web.ROOT, 100)
        answers = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))]
        with (
            patch.object(web.socket, "getaddrinfo", return_value=answers),
            patch.object(web.socket, "create_connection") as connect,
        ):
            with self.assertRaisesRegex(ValueError, "non-public"):
                web.PinnedHTTPS("docs.replit.com").connect()
            connect.assert_not_called()

    def test_initial_index_only_is_saved_and_retryable(self):
        def retrieve(url, limit):
            if url == web.ROOT:
                return f"# Root\n- [A]({web.BASE}a.md)\n", url, None
            raise OSError("full offline")

        with (
            tempfile.TemporaryDirectory() as directory,
            patch.object(web, "fetch", side_effect=retrieve),
        ):
            code, _, err = self.run_cli(directory, "update")
            self.assertEqual(code, 0)
            self.assertIn("index only", err)
            self.assertEqual(self.run_cli(directory, "index", "a")[0], 0)
            self.assertEqual(self.run_cli(directory, "search", "a")[0], 1)
            data = json.loads((Path(directory) / "snapshot.json").read_text())
            self.assertIn("full offline", data["full"]["error"])

    def test_url_restrictions(self):
        for url in (
            "http://docs.replit.com/a",
            "https://evil.test/a",
            "https://docs.replit.com.evil.test/a",
            "https://user@docs.replit.com/a",
            "https://docs.replit.com:444/a",
            "https://docs.replit.com/%2e%2e/a",
            "https://docs.replit.com/a?x=1",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                web.validate_url(url)
        self.assertEqual(
            web.page_url("features/agent/skills"), web.BASE + "features/agent/skills.md"
        )

    def test_dns_rejects_mixed_public_and_private(self):
        answers = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, 443))
            for ip in ("8.8.8.8", "127.0.0.1")
        ]
        with (
            patch.object(web.socket, "getaddrinfo", return_value=answers),
            self.assertRaises(ValueError),
        ):
            web.public_addresses("docs.replit.com")

    def test_full_source_boundaries(self):
        a, b = web.BASE + "a", web.BASE + "b"
        text = f"# A\nSource: {a}\n\nbody\n# ordinary heading\ntext\n# B\nSource: {b}\n\nsecond\n"
        sections = web.parse_sections(text, {a, b})
        self.assertIn("# ordinary heading", sections[0]["body"])
        for bad in (
            text + f"# Duplicate\nSource: {a}\n\nx",
            text.replace(b, web.BASE + "unknown"),
            text.replace("Source: " + b, "Source: invalid URL"),
            "preamble\n" + text,
        ):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                web.parse_sections(bad, {a, b})

    def test_hierarchical_index_recursion(self):
        child = web.BASE + "_llms/en/features.txt"
        responses = {
            web.ROOT: f"# Root\n- [Features]({child})\n## Home\n- [A]({web.BASE}a.md)\n",
            child: f"# Features\n## Agent\n- [B]({web.BASE}b.md)\n",
            web.FULL: f"# A\nSource: {web.BASE}a\n\nbody\n# B\nSource: {web.BASE}b\n\nbody\n",
        }
        with patch.object(web, "fetch", side_effect=lambda url, limit: (responses[url], url, None)):
            snapshot = web.build_snapshot()
        self.assertEqual(len(snapshot["indexes"]), 2)
        self.assertEqual(snapshot["pages"][1]["hierarchy"], "Features / Agent")

    def test_failed_update_keeps_existing_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            path = out / "snapshot.json"
            original = {"fetched_at": "2020-01-01T00:00:00+00:00", "value": "untouched"}
            path.write_text(json.dumps(original), encoding="utf-8")
            with (
                patch.object(web, "OUTPUT", out),
                patch.object(web, "build_snapshot", side_effect=ValueError("failed")),
                patch("sys.argv", ["webref_cli.py", "update", "--force"]),
                contextlib.redirect_stderr(io.StringIO()) as err,
            ):
                self.assertEqual(web.main(), 0)
            self.assertEqual(json.loads(path.read_text()), original)
            self.assertIn(original["fetched_at"], err.getvalue())

    def test_redirect_revalidated_before_connecting(self):
        class Response:
            status = 302

            def getheader(self, key, default=None):
                return "https://evil.test/" if key == "Location" else default

        class Connection:
            def __init__(self, *args, **kwargs):
                pass

            def request(self, *args, **kwargs):
                pass

            def getresponse(self):
                return Response()

            def close(self):
                pass

        with patch.object(web, "PinnedHTTPS", Connection), self.assertRaises(ValueError):
            web.fetch(web.ROOT, 1000)

    def test_page_failure_without_cache_is_error(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.object(web, "OUTPUT", Path(directory)),
            patch.object(web, "fetch", side_effect=OSError("offline")),
            patch("sys.argv", ["webref_cli.py", "page", "welcome"]),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            self.assertEqual(web.main(), 1)

    def test_extract_found_and_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            web.atomic_json(
                out / "snapshot.json",
                {
                    "fetched_at": "2020",
                    "full": {
                        "fetched_at": "2019",
                        "last_modified": None,
                        "sections": [{"title": "A", "url": web.BASE + "a", "body": "body"}],
                    },
                },
            )
            with (
                patch.object(web, "OUTPUT", out),
                patch("sys.argv", ["webref_cli.py", "extract", "a"]),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                self.assertEqual(web.main(), 0)
            with (
                patch.object(web, "OUTPUT", out),
                patch("sys.argv", ["webref_cli.py", "extract", "missing"]),
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                self.assertEqual(web.main(), 1)
            files = list((out / "sections").glob("*.md"))
            self.assertEqual(len(files), 1)
            self.assertIn("\n\n# A\n\nbody\n", files[0].read_text(encoding="utf-8"))

    def test_page_output_preserves_lines(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            with (
                patch.object(web, "OUTPUT", out),
                patch.object(
                    web, "fetch", return_value=("# Title\n\nBody\n", web.BASE + "a.md", None)
                ),
                patch("sys.argv", ["webref_cli.py", "page", "a"]),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                self.assertEqual(web.main(), 0)
            files = list((out / "pages").glob("*.md"))
            self.assertEqual(len(files), 1)
            self.assertIn("\n\n# Title\n\nBody\n", files[0].read_text(encoding="utf-8"))

    def test_first_fetch_can_preserve_index_when_full_invalid(self):
        def retrieve(url, limit):
            if url == web.ROOT:
                return f"# Root\n- [A]({web.BASE}a.md)\n", url, None
            return "unrecognized format", url, None

        with patch.object(web, "fetch", side_effect=retrieve):
            with self.assertRaises(ValueError):
                web.build_snapshot()
            data = web.build_snapshot(allow_index_only=True)
        self.assertEqual(len(data["pages"]), 1)
        self.assertIn("error", data["full"])


if __name__ == "__main__":
    unittest.main()
