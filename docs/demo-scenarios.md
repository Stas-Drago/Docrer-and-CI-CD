# Демонстрационные сценарии лабораторной работы 4

## Подготовка

```bash
cd lab3
docker compose up --build
curl http://localhost:8081/api/v1/courses
```

Ожидаемый результат: в списке есть опубликованный курс `course-101` с ценой 2490 рублей.

## Успешная запись

```bash
curl -X POST http://localhost:8081/api/v1/enrollments \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: success-1' \
  -d '{"courseId":"course-101"}'
```

Сохраните `id` из ответа. Сразу после запроса запись имеет состояние `PENDING_PAYMENT`. Затем реальная цепочка RabbitMQ передаёт `enrollment.created` в payment-service. Локальный mock платежного шлюза возвращает успех, payment-service публикует `payment.succeeded`; enrollment-service переводит запись в `ACTIVE` и публикует `enrollment.activated`; notification-service сохраняет уведомление.

```bash
curl http://localhost:8081/api/v1/enrollments/ID_ЗАПИСИ
curl http://localhost:8081/api/v1/notifications
```

Повторите тот же POST с `Idempotency-Key: success-1`. Вернётся тот же `id`, второй платёж и вторая запись не создадутся.

## Отказ оплаты и компенсация

Остановите систему, затем запустите её с режимом отказа:

```bash
docker compose down
PAYMENT_MODE=fail docker compose up --build
```

Создайте запись с новым ключом `fail-1`. Mock шлюза публикует `payment.failed`; enrollment-service компенсирует операцию, переводя запись из `PENDING_PAYMENT` в `CANCELLED`, и публикует `enrollment.cancelled`. notification-service создаёт уведомление об отказе. Доступ к курсу не открывается.

Используются реальные сервисы catalog, enrollment, payment, notification, Gateway и RabbitMQ. Внешние платёжный шлюз и почтовый провайдер заменены локальными моками в payment-service и notification-service.
