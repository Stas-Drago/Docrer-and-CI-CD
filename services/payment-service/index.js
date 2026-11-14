import express from 'express';
import { createStore } from '../../shared/store.js';
import { requireIdempotency, sendProblem } from '../../shared/http.js';
import { createEventBus } from '../../shared/events.js';
import { id } from '../../shared/ids.js';

const app = express(); app.use(express.json());
const store = createStore('payment'); const bus = await createEventBus('payment-service');
const mode = process.env.PAYMENT_MODE || 'success';
async function charge({ enrollmentId, amountRub, correlationId }) {
  const payment = store.put({ id: id('pay'), enrollmentId, amountRub, status: 'PENDING', correlationId });
  const succeeded = mode !== 'fail'; const status = succeeded ? 'SUCCEEDED' : 'FAILED'; store.update(payment.id, { status });
  await bus.publish(succeeded ? 'payment.succeeded' : 'payment.failed', succeeded ? { enrollmentId, paymentId: payment.id } : { enrollmentId, reason: 'payment gateway declined' }, correlationId);
  return store.get(payment.id);
}
await bus.subscribe(['enrollment.created'], async (event) => { if (store.processed(event.eventId)) return; store.markProcessed(event.eventId); await charge({ ...event.payload, correlationId: event.correlationId }); });
app.get('/health', (_req, res) => res.json({ status: 'online', service: 'payment-service', mockGatewayMode: mode }));
for (const path of ['/api/v1/payments/:paymentId', '/internal/v1/payments/:paymentId']) app.get(path, (req, res) => { const payment = store.get(req.params.paymentId); return payment ? res.json(payment) : sendProblem(res, 404, 'Не найдено', 'Платёж не найден'); });
app.post('/internal/v1/payments', requireIdempotency, async (req, res) => { const key = req.get('Idempotency-Key'); if (store.idempotent(key)) return res.status(201).json(store.idempotent(key)); if (!req.body.enrollmentId || !Number.isInteger(req.body.amountRub)) return sendProblem(res, 400, 'Некорректный запрос', 'Требуются enrollmentId и amountRub'); const payment = await charge(req.body); store.remember(key, payment); res.status(201).json(payment); });
app.post('/internal/v1/payments/:paymentId/refund', requireIdempotency, async (req, res) => { const payment = store.get(req.params.paymentId); if (!payment) return sendProblem(res, 404, 'Не найдено', 'Платёж не найден'); if (payment.status !== 'SUCCEEDED') return sendProblem(res, 409, 'Конфликт', 'Возврат возможен только для успешного платежа'); const refunded = store.update(payment.id, { status: 'REFUNDED' }); await bus.publish('payment.refunded', { enrollmentId: payment.enrollmentId, paymentId: payment.id }, payment.correlationId); res.json(refunded); });
app.listen(process.env.PORT || 3003, '0.0.0.0', () => console.log('payment-service started'));
