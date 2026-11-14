import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

test('store keeps records and idempotent response independently', async () => {
  const temporaryDirectory = fs.mkdtempSync(path.join(os.tmpdir(), 'mathcourses-'));
  process.env.DATA_DIR = temporaryDirectory;
  const { createStore } = await import(`../shared/store.js?test=${Date.now()}`);
  const store = createStore('unit');
  store.put({ id: 'course-1', title: 'Геометрия' });
  store.remember('fixed-key', { id: 'enr-1', status: 'PENDING_PAYMENT' });
  assert.equal(store.get('course-1').title, 'Геометрия');
  assert.equal(store.idempotent('fixed-key').id, 'enr-1');
});

test('Problem Details has one predictable format', async () => {
  const { problem } = await import('../shared/http.js');
  const result = problem(409, 'Конфликт', 'Курс недоступен');
  assert.deepEqual(Object.keys(result).sort(), ['detail', 'status', 'title', 'traceId', 'type']);
  assert.equal(result.status, 409);
  assert.match(result.type, /http-409$/);
});
