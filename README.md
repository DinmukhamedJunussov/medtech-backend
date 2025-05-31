# 🏥 MedTech Backend API

[![Backend CI/CD](https://github.com/yourusername/medtech/actions/workflows/backend-ci-cd.yml/badge.svg)](https://github.com/yourusername/medtech/actions/workflows/backend-ci-cd.yml)
[![codecov](https://codecov.io/gh/yourusername/medtech/graph/badge.svg?token=YOUR_TOKEN)](https://codecov.io/gh/yourusername/medtech)
[![Python](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![Tests](https://img.shields.io/badge/tests-40%20passed-success.svg)](./tests/)
[![Coverage](https://img.shields.io/badge/coverage-48%25-yellow.svg)](./htmlcov/)

> Система анализа медицинских показателей крови с расчетом SII (Systemic Immune-Inflammation Index)

## 🚀 Особенности

- **🔬 Расчет SII** - автоматический расчет индекса системного воспаления
- **🏥 Поддержка лабораторий** - Инвитро, Олимп, InVivo
- **📄 Обработка документов** - PDF и изображения через AWS Textract
- **🩺 Типы рака** - поддержка различных ICD-10 кодов
- **⚡ Быстрый API** - FastAPI с автоматической документацией
- **🛡️ Обработка ошибок** - структурированные исключения
- **🌡️ Мониторинг** - эндпоинт здоровья системы

## 📊 Архитектура

### 🏗️ Модульная структура:
```
src/
├── api/           # API эндпоинты
├── services/      # Бизнес-логика
├── core/          # Исключения и базовые классы
├── schemas/       # Pydantic модели
├── middlewares.py # Промежуточное ПО
└── main.py        # Точка входа приложения
```

### 🔄 Сервисы:
- **SIICalculator** - расчет индекса SII
- **DocumentProcessor** - обработка медицинских документов
- **LabParsers** - парсеры для разных лабораторий

## 🛠️ Установка и запуск

### Требования:
- Python 3.13+
- AWS аккаунт (для Textract OCR)

### Локальная разработка:

```bash
# Клонирование проекта
git clone https://github.com/yourusername/medtech.git
cd medtech/backend

# Создание виртуального окружения
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# или .venv\Scripts\activate  # Windows

# Установка зависимостей
pip install -r requirements.txt

# Запуск сервера
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 🐳 Docker:

```bash
# Сборка образа
docker build -t medtech-backend .

# Запуск контейнера
docker run -p 8000:8000 medtech-backend
```

## 🧪 Тестирование

### Запуск тестов:

```bash
# Все тесты
pytest tests/ -v

# С покрытием
pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

# По компонентам
pytest tests/test_blood_results_controller_updated.py -v  # API тесты
pytest tests/test_interpret_sii_unit.py -v                # Unit тесты SII
pytest tests/test_blood_parser.py -v                      # Парсеры
```

### 📈 Статистика тестов:
- **Всего тестов:** 40
- **Успешных:** 40 ✅ (100%)
- **Покрытие кода:** 48%
- **Время выполнения:** ~0.07 секунды

## 📖 API Документация

После запуска сервера документация доступна по адресам:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### 🔗 Основные эндпоинты:

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| `GET` | `/` | Информация об API |
| `GET` | `/health` | Состояние системы |
| `POST` | `/parse-blood-test` | Парсинг документа анализа |
| `POST` | `/blood-results` | Расчет SII по данным |

### 📝 Пример запроса:

```bash
curl -X POST "http://localhost:8000/blood-results" \
     -H "Content-Type: application/json" \
     -d '{
       "neutrophils_absolute": 4.0,
       "platelets": 250.0,
       "lymphocytes_absolute": 2.0,
       "cancer_type": "C34"
     }'
```

## 🏥 Поддерживаемые лаборатории

| Лаборатория | Тип документов | Статус |
|-------------|----------------|--------|
| **Инвитро** | PDF, изображения | ✅ |
| **Олимп** | PDF, изображения | ✅ |
| **InVivo** | PDF, изображения | ✅ |

## 🩺 Поддерживаемые типы рака

- **C34** - Рак легкого
- **C25** - Рак поджелудочной железы
- **C16** - Рак желудка
- **C15** - Рак пищевода
- **C18** - Колоректальный рак
- **C50** - Рак молочной железы
- **C53** - Гинекологические опухоли
- **C22.0** - Гепатоцеллюлярная карцинома

## 🚀 Деплой

### AWS (автоматический):
Проект автоматически деплоится в AWS ECS через GitHub Actions при push в `main` ветку.

### Ручной деплой:
```bash
# Сборка для production
docker build -t medtech-backend:prod .

# Пуш в ECR
docker tag medtech-backend:prod $ECR_REGISTRY/medtech-backend:latest
docker push $ECR_REGISTRY/medtech-backend:latest
```

## 🤝 Разработка

### 🔄 Процесс разработки:
1. Создайте ветку от `main`
2. Внесите изменения
3. Добавьте тесты для новой функциональности
4. Запустите тесты локально
5. Создайте Pull Request

### 📋 Требования к коду:
- Покрытие тестами новой функциональности
- Соблюдение типизации (mypy)
- Следование стилю кода (flake8)
- Документирование API (docstrings)

## 📄 Лицензия

MIT License - см. [LICENSE](LICENSE) файл.

## 👥 Команда

Создано с ❤️ командой MedTech

---

**📞 Поддержка:** Если у вас есть вопросы, создайте [issue](https://github.com/yourusername/medtech/issues) в репозитории. 