import hashlib
from html.parser import HTMLParser
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import unquote, urlsplit
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import build_pages
from offline import ASSETS, IPK

ROOT = Path(__file__).resolve().parents[1]

class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.links = []
    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name in ('href', 'src'): self.links.append(value)

class PagesTests(unittest.TestCase):
    def test_hosted_build_keeps_offline_sources_unchanged_and_has_complete_downloads(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ASSETS + ['resources/' + IPK]:
                target = root / 'web' / name
                target.parent.mkdir(parents=True, exist_ok=True)
                if name.endswith('.ipk'): target.write_bytes(b'test fixture')
                else: shutil.copyfile(ROOT / 'web' / name, target)
            for name in ('README.md', 'PRIVACY.md', 'privacy.py', 'site/index.html'):
                target = root / name; target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, target)
            (root / 'dist').mkdir()
            bundle = root / 'dist' / 'dangbro-offline.zip'; bundle.write_bytes(b'opaque offline fixture')
            before = {p.relative_to(root): p.read_bytes() for p in (root / 'web').rglob('*') if p.is_file()}
            output = build_pages.build(root)
            for name, data in before.items(): self.assertEqual((root / name).read_bytes(), data)
            self.assertEqual((output / 'downloads' / bundle.name).read_bytes(), bundle.read_bytes())
            self.assertIn(hashlib.sha256(bundle.read_bytes()).hexdigest(), (output / 'downloads' / 'SHA256SUMS').read_text())
            parser = Links(); parser.feed((output / 'index.html').read_text())
            for link in parser.links:
                parsed = urlsplit(link)
                if not parsed.scheme and parsed.path:
                    target = output / unquote(parsed.path)
                    self.assertTrue(target.exists(), link)
            source = (output / 'online' / 'resources' / 'root_persistence.sh').read_text()
            self.assertNotIn('http://10.', source)
            self.assertIn('https://sectumsempra82.github.io/dangbro/online/resources/' + IPK, source)
            self.assertNotIn('paste.rs', source)
            subprocess.run(['sh', '-n', str(output / 'online' / 'resources' / 'root_persistence.sh')], check=True)
            generated = output / 'online' / 'local-url.js'
            script = '''const fs = require('node:fs'); const assert = require('node:assert/strict');
(async () => {
const {localTarget} = await import('data:text/javascript;base64,' + fs.readFileSync(process.argv[1]).toString('base64'));
assert.equal(localTarget('https://sectumsempra82.github.io/dangbro/online/'), 'https://sectumsempra82.github.io/dangbro/online/resources/dangbro/');
for (const url of ['https://evil.example/dangbro/online/', 'http://sectumsempra82.github.io/dangbro/online/', 'https://sectumsempra82.github.io/other/', 'http://localhost/']) assert.throws(() => localTarget(url));
})().catch(e => { console.error(e); process.exit(1); });'''
            subprocess.run(['node', '-e', script, str(generated)], check=True)

    def test_source_drift_stops_build_instead_of_relaxing_url_checks(self):
        with self.assertRaises(ValueError): build_pages.replace_once('changed source', 'expected guard', 'replacement')
        with self.assertRaises(ValueError): build_pages.replace_once('xx', 'x', 'replacement')

if __name__ == '__main__': unittest.main()
