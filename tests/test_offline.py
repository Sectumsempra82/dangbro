from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import serve
from tools import offline

class OfflineTests(unittest.TestCase):
    def test_private_interface_required(self):
        for host in ('127.0.0.1', '0.0.0.0', '8.8.8.8', '224.0.0.1', '169.254.1.2', 'localhost'):
            with self.assertRaises(ValueError): serve.lan_address(host)
        self.assertEqual(serve.lan_address('192.168.1.10'), '192.168.1.10')

    def test_corrupt_package_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            package = Path(tmp) / 'bad.ipk'; package.write_bytes(b'not a package')
            with self.assertRaisesRegex(ValueError, 'checksum mismatch'): offline.verify_ipk(package)

    def test_missing_asset_has_no_network_fallback(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(offline, 'WEB', Path(tmp)):
            with self.assertRaisesRegex(ValueError, 'Missing offline asset'): offline.check_assets()

    def test_http_serves_only_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            web = Path(tmp).resolve() / 'web'; web.mkdir()
            (web / 'index.html').write_text('<h1>local</h1>')
            (web / 'folder').mkdir()
            secret = web.parent / 'secret'; secret.write_text('private')
            (web / 'leak').symlink_to(secret)
            (web / '.hidden').write_text('private')
            with patch.object(serve, 'WEB', web):
                server = ThreadingHTTPServer(('127.0.0.1', 0), serve.Handler)
                server.expected_host = '127.0.0.1:' + str(server.server_port)
                thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
                try:
                    for path, host, expected in [('/', server.expected_host, 200), ('/', 'evil.example', 403),
                        ('/folder/', server.expected_host, 403), ('/leak', server.expected_host, 403),
                        ('/.hidden', server.expected_host, 403), ('/%2e%2e/secret', server.expected_host, 403)]:
                        connection = HTTPConnection('127.0.0.1', server.server_port, timeout=3)
                        connection.request('GET', path, headers={'Host': host})
                        response = connection.getresponse()
                        self.assertEqual(response.status, expected, path)
                        self.assertNotIn(b'private', response.read())
                        connection.close()
                finally:
                    server.shutdown(); server.server_close(); thread.join()

if __name__ == '__main__': unittest.main()
