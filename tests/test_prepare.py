import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import offline
import prepare


class PrepareTests(unittest.TestCase):
    def test_local_import_bundles_complete_allowlist_without_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            web = root / 'docs'
            package = root / 'input.ipk'
            package.write_bytes(b'test package')
            digest = hashlib.sha256(package.read_bytes()).hexdigest()
            names = ['README.md', 'OFFLINE.md', 'serve.py', 'tools/offline.py', 'tools/prepare.py']
            names += ['docs/' + name for name in offline.ASSETS]
            for name in names:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(name)
            (root / 'private-key').write_text('must not be bundled')
            (web / 'unrelated.txt').write_text('must not be bundled')
            with patch.object(offline, 'WEB', web), patch.object(offline, 'SHA256', digest), \
                    patch.object(prepare, 'ROOT', root), patch.object(prepare, 'WEB', web), \
                    patch.object(prepare.urllib.request, 'urlopen') as network, \
                    patch.object(sys, 'argv', ['prepare.py', '--ipk', str(package), '--bundle']):
                prepare.main()
                network.assert_not_called()
            with zipfile.ZipFile(root / 'dist/dangbro-offline.zip') as archive:
                expected = names + ['docs/resources/' + offline.IPK]
                self.assertEqual(set(archive.namelist()), {'dangbro-offline/' + name for name in expected})
                self.assertEqual(archive.read('dangbro-offline/docs/resources/' + offline.IPK), package.read_bytes())

    def test_bad_import_does_not_replace_existing_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            resources = root / 'resources'
            resources.mkdir()
            destination = resources / offline.IPK
            destination.write_bytes(b'previous package')
            package = root / 'bad.ipk'
            package.write_bytes(b'bad import')
            with patch.object(prepare, 'WEB', root), \
                    patch.object(sys, 'argv', ['prepare.py', '--ipk', str(package)]):
                with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
                    prepare.main()
            self.assertEqual(destination.read_bytes(), b'previous package')

    def test_symlinked_asset_is_rejected_before_serving_or_bundling(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            real = root / 'real.html'
            real.write_text('test')
            (root / offline.ASSETS[0]).symlink_to(real)
            with patch.object(offline, 'WEB', root):
                with self.assertRaisesRegex(ValueError, 'symlinks'):
                    offline.check_assets()


if __name__ == '__main__':
    unittest.main()
