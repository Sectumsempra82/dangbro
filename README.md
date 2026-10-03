# 📺 DangBro

**Root locally. Make yourself at home.**

Bring Homebrew to your LG TV without giving it Internet access. Prepare the files on your computer and run the rooting workflow over your own LAN.

Built on [azoffshowy/dangbro](https://github.com/azoffshowy/dangbro), with offline preparation, local serving and portable packaging added.

For privacy controls after rooting, see the separate [PWN-your-glass project](https://github.com/Sectumsempra82/PWN-your-glass). Its supported models and validation limits are documented there.

## ⚡ TL;DR — get to the good part

- **Root over LAN.** The TV can stay blocked from the Internet throughout setup.
- **Pack it and go.** One ZIP contains the website, root script and verified Homebrew package. Logs stay local.

On your computer, with **Python 3.10+**:

```sh
python3 tools/prepare.py --bundle
python3 serve.py --host 192.168.1.10
```

**Replace `192.168.1.10` with your computer's LAN IPv4 address.** The first command downloads the package on the computer; already have it? [Prepare offline instead](#1-prepare-once-on-a-computer).

Open the printed URL → enter the **TV's** IP → accept pairing → wait for success → disable **Quick Start+** → reboot → confirm **Root OK** in Homebrew Channel.

> Rooting needs a vulnerable DVB-tuner webOS build. Check your model and firmware before running the local workflow.

**[Offline setup ↓](#1-prepare-once-on-a-computer) · [Recovery ↓](#recovery-and-troubleshooting)**

Get the complete bundle from the [offline download site](https://sectumsempra82.github.io/dangbro/). Run the launcher on your own computer; this fork is **offline-use only**.

## 🧰 What's in the box?

| Piece | What it does |
| --- | --- |
| `serve.py` | Serves the rooting files from your computer's LAN address. |
| `tools/prepare.py` | Verifies the pinned Homebrew package and builds a portable offline ZIP. |

No runtime CDN dependencies, external package downloads, or automatic log uploads. **LAN access is still required.** Existing TV firmware/apps may independently attempt Internet connections, so block the TV's WAN access at your router during setup while allowing LAN traffic.

## 1. Prepare once on a computer

Requires Python 3.10+ on macOS, Linux or Windows (use `py -3` instead of `python3` on Windows if needed). No pip, npm, account or cloud server is needed.

```sh
python3 tools/prepare.py --bundle
```

This downloads **Homebrew Channel 0.7.3** from its official GitHub release, checks a pinned SHA-256, and produces `dist/dangbro-offline.zip`. Only this preparation computer needs Internet. Transfer the ZIP to the offline computer and extract it, or continue using this checkout.

Already have the package? Preparation can also be completely offline:

```sh
python3 tools/prepare.py --ipk /path/to/org.webosbrew.hbchannel_0.7.3_all.ipk --bundle
```

The expected SHA-256 is `d10bf3c753551d7c72fb7a92b20fcd2317e502a220ac668ba8e76f6ea78b363c`. A different package is rejected. Do not substitute another version without reviewing the installer and updating the pin.

## 2. Root with the TV offline

1. Keep the TV and computer on the same LAN. Block only the TV's Internet access at the router; a rule that also blocks LAN traffic will prevent setup.
2. Find the computer's private IPv4 address in its network settings. Start the server with **that computer address**, not the TV address:

   ```sh
   python3 serve.py --host 192.168.1.10
   ```

   The address above is an example. Use `--port 8001` if port 8000 is occupied.
3. Open the exact LAN URL printed by the server on the computer. **Do not use `localhost` or `127.0.0.1`.** Those addresses refer to the TV itself when passed to the overlay app.
4. Enter the TV's LAN IPv4 address, connect, and accept its pairing prompt. If needed, first open `https://TV-IP:3001/` and accept your TV's self-signed certificate exception. [Local connection help](web/help.html) is included in the bundle.
5. Leave the computer/server running until the TV reports success. DangBro establishes root, installs Homebrew Channel, and removes the Developer Mode app if installed, following upstream's persistence workflow.
6. Disable **Quick Start+**, reboot the TV, and confirm **Root OK** in Homebrew Channel. Stop the server with Ctrl+C afterward.

The server binds only the selected LAN interface and serves only `web/`; it rejects directory listings, hidden paths and symlinks. Keep it on a trusted LAN and do not expose it through router port forwarding. HTTP is needed by this workflow; the pinned IPK checksum detects package corruption but does not authenticate every exploit asset against a hostile LAN peer.

Upstream targets vulnerable **DVB-tuner webOS 7.x through webOS 25** builds. Patched firmware or a missing `dangbei-overlay`/legacy-broadcast path will not work. This is upstream's compatibility claim, not a guarantee that every model was tested here.

## Recovery and troubleshooting

- **Root error:** inspect `/tmp/dangbro-root.log` locally. Debug mode does not upload it.
- **IPK error -5:** check the TV's date/time; an incorrect clock can prevent installation.

## GitHub Pages

GitHub Pages provides the offline rooting ZIP and setup instructions. It adds no analytics, external fonts or log uploads. Download the bundle on your computer and run it locally; the TV fetches rooting files only from your LAN server.

```sh
python3 tools/prepare.py --bundle
python3 tools/build_pages.py
```

The output is `dist/pages/`. Only that directory is uploaded by `.github/workflows/pages.yml`, using the [official Pages Actions workflow](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages). Set repository **Settings → Pages → Source → GitHub Actions**, then publish the changes to `main` or manually run the workflow. The workflow runs tests before building and deploying.

The download site is `https://sectumsempra82.github.io/dangbro/`. The builder publishes only the landing page and an explicit list of downloads. Launcher assets stay inside the offline ZIP and run on your computer. For another fork/domain, update the landing page and documentation links.

## Development and credits

```sh
python3 -m unittest discover -s tests -v
node --test tests/local-url.test.mjs
sh -n web/resources/root_persistence.sh
```

Runtime website assets live under `web/` (moved from upstream `docs/`). `AGENTS.md`, local `docs/`, notebook files, generated IPKs and `dist/` are ignored. GitHub Pages is optional; the local workflow does not depend on it.

Root exploit: [azoffshowy/dangbro](https://github.com/azoffshowy/dangbro). Persistence and Homebrew package: [webosbrew/webos-homebrew-channel](https://github.com/webosbrew/webos-homebrew-channel), especially [v0.7.3 startup behavior](https://github.com/webosbrew/webos-homebrew-channel/blob/v0.7.3/services/startup.sh). SSAP proxy approach: [Informatic/webos-ssap-web](https://github.com/Informatic/webos-ssap-web). Existing upstream credits are retained. Upstream supplied no top-level license file; this fork does not invent a license for upstream code or the separately downloaded Homebrew artifact.
