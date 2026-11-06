from __future__ import annotations

import io
import unittest
import urllib.error
import urllib.request
from unittest.mock import Mock, patch

from infra.control_plane import probe_package_mirrors as probe_module


class ProbeTests(unittest.TestCase):
    def test_probe_uses_get_tls_opener_timeout_and_small_read(self) -> None:
        response = Mock()
        response.status = 200
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        opener = Mock()
        opener.open.return_value = response

        with patch.object(
            probe_module.urllib.request, "build_opener", return_value=opener
        ) as build:
            status, elapsed, error = probe_module.probe(
                "https://mirror.example/simple/jsonschema/"
            )

        self.assertEqual(status, 200)
        self.assertEqual(error, "")
        self.assertGreaterEqual(elapsed, 0)
        self.assertIsInstance(
            build.call_args.args[0], probe_module.HTTPSOnlyRedirectHandler
        )
        request, = opener.open.call_args.args
        self.assertEqual(request.get_method(), "GET")
        self.assertEqual(request.get_header("User-agent"), probe_module.USER_AGENT)
        self.assertEqual(request.get_header("Accept"), "text/html")
        self.assertEqual(opener.open.call_args.kwargs["timeout"], 12)
        response.read.assert_called_once_with(2048)

    def test_http_error_returns_only_status(self) -> None:
        opener = Mock()
        opener.open.side_effect = urllib.error.HTTPError(
            "https://mirror.example/simple/pkg/",
            403,
            "forbidden",
            hdrs=None,
            fp=io.BytesIO(b"private response body"),
        )
        with patch.object(
            probe_module.urllib.request, "build_opener", return_value=opener
        ):
            status, _, error = probe_module.probe(
                "https://mirror.example/simple/pkg/"
            )
        self.assertEqual(status, 403)
        self.assertEqual(error, "HTTP 403")
        self.assertNotIn("private response", error)

    def test_transport_error_does_not_echo_sensitive_detail(self) -> None:
        opener = Mock()
        opener.open.side_effect = urllib.error.URLError("token=do-not-print")
        with patch.object(
            probe_module.urllib.request, "build_opener", return_value=opener
        ):
            status, _, error = probe_module.probe(
                "https://mirror.example/simple/pkg/"
            )
        self.assertIsNone(status)
        self.assertEqual(error, "URLError")
        self.assertNotIn("do-not-print", error)

    def test_redirect_handler_rejects_http_downgrade(self) -> None:
        handler = probe_module.HTTPSOnlyRedirectHandler()
        request = urllib.request.Request("https://mirror.example/pkg/")
        with self.assertRaises(urllib.error.URLError):
            handler.redirect_request(
                request, None, 302, "Found", {}, "http://mirror.example/pkg/"
            )

    def test_redirect_handler_allows_https_redirect(self) -> None:
        handler = probe_module.HTTPSOnlyRedirectHandler()
        request = urllib.request.Request("https://mirror.example/pkg/")
        redirected = handler.redirect_request(
            request, None, 302, "Found", {}, "https://cdn.example/pkg/"
        )
        self.assertEqual(redirected.full_url, "https://cdn.example/pkg/")

    def test_main_reports_any_non_200_as_failure(self) -> None:
        from contextlib import redirect_stdout
        output = io.StringIO()
        with patch.object(
            probe_module, "MIRRORS", (("test", "https://mirror.example/simple/"),)
        ):
            with patch.object(probe_module, "PACKAGES", ("one", "two")):
                with patch.object(
                    probe_module,
                    "probe",
                    side_effect=[(200, 0.01, ""), (404, 0.02, "HTTP 404")],
                ):
                    with redirect_stdout(output):
                        result = probe_module.main()
        self.assertEqual(result, 1)
        self.assertIn("Non-200 package pages: 1", output.getvalue())


if __name__ == "__main__":
    unittest.main()
