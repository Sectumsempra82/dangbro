import hashlib
from html.parser import HTMLParser
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from urllib.parse import unquote, urlsplit
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import build_pages

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_FILES = {'index.html', '.nojekyll', 'downloads/README.md', 'downloads/PRIVACY.md',
                'downloads/privacy.py', 'downloads/dangbro-offline.zip', 'downloads/SHA256SUMS'}

class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.links = []
    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name in ('href', 'src'): self.links.append(value)

class PagesTests(unittest.TestCase):
    def prepare(self, root):
        for name in ('README.md', 'PRIVACY.md', 'privacy.py', 'site/index.html'):
            target = root / name; target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
        (root / 'dist').mkdir()
        (root / 'dist' / 'dangbro-offline.zip').write_bytes(b'opaque offline fixture')

    def test_only_downloads_are_published_and_all_links_resolve(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.prepare(root)
            output = build_pages.build(root)
            files = {p.relative_to(output).as_posix() for p in output.rglob('*') if p.is_file()}
            self.assertEqual(files, PUBLIC_FILES)
            bundle = root / 'dist' / 'dangbro-offline.zip'
            self.assertEqual((output / 'downloads' / bundle.name).read_bytes(), bundle.read_bytes())
            self.assertIn(hashlib.sha256(bundle.read_bytes()).hexdigest(), (output / 'downloads' / 'SHA256SUMS').read_text())
            parser = Links(); parser.feed((output / 'index.html').read_text())
            for link in parser.links:
                parsed = urlsplit(link)
                if not parsed.scheme and parsed.path:
                    self.assertTrue((output / unquote(parsed.path)).exists(), link)

    def test_rebuild_removes_previously_published_launcher_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.prepare(root)
            stale = root / 'dist' / 'pages' / 'online' / 'resources'
            stale.mkdir(parents=True)
            (stale / 'root_persistence.sh').write_text('old executable asset')
            output = build_pages.build(root)
            self.assertFalse((output / 'online').exists())
            self.assertEqual({p.relative_to(output).as_posix() for p in output.rglob('*') if p.is_file()}, PUBLIC_FILES)

if __name__ == '__main__': unittest.main()
