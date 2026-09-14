#!/usr/bin/env python3
"""Build the Pages hub and a hosted launcher without changing offline assets."""
from pathlib import Path
import hashlib
import shutil
from offline import ROOT, ASSETS, IPK, check_assets

PAGES_ORIGIN = 'https://sectumsempra82.github.io'
PAGES_PATH = '/dangbro/online/'


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('Upstream source changed; review hosted transformation: ' + old[:70])
    return text.replace(old, new, 1)


def build(root=ROOT):
    root = Path(root)
    output = root / 'dist' / 'pages'
    if output.exists():
        shutil.rmtree(output)
    online = output / 'online'
    downloads = output / 'downloads'
    downloads.mkdir(parents=True)
    for name in ASSETS + ['resources/' + IPK]:
        source = root / 'web' / name
        if source.is_symlink() or not source.is_file():
            raise ValueError('Missing or symlinked asset: ' + name)
        destination = online / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    shutil.copyfile(root / 'site' / 'index.html', output / 'index.html')
    for name in ['README.md', 'PRIVACY.md', 'privacy.py']:
        shutil.copyfile(root / name, downloads / name)
    bundle = root / 'dist' / 'dangbro-offline.zip'
    shutil.copyfile(bundle, downloads / bundle.name)
    digest = hashlib.sha256(bundle.read_bytes()).hexdigest()
    (downloads / 'SHA256SUMS').write_text(digest + '  ' + bundle.name + '\n')
    (output / '.nojekyll').touch()

    # Hosted behavior exists only in the generated online/ copy. The offline ZIP stays LAN-only.
    (online / 'local-url.js').write_text('''export function localTarget(href, debug = false) {
  const origin = new URL(href);
  if (origin.origin !== "''' + PAGES_ORIGIN + '''" ||
      !origin.pathname.startsWith("''' + PAGES_PATH + '''") || origin.username || origin.password) {
    throw new Error('Open the official HTTPS Pages launcher, or use the separate offline bundle.');
  }
  return new URL('./resources/dangbro/' + (debug ? '?debug' : ''), origin).toString();
}
''')
    index = online / 'index.html'
    index.write_text(replace_once(index.read_text(),
        'Local mode: all rooting files come from this computer. The TV only needs LAN access.',
        'Online mode: the computer and TV fetch rooting files from GitHub Pages. Both need Internet access. '
        '<a href="../">Prefer offline? Download the LAN bundle.</a>'))
    script = online / 'dangbro.js'
    script.write_text(replace_once(script.read_text(),
        "'. Run tools/prepare.py first.'", "'. The hosted build may be incomplete; use the offline bundle.'"))
    overlay = online / 'resources' / 'dangbro' / 'index.html'
    source = overlay.read_text()
    line = next(line for line in source.splitlines() if line.strip().startswith('if (!/^http:'))
    expected = PAGES_ORIGIN + PAGES_PATH + 'resources/' + IPK
    source = replace_once(source, line, '    if (ipkTarget !== ' + repr(expected) + ') {')
    source = replace_once(source, 'Use the local server with a private LAN IPv4 address.',
                          'Open the official HTTPS Pages launcher or use the separate offline bundle.')
    overlay.write_text(source)
    persistence = online / 'resources' / 'root_persistence.sh'
    source = persistence.read_text()
    source = replace_once(source, '        http://10.*/*|http://192.168.*/*|http://172.*/*) ;;',
                          '        ' + expected + ') ;;')
    source = replace_once(source, 'Missing local Homebrew package URL', 'Unexpected hosted Homebrew package URL')
    persistence.write_text(source)
    help_page = online / 'help.html'
    source = help_page.read_text()
    source = replace_once(source,
        'Keep the server running. Open the exact http://LAN-IP:PORT/ address printed by serve.py on your computer. Do not use localhost: the TV would then try to download from itself.',
        'Open the hosted launcher on your computer. Both the computer and TV need Internet access to download files from GitHub Pages. The offline ZIP is available from the site home page.')
    source = replace_once(source, 'The TV does not need Internet access.', 'Online mode requires TV Internet access.')
    help_page.write_text(source)
    return output


if __name__ == '__main__':
    check_assets()
    print(build())
