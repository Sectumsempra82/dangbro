"""Exercise the shell's download/reporting branches without running TV operations."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'docs/resources/root_persistence.sh').read_text().split('# ---------- main ----------')[0]
LOCAL_IPK = 'http://192.168.1.10:8000/resources/org.webosbrew.hbchannel_0.7.3_all.ipk'


class RootOfflineTests(unittest.TestCase):
    def run_shell(self, url=LOCAL_IPK, offline='1', curl_status='0', checksum_status='0', upload=False):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            source = SOURCE.replace('LOGFILE="/tmp/dangbro-root.log"', 'LOGFILE="$TEST_DIR/root.log"')
            source = source.replace('IPK_TMP="/tmp/hbchannel.ipk"', 'IPK_TMP="$TEST_DIR/hbchannel.ipk"')
            source = source.replace('LUNA_FIFO="/tmp/dangbro-root.fifo"', 'LUNA_FIFO="$TEST_DIR/root.fifo"')
            script = directory / 'test.sh'
            script.write_text(source + '''
log() { :; }
send_toast() { :; }
curl() { printf '%s\\n' "$@" >> "$TEST_DIR/curl.args"; return "$CURL_STATUS"; }
sha256sum() { cat > "$TEST_DIR/checksum.input"; return "$CHECKSUM_STATUS"; }
printf 'upload_flag=%s\\n' "$UPLOAD_LOG"
''' + ('UPLOAD_LOG=1; upload_log' if upload else 'prepare_hbc_ipk') + '''
status=$?
printf 'status=%s\\nerror=%s\\n' "$status" "$error_reason"
exit "$status"
''')
            result = subprocess.run(['sh', str(script)], text=True, capture_output=True, env={
                **os.environ, 'TEST_DIR': tmp, 'DANGBRO_OFFLINE': offline, 'IPK_URL': url,
                'UPLOAD_LOG': '1', 'CURL_STATUS': curl_status, 'CHECKSUM_STATUS': checksum_status
            })
            args = directory / 'curl.args'
            checksum = directory / 'checksum.input'
            return result, args.read_text().splitlines() if args.exists() else [], checksum.read_text() if checksum.exists() else ''

    def test_offline_download_uses_no_proxy_no_redirect_and_verifies_pin(self):
        result, args, checksum = self.run_shell()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(args[:2], ['--noproxy', '*'])
        self.assertIn('--fail', args)
        self.assertNotIn('-L', args)
        self.assertEqual(args[-2:], ['--', LOCAL_IPK])
        self.assertIn('d10bf3c753551d7c72fb7a92b20fcd2317e502a220ac668ba8e76f6ea78b363c', checksum)
        self.assertIn('upload_flag=\n', result.stdout)

    def test_offline_rejects_missing_external_or_malformed_url_without_curl(self):
        for url in ['', 'https://github.com/package.ipk', 'http://localhost/package.ipk',
                    'http://8.8.8.8/package.ipk', 'http://10.999.1.1/package.ipk',
                    'http://192.168.1.1/evil;command.ipk', 'http://192.168.1.1@evil.example/package.ipk']:
            with self.subTest(url=url):
                result, args, _ = self.run_shell(url)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(args, [])

    def test_download_and_checksum_failures_have_no_network_fallback(self):
        for curl_status, checksum_status in [('22', '0'), ('0', '1')]:
            result, args, _ = self.run_shell(curl_status=curl_status, checksum_status=checksum_status)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(args.count(LOCAL_IPK), 1)
            self.assertFalse(any('github.com' in arg or 'paste.rs' in arg for arg in args))

    def test_offline_log_upload_is_blocked_even_if_reenabled_after_initialization(self):
        result, args, _ = self.run_shell(upload=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(args, [])

    def test_hosted_download_retains_official_default_and_redirects(self):
        result, args, checksum = self.run_shell(url='', offline='0')
        self.assertEqual(result.returncode, 0)
        self.assertIn('-L', args)
        self.assertEqual(args[-1], 'https://github.com/webosbrew/webos-homebrew-channel/releases/download/v0.7.3/org.webosbrew.hbchannel_0.7.3_all.ipk')
        self.assertIn('upload_flag=1', result.stdout)
        self.assertEqual(checksum, '')


if __name__ == '__main__':
    unittest.main()
