import express from 'express';
import { createStore } from '../../shared/store.js';
import { page, sendProblem } from '../../shared/http.js';
import { createEventBus } from '../../shared/events.js';
import { id } from '../../shared/ids.js';

const app = express(); app.use(express.json());
const store = createStore('notification'); const bus = await createEventBus('notification-service');
await bus.subscribe(['enrollment.activated', 'enrollment.cancelled', 'payment.refunded'], async (event) => {
  if (store.processed(event.eventId)) return; store.markProcessed(event.eventId);
  const notification = store.put({ id: id('ntf'), enrollmentId: event.payload.enrollmentId, recipientId: event.payload.studentId || 'student-7', kind: event.eventType, status: 'SENT', deliveredBy: 'email mock' });
  console.log(`notification-service: mock email sent ${notification.kind}`);
});
app.get('/health', (_req, res) => res.json({ status: 'online', service: 'notification-service', emailProvider: 'mock' }));
app.get('/api/v1/notifications', (req, res) => res.json(page(store.all(), req)));
for (const path of ['/api/v1/notifications/:notificationId', '/internal/v1/notifications/:notificationId']) app.get(path, (req, res) => { const notification = store.get(req.params.notificationId); return notification ? res.json(notification) : sendProblem(res, 404, 'Не найдено', 'Уведомление не найдено'); });
app.listen(process.env.PORT || 3004, '0.0.0.0', () => console.log('notification-service started'));
