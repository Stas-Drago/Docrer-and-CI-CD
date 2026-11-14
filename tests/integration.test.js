import test from 'node:test';
import assert from 'node:assert/strict';

const baseUrl = process.env.GATEWAY_URL || 'http://localhost:8081';
const enabled = process.env.RUN_INTEGRATION === '1';
const delay = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));

test('gateway exposes courses and completes the payment saga', { skip: !enabled }, async () => {
  const courses = await fetch(`${baseUrl}/api/v1/courses`).then((response) => response.json());
  assert.equal(courses.items[0].id, 'course-101');
  const key = crypto.randomUUID();
  const created = await fetch(`${baseUrl}/api/v1/enrollments`, {
    method: 'POST', headers: { 'Content-Type': 'application/json', 'Idempotency-Key': key }, body: JSON.stringify({ courseId: 'course-101' })
  });
  assert.equal(created.status, 201);
  const enrollment = await created.json();
  let current = enrollment;
  for (let attempt = 0; attempt < 20 && current.status !== 'ACTIVE'; attempt += 1) {
    await delay(500);
    current = await fetch(`${baseUrl}/api/v1/enrollments/${enrollment.id}`).then((response) => response.json());
  }
  assert.equal(current.status, 'ACTIVE');
  const repeated = await fetch(`${baseUrl}/api/v1/enrollments`, {
    method: 'POST', headers: { 'Content-Type': 'application/json', 'Idempotency-Key': key }, body: JSON.stringify({ courseId: 'course-101' })
  }).then((response) => response.json());
  assert.equal(repeated.id, enrollment.id);
});

test('gateway returns Problem Details for an unavailable course', { skip: !enabled }, async () => {
  const response = await fetch(`${baseUrl}/api/v1/enrollments`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Idempotency-Key': crypto.randomUUID() },
    body: JSON.stringify({ courseId: 'course-does-not-exist' })
  });
  assert.equal(response.status, 409);
  const error = await response.json();
  assert.equal(error.title, 'Конфликт');
  assert.equal(error.status, 409);
  assert.match(error.type, /http-409$/);
});
