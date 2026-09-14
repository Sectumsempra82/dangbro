import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
const source = fs.readFileSync(new URL('../docs/local-url.js', import.meta.url), 'utf8');
const { localTarget } = await import('data:text/javascript;base64,' + Buffer.from(source).toString('base64'));
test('TV uses LAN computer and preserves subdirectory and port', () => {
  assert.equal(localTarget('http://192.168.1.10:8000/'), 'http://192.168.1.10:8000/resources/dangbro/?offline');
  assert.equal(localTarget('http://10.0.0.2:8001/dangbro/index.html', true), 'http://10.0.0.2:8001/dangbro/resources/dangbro/?offline&debug');
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
const overlay = fs.readFileSync(new URL('../docs/resources/dangbro/index.html', import.meta.url), 'utf8').match(/<script>([\s\S]*?)<\/script>/)[1];
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
  assert.ok(command.includes('DANGBRO_OFFLINE=1${IFS}'));
  assert.ok(command.includes('IPK_URL=http://192.168.1.10:8000/resources/org.webosbrew.hbchannel_0.7.3_all.ipk${IFS}'));
  assert.ok(!command.includes('UPLOAD_LOG'));
});

test('hosted overlay retains its original script source and opt-in debug upload', () => {
  for (const debug of [false, true]) {
    const { calls, bridges } = runOverlay('https://azoffshowy.github.io/dangbro/resources/dangbro/' + (debug ? '?debug' : ''));
    assert.equal(calls[0].payload.target, 'https://azoffshowy.github.io/dangbro/resources/root_persistence.sh');
    bridges[0].onservicecallback(JSON.stringify({ ticket: 1 }));
    bridges[1].onservicecallback(JSON.stringify({ completed: true }));
    bridges[2].onservicecallback(JSON.stringify({ configs: { 'tv.nyx.tvBroadcastSystem': 'DVB' } }));
    const command = calls.at(-1).payload.data;
    assert.equal(command.includes('UPLOAD_LOG=1'), debug);
    assert.ok(!command.includes('DANGBRO_OFFLINE'));
    assert.ok(!command.includes('IPK_URL='));
  }
});

const frontend = fs.readFileSync(new URL('../docs/dangbro.js', import.meta.url), 'utf8')
  .replace("import { localTarget } from './local-url.js';", '');
async function connectFrontend(href, available = true) {
  const elements = new Map();
  const requests = [];
  const connections = [];
  const location = new URL(href);
  const context = vm.createContext({ URL, URLSearchParams, EventTarget, localTarget,
    window: { location }, setTimeout() {},
    localStorage: { getItem: () => '', setItem() {} },
    fetch: async (url, options) => { requests.push({ url: url.toString(), options }); return { ok: available }; },
    document: { getElementById(id) {
      if (!elements.has(id)) elements.set(id, { value: id === 'tvIp' ? '192.168.1.50' : '', textContent: '', addEventListener() {} });
      return elements.get(id);
    } }
  });
  vm.runInContext(frontend + '\nglobalThis.testApi = { bridge, startConnect, getTarget: () => targetUrl };', context);
  context.testApi.bridge.disconnect = () => {};
  context.testApi.bridge.connect = async (ip) => connections.push(ip);
  await context.testApi.startConnect();
  return { requests, connections, target: context.testApi.getTarget(), log: elements.get('log').textContent };
}

test('frontend checks both LAN assets before connecting and propagates offline debug mode', async () => {
  const result = await connectFrontend('http://192.168.1.10:8000/?offline&debug');
  assert.equal(result.target, 'http://192.168.1.10:8000/resources/dangbro/?offline&debug');
  assert.deepEqual(result.connections, ['192.168.1.50']);
  assert.deepEqual(result.requests.map(r => r.url), [
    'http://192.168.1.10:8000/resources/root_persistence.sh',
    'http://192.168.1.10:8000/resources/org.webosbrew.hbchannel_0.7.3_all.ipk'
  ]);
  assert.ok(result.requests.every(r => r.options.method === 'HEAD'));
  assert.ok(!result.log.includes('log upload enabled'));
});

test('missing local asset or invalid local origin prevents any TV connection', async () => {
  const missing = await connectFrontend('http://192.168.1.10:8000/', false);
  assert.deepEqual(missing.connections, []);
  assert.match(missing.log, /Missing local asset/);
  for (const href of ['http://localhost:8000/', 'https://example.com/?offline']) {
    const invalid = await connectFrontend(href);
    assert.deepEqual(invalid.requests, []);
    assert.deepEqual(invalid.connections, []);
    assert.match(invalid.log, /Open the LAN URL/);
  }
});

test('hosted frontend retains target and does not require a local IPK', async () => {
  const result = await connectFrontend('https://azoffshowy.github.io/dangbro/?debug', false);
  assert.deepEqual(result.requests, []);
  assert.deepEqual(result.connections, ['192.168.1.50']);
  assert.equal(result.target, 'https://azoffshowy.github.io/dangbro/resources/dangbro/?debug');
  assert.match(result.log, /log upload enabled/);
});
test('overlay rejects external origins and shell metacharacters before any bridge call', () => {
  for (const href of ['http://localhost:8000/resources/dangbro/', 'https://example.com/resources/dangbro/?offline',
    'http://192.168.1.10/evil;command/resources/dangbro/']) {
    assert.throws(() => runOverlay(href));
  }
});
