export const problem = (status, title, detail) => ({
  type: `https://mathcourses.example/problems/http-${status}`,
  title,
  status,
  detail,
  traceId: crypto.randomUUID()
});

export function sendProblem(res, status, title, detail) {
  return res.status(status).type('application/problem+json').json(problem(status, title, detail));
}

export function requireIdempotency(req, res, next) {
  if (!req.get('Idempotency-Key')) return sendProblem(res, 400, 'Некорректный запрос', 'Требуется заголовок Idempotency-Key');
  next();
}

export function page(items, req) {
  const requestedPage = Number(req.query.page || 1);
  const requestedSize = Math.min(Number(req.query.size || 20), 100);
  const start = (requestedPage - 1) * requestedSize;
  return { items: items.slice(start, start + requestedSize), page: requestedPage, size: requestedSize, total: items.length };
}
