import express from 'express';
import { createStore } from '../../shared/store.js';
import { page, requireIdempotency, sendProblem } from '../../shared/http.js';
import { createEventBus } from '../../shared/events.js';
import { id } from '../../shared/ids.js';

const app = express(); app.use(express.json());
const store = createStore('enrollment'); const bus = await createEventBus('enrollment-service');
const catalogUrl = process.env.CATALOG_URL || 'http://catalog-service:3001';

async function setStatus(enrollment, status, eventType) {
  const updated = store.update(enrollment.id, { status });
  await bus.publish(eventType, { enrollmentId: updated.id, studentId: updated.studentId, courseId: updated.courseId }, enrollment.correlationId);
  return updated;
}
await bus.subscribe(['payment.succeeded', 'payment.failed', 'payment.refunded'], async (event) => {
  if (store.processed(event.eventId)) return; store.markProcessed(event.eventId);
  const enrollment = store.get(event.payload.enrollmentId); if (!enrollment) return;
  if (event.eventType === 'payment.succeeded' && enrollment.status === 'PENDING_PAYMENT') await setStatus(enrollment, 'ACTIVE', 'enrollment.activated');
  if (event.eventType === 'payment.failed' && enrollment.status === 'PENDING_PAYMENT') await setStatus(enrollment, 'CANCELLED', 'enrollment.cancelled');
  if (event.eventType === 'payment.refunded') store.update(enrollment.id, { status: 'CANCELLED' });
});
app.get('/health', (_req, res) => res.json({ status: 'online', service: 'enrollment-service' }));
app.get('/api/v1/enrollments', (req, res) => res.json(page(store.all(), req)));
for (const path of ['/api/v1/enrollments/:enrollmentId', '/internal/v1/enrollments/:enrollmentId']) app.get(path, (req, res) => {
  const enrollment = store.get(req.params.enrollmentId); return enrollment ? res.json(enrollment) : sendProblem(res, 404, 'Не найдено', 'Запись не найдена');
});
app.post('/api/v1/enrollments', requireIdempotency, async (req, res) => {
  const key = req.get('Idempotency-Key'); if (store.idempotent(key)) return res.status(201).json(store.idempotent(key));
  if (!req.body.courseId) return sendProblem(res, 400, 'Некорректный запрос', 'Требуется courseId');
  const courseResponse = await fetch(`${catalogUrl}/internal/v1/courses/${req.body.courseId}`);
  if (!courseResponse.ok) return sendProblem(res, 409, 'Конфликт', 'Курс недоступен для записи');
  const course = await courseResponse.json(); if (course.status !== 'PUBLISHED') return sendProblem(res, 409, 'Конфликт', 'Курс не опубликован');
  const enrollment = store.put({ id: id('enr'), courseId: course.id, studentId: 'student-7', priceRub: course.priceRub, status: 'PENDING_PAYMENT', correlationId: crypto.randomUUID() }); store.remember(key, enrollment);
  await bus.publish('enrollment.created', { enrollmentId: enrollment.id, courseId: course.id, studentId: enrollment.studentId, amountRub: enrollment.priceRub }, enrollment.correlationId);
  res.status(201).json(enrollment);
});
app.post('/internal/v1/enrollments/:enrollmentId/activate', requireIdempotency, async (req, res) => { const enrollment = store.get(req.params.enrollmentId); if (!enrollment) return sendProblem(res, 404, 'Не найдено', 'Запись не найдена'); res.json(await setStatus(enrollment, 'ACTIVE', 'enrollment.activated')); });
app.post('/internal/v1/enrollments/:enrollmentId/cancel', requireIdempotency, async (req, res) => { const enrollment = store.get(req.params.enrollmentId); if (!enrollment) return sendProblem(res, 404, 'Не найдено', 'Запись не найдена'); res.json(await setStatus(enrollment, 'CANCELLED', 'enrollment.cancelled')); });
app.listen(process.env.PORT || 3002, '0.0.0.0', () => console.log('enrollment-service started'));
