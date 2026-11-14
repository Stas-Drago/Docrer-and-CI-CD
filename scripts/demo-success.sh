#!/usr/bin/env sh
set -eu
api="${API_URL:-http://localhost:8081}"
key="demo-success-$(date +%s)"
curl -fsS "$api/api/v1/courses"
printf '\n'
curl -fsS -X POST "$api/api/v1/enrollments" -H 'Content-Type: application/json' -H "Idempotency-Key: $key" -d '{"courseId":"course-101"}'
printf '\nПроверьте через несколько секунд: GET /api/v1/enrollments\n'
