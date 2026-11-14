#!/usr/bin/env sh
set -eu
echo 'Запустите: PAYMENT_MODE=fail docker compose up --build'
echo 'Затем выполните: curl -X POST http://localhost:8081/api/v1/enrollments -H "Content-Type: application/json" -H "Idempotency-Key: fail-1" -d "{\"courseId\":\"course-101\"}"'
echo 'Событие payment.failed переведёт запись в CANCELLED, а notification-service запишет уведомление.'
