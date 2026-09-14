#!/usr/bin/env python3
"""Build the offline-download and documentation site."""
from pathlib import Path
import hashlib
import shutil
from offline import ROOT, check_assets


def build(root=ROOT):
    root = Path(root)
    output = root / 'dist' / 'pages'
    if output.exists():
        shutil.rmtree(output)
    downloads = output / 'downloads'
    downloads.mkdir(parents=True)
    shutil.copyfile(root / 'site' / 'index.html', output / 'index.html')
    for name in ['README.md', 'PRIVACY.md', 'privacy.py']:
        shutil.copyfile(root / name, downloads / name)
    bundle = root / 'dist' / 'dangbro-offline.zip'
    shutil.copyfile(bundle, downloads / bundle.name)
    digest = hashlib.sha256(bundle.read_bytes()).hexdigest()
    (downloads / 'SHA256SUMS').write_text(digest + '  ' + bundle.name + '\n')
    (output / '.nojekyll').touch()
    return output


if __name__ == '__main__':
    check_assets()
    print(build())
