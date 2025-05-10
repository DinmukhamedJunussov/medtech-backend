# CI/CD настройка для MedTech проекта

Этот репозиторий настроен с автоматическим CI/CD пайплайном, используя GitHub Actions.

## Секреты репозитория

Для правильной работы CI/CD необходимо настроить следующие секреты в вашем GitHub репозитории:

### AWS Credentials (для бэкенда)
- `AWS_ACCESS_KEY_ID` - ID ключа доступа AWS
- `AWS_SECRET_ACCESS_KEY` - Секретный ключ доступа AWS

### Vercel (для фронтенда)
- `VERCEL_TOKEN` - Токен доступа Vercel

## Workflows

### Backend CI/CD (backend-ci-cd.yml)
- Запускается при push и pull request в ветку main, если были изменения в директории `backend/`
- Тестирует код с помощью pytest
- Собирает Docker образ и отправляет его в AWS ECR
- Обновляет сервис в AWS ECS

### Frontend CI/CD (frontend-ci-cd.yml)
- Запускается при push и pull request в ветку main, если были изменения в директории `frontend/`
- Собирает проект с помощью pnpm
- Деплоит собранный проект на Vercel

### PR Checks (pr-checks.yml)
- Запускается при создании или обновлении Pull Request
- Проверяет бэкенд с помощью flake8 и mypy
- Проверяет фронтенд с помощью lint

## Ручной запуск

Вы можете вручную запустить любой workflow через интерфейс GitHub Actions на вкладке "Actions" в вашем репозитории.

## Локальное тестирование workflows

Для локального тестирования GitHub Actions workflows можно использовать [act](https://github.com/nektos/act).

```bash
# Установка
brew install act

# Запуск конкретного workflow
act -W .github/workflows/backend-ci-cd.yml
``` 