# CI/CD для платформы математических курсов

Для лабораторной №5 выбраны GitHub Actions и Docker Hub. Конфигурация workflow хранится в `.github/workflows/ci.yml`: GitHub автоматически запускает её при `push` и pull request в `main`. Docker Hub хранит готовые образы четырёх реализованных бизнес-сервисов.

## Этапы

1. `unit` — устанавливает npm-зависимости с кэшем и запускает unit-тесты.
2. `package` — в матрице собирает Docker-образы catalog, enrollment, payment и notification.
3. `integration` — запускает Docker Compose, ждёт Gateway и проходит сквозной сценарий оплаты.
4. `publish-images` — только при push в `main`: публикует образы всех четырёх сервисов в Docker Hub с тегами SHA и `latest`.

## Однократная настройка Docker Hub и GitHub

1. Зарегистрироваться на [Docker Hub](https://hub.docker.com/) и запомнить логин в нижнем регистре.
2. В Docker Hub открыть **Account Settings → Personal access tokens**, создать токен с правами `Read & Write`, скопировать его один раз и сохранить в надёжном месте. Пароль аккаунта для workflow не используется.
3. Открыть GitHub-репозиторий `Stas-Drago/Docrer-and-CI-CD` → **Settings → Secrets and variables → Actions**.
4. Создать два repository secrets:
   - `DOCKERHUB_USERNAME` — логин Docker Hub;
   - `DOCKERHUB_TOKEN` — созданный Personal Access Token.
5. Вкладка **Actions → General**: разрешить workflow `Read repository contents permission`; дополнительные права packages не нужны.

Значения секретов недоступны исходному коду, не печатаются в логе и не должны попадать в `.env`, README или коммиты.

После первого успешного `push` в `main` в Docker Hub появятся репозитории:

```text
<dockerhub-login>/mathcourses-catalog-service
<dockerhub-login>/mathcourses-enrollment-service
<dockerhub-login>/mathcourses-payment-service
<dockerhub-login>/mathcourses-notification-service
```

Каждый образ получает два тега: `latest` для последней версии из `main` и SHA коммита для точного воспроизводимого развёртывания.

## Локальная проверка

```bash
npm install
npm test
docker compose build
docker compose up -d
RUN_INTEGRATION=1 npm run test:integration
docker compose down
```

## Запуск опубликованных образов

После публикации скопировать `.env.example` в `.env` и указать свой логин Docker Hub. Затем вместо локальной сборки выполнить:

```bash
docker compose -f docker-compose.yml -f docker-compose.hub.yml pull
docker compose -f docker-compose.yml -f docker-compose.hub.yml up -d --no-build
```

Для запуска строго определённой версии задать SHA-тег в `.env`, например `IMAGE_TAG=3e7241a`. Проверка доступности: `curl http://localhost:8081/health`. Остановка: `docker compose -f docker-compose.yml -f docker-compose.hub.yml down`.

В GitHub открыть вкладку **Actions** и выбрать workflow `Math Courses CI CD`. Для демонстрации неуспешного прогона достаточно временно изменить ожидаемый статус в `tests/integration.test.js`, отправить ветку с изменением и показать остановку workflow на этапе `integration`; затем изменение нужно отменить.
