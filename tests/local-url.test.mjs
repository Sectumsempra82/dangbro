import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
const source = fs.readFileSync(new URL('../web/local-url.js', import.meta.url), 'utf8');
const { localTarget } = await import('data:text/javascript;base64,' + Buffer.from(source).toString('base64'));
test('TV uses LAN computer and preserves subdirectory and port', () => {
  assert.equal(localTarget('http://192.168.1.10:8000/'), 'http://192.168.1.10:8000/resources/dangbro/');
  assert.equal(localTarget('http://10.0.0.2:8001/dangbro/index.html', true), 'http://10.0.0.2:8001/dangbro/resources/dangbro/?debug');
});
test('reject localhost, public origins and file URLs', () => {
  for (const origin of ['http://localhost:8000/', 'http://127.0.0.1:8000/', 'http://0.0.0.0/',
    'http://8.8.8.8/', 'https://example.com/', 'file:///tmp/index.html', 'http://user:pass@192.168.1.2/']) {
    assert.throws(() => localTarget(origin));
  }
});
test('private 172 range has correct boundaries', () => {
  assert.throws(() => localTarget('http://172.15.0.1/'));
  assert.throws(() => localTarget('http://172.32.0.1/'));
  assert.ok(localTarget('http://172.16.0.1/'));
  assert.ok(localTarget('http://172.31.0.1/'));
});

import vm from 'node:vm';
const overlay = fs.readFileSync(new URL('../web/resources/dangbro/index.html', import.meta.url), 'utf8').match(/<script>([\s\S]*?)<\/script>/)[1];
function runOverlay(href) {
  const calls = [];
  const bridges = [];
  const location = new URL(href);
  function PalmServiceBridge() {
    bridges.push(this);
    this.call = (uri, payload) => calls.push({ uri, payload: JSON.parse(payload) });
  }
  const context = { URL, URLSearchParams, window: { location, PalmServiceBridge },
    document: { getElementById: () => ({}) } };
  vm.runInNewContext(overlay, context);
  return { calls, bridges, context };
}
test('complete overlay flow keeps script and IPK on same LAN origin, including debug', () => {
  const { calls, bridges } = runOverlay('http://192.168.1.10:8000/resources/dangbro/?debug');
  assert.equal(calls[0].payload.target, 'http://192.168.1.10:8000/resources/root_persistence.sh');
  bridges[0].onservicecallback(JSON.stringify({ ticket: 1, returnValue: true }));
  bridges[1].onservicecallback(JSON.stringify({ completed: true, returnValue: true }));
  bridges[2].onservicecallback(JSON.stringify({ returnValue: false }));
  const command = calls.at(-1).payload.data;
  assert.ok(command.includes('IPK_URL=http://192.168.1.10:8000/resources/org.webosbrew.hbchannel_0.7.3_all.ipk${IFS}'));
  assert.ok(!command.includes('UPLOAD_LOG'));
});
test('overlay rejects external origins and shell metacharacters before any bridge call', () => {
  for (const href of ['http://localhost:8000/resources/dangbro/', 'https://example.com/resources/dangbro/',
    'http://192.168.1.10/evil;command/resources/dangbro/']) {
    assert.throws(() => runOverlay(href));
  }
});
