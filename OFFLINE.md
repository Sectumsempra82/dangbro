# Root over your LAN, with the TV's Internet access blocked

Prepare the files on a computer, start a local server, and open the printed
address in that computer's browser. The TV downloads the root script and Homebrew
Channel from that computer. No account, Python packages, or TV Internet access
are required for this workflow.

## Quick start

Requirements: Python 3.10 or newer on the computer, a supported DVB-tuner TV, and
both devices on the same trusted LAN. These steps do not broaden DangBro's
firmware compatibility.

1. Download and extract this repository on a computer.
2. In its directory, prepare the pinned Homebrew Channel package:

   ```sh
   python3 tools/prepare.py --bundle
   ```

   This step downloads Homebrew Channel **0.7.3** from its official GitHub release
   on the **computer only**. It verifies the package's SHA-256 and creates
   `dist/dangbro-offline.zip`. You can transfer that ZIP to a disconnected computer
   and extract it there. It already contains the required files.

   If you already have the official package, prepare without any network request:

   ```sh
   python3 tools/prepare.py --ipk /path/to/org.webosbrew.hbchannel_0.7.3_all.ipk --bundle
   ```

3. Block the TV's Internet access at the router while allowing local connections.
   Find the **computer's** LAN IPv4 address in its network settings, then run:

   ```sh
   python3 serve.py --host 192.168.1.10
   ```

   Replace `192.168.1.10` with the computer's address. On Windows, use
   `py -3` instead of `python3` if that is how Python is installed.

4. Open the exact address printed by the server, for example
   `http://192.168.1.10:8000/?offline`, in the **computer's browser**. Enter the
   **TV's** IP, connect, and accept the pairing prompt on the TV.
5. Follow the TV's result dialog. Disable Quick Start+, reboot, and confirm
   **Root OK** in Homebrew Channel. Stop the computer's server with **Ctrl+C**.

Do not open `index.html` directly or substitute `localhost` for the printed URL:
the TV would interpret localhost as itself. The server accepts only a private
IPv4 interface (`10.x.x.x`, `172.16–31.x.x`, or `192.168.x.x`). IPv6, public IPs,
hostnames, and HTTPS local servers are not supported by this offline workflow.

## What stays local

- `serve.py` serves only the browser application under `docs/`, validates all
  required assets and the IPK checksum before listening, and never downloads
  missing files. It rejects directory listings, hidden files, symlinks, path
  traversal, and requests for an unexpected Host.
- Local HTTP automatically selects offline mode. The explicit `?offline` flag
  also travels to the TV's overlay. Script and IPK URLs use the same LAN origin.
- The TV checks the IPK checksum before installation. Offline IPK requests do not
  follow redirects, use a proxy, or fall back to a public download.
- `?offline&debug` enables browser diagnostics while keeping the root log at
  `/tmp/dangbro-root.log` on the TV. Offline mode never uploads that log to paste.rs.
- The ZIP contains an explicit list of application files, instructions, tools,
  and the pinned IPK; it excludes Git metadata and unrelated local files.

This controls **DangBro's offline workflow**, not the TV's other services. Keep a
router WAN block if you want to ensure the TV cannot reach the Internet. Local
HTTP assumes a trusted LAN; the checksum checks the expected IPK, but does not
authenticate the whole local HTTP connection. Use a private network, permit the
server through the computer's firewall only there, and do not forward its port.

The existing hosted HTTPS workflow is unchanged. This feature adds no Pages
deployment or hosted service.

## Troubleshooting

| Symptom | Check |
|---|---|
| Server refuses to start | Prepare the assets first; a missing or wrong IPK is an error, never a download fallback. |
| TV shows a network error immediately | Use the computer's printed LAN address, not localhost. Check the firewall and disable Wi-Fi client isolation. Keep LAN access allowed in the router's TV block. |
| WSS connection fails | Open `https://TV-IP:3001/` on the computer and accept the certificate exception for your own TV, then retry. The bundled browser guide is available without Internet. |
| Local network permission prompt | Allow the browser to reach your TV on the local network. Browser permission requirements still apply when self-hosting. |
| Package checksum fails | Use the official 0.7.3 IPK; do not bypass the check. Re-copy or re-download it on the preparation computer. |
| Rooting fails | Inspect `/tmp/dangbro-root.log` locally and redact device details before choosing to share it. |

Pinned package SHA-256:

```text
d10bf3c753551d7c72fb7a92b20fcd2317e502a220ac668ba8e76f6ea78b363c
```

## Validation and maintenance

Run the host-side checks without a TV or downloaded IPK:

```sh
python3 -m unittest discover -s tests -v
node --test tests/local-url.test.mjs
sh -n docs/resources/root_persistence.sh
git diff --check
```

Node 20 or newer is needed only for tests. Tests cover local URL propagation,
hosted-flow compatibility, package validation, local HTTP restrictions, and
offline download/log-upload failures using simulated TV services. They do not
prove compatibility with a particular firmware.

For a hardware check, keep the TV's WAN blocked, complete the LAN flow, confirm
Root OK after a reboot, and check the server log for the overlay, root script,
and IPK requests (an existing Homebrew installation can skip the IPK download).
Also check that debug failure reporting leaves the log on the TV.

When updating Homebrew, review and update the filename/version and SHA-256 in
`tools/offline.py`, the browser preflight, the overlay, and the root script
together. Verify the official artifact before changing the pin.
