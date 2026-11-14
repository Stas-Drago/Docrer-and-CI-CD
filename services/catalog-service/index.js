import express from 'express';
import { createStore } from '../../shared/store.js';
import { page, requireIdempotency, sendProblem } from '../../shared/http.js';
import { createEventBus } from '../../shared/events.js';
import { id } from '../../shared/ids.js';

const app = express(); app.use(express.json());
const store = createStore('catalog'); const bus = await createEventBus('catalog-service');
if (!store.all().length) store.put({ id: 'course-101', title: 'Алгебра для ЕГЭ', priceRub: 2490, status: 'PUBLISHED', teacherId: 'teacher-7' });
app.get('/health', (_req, res) => res.json({ status: 'online', service: 'catalog-service' }));
app.get('/api/v1/courses', (req, res) => res.json(page(store.all().filter((course) => course.status === 'PUBLISHED'), req)));
for (const path of ['/api/v1/courses/:courseId', '/internal/v1/courses/:courseId']) app.get(path, (req, res) => {
  const course = store.get(req.params.courseId); return course ? res.json(course) : sendProblem(res, 404, 'Не найдено', 'Курс не найден');
});
app.post('/api/v1/courses', requireIdempotency, async (req, res) => {
  const key = req.get('Idempotency-Key'); if (store.idempotent(key)) return res.status(201).json(store.idempotent(key));
  if (!req.body.title || !Number.isInteger(req.body.priceRub) || req.body.priceRub < 0) return sendProblem(res, 400, 'Некорректный запрос', 'Нужны title и неотрицательный priceRub');
  const course = store.put({ id: id('course'), title: req.body.title, priceRub: req.body.priceRub, status: 'PUBLISHED', teacherId: 'teacher-7' }); store.remember(key, course);
  await bus.publish('course.updated', { courseId: course.id, status: course.status }); res.status(201).json(course);
});
app.listen(process.env.PORT || 3001, '0.0.0.0', () => console.log('catalog-service started'));
