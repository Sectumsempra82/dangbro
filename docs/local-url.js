export function localTarget(href, debug = false) {
  const origin = new URL(href);
  const octets = origin.hostname.split('.').map(Number);
  const privateIP = octets.length === 4 && octets.every(n => Number.isInteger(n) && n >= 0 && n <= 255) &&
    (octets[0] === 10 || (octets[0] === 172 && octets[1] >= 16 && octets[1] <= 31) ||
      (octets[0] === 192 && octets[1] === 168));
  if (origin.protocol !== 'http:' || !privateIP || origin.username || origin.password) {
    throw new Error('Open the LAN URL printed by serve.py. localhost points back to the TV, not this computer.');
  }
  return new URL('./resources/dangbro/' + (debug ? '?offline&debug' : '?offline'), origin).toString();
}
