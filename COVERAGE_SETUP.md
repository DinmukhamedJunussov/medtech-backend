# 📊 Настройка GitHub Coverage Badge

## 🎯 Что было настроено

### ✅ Файлы добавлены/обновлены:
1. **`.coveragerc`** - конфигурация coverage
2. **`.github/workflows/backend-ci-cd.yml`** - обновлен для coverage
3. **`requirements.txt`** - добавлен `pytest-cov==6.0.0`
4. **`README.md`** - добавлены badges

### 📈 Текущее покрытие:
- **Общее покрытие:** 48%
- **Всего тестов:** 40 ✅ (100% успешных)
- **Покрытые компоненты:** API endpoints, SII калькулятор, обработка ошибок

## 🚀 Настройка GitHub

### 1. Codecov (рекомендуется)

#### Шаг 1: Регистрация в Codecov
1. Перейдите на [codecov.io](https://codecov.io)
2. Войдите через GitHub аккаунт
3. Добавьте ваш репозиторий

#### Шаг 2: Получение токена
1. В настройках репозитория Codecov найдите `Repository Upload Token`
2. Скопируйте токен

#### Шаг 3: Добавление секрета в GitHub
1. Перейдите в ваш GitHub репозиторий
2. Settings → Secrets and Variables → Actions
3. Добавьте новый секрет: `CODECOV_TOKEN` со значением токена

#### Шаг 4: Обновление README
Замените в `README.md`:
```markdown
[![codecov](https://codecov.io/gh/yourusername/medtech/graph/badge.svg?token=YOUR_TOKEN)](https://codecov.io/gh/yourusername/medtech)
```

На ваши реальные данные:
```markdown
[![codecov](https://codecov.io/gh/ВАШЕ_ИМЯ/ВАШЕ_РЕПО/graph/badge.svg?token=ВАШ_ТОКЕН)](https://codecov.io/gh/ВАШЕ_ИМЯ/ВАШЕ_РЕПО)
```

### 2. GitHub Actions Badge

Обновите в `README.md`:
```markdown
[![Backend CI/CD](https://github.com/yourusername/medtech/actions/workflows/backend-ci-cd.yml/badge.svg)](https://github.com/yourusername/medtech/actions/workflows/backend-ci-cd.yml)
```

На:
```markdown
[![Backend CI/CD](https://github.com/ВАШЕ_ИМЯ/ВАШЕ_РЕПО/actions/workflows/backend-ci-cd.yml/badge.svg)](https://github.com/ВАШЕ_ИМЯ/ВАШЕ_РЕПО/actions/workflows/backend-ci-cd.yml)
```

## 🔧 Локальное тестирование

### Команды для coverage:

```bash
# Базовый запуск с coverage
pytest tests/ --cov=src

# Полный отчет с HTML
pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

# Только XML для CI/CD
pytest tests/ --cov=src --cov-report=xml

# Просмотр HTML отчета
open htmlcov/index.html  # macOS
```

### Настройка coverage минимума:

В `.coveragerc` можно добавить:
```ini
[report]
fail_under = 70
show_missing = True
```

## 📊 Интерпретация результатов

### Текущие показатели по файлам:
- **🟢 Высокое покрытие (80%+):**
  - `core/exceptions.py` - 100%
  - `middlewares.py` - 100%  
  - `main.py` - 88%
  - `sii_calculator.py` - 81%

- **🟡 Среднее покрытие (50-80%):**
  - `api/endpoints.py` - 61%
  - `services/helper.py` - 57%

- **🟠 Низкое покрытие (<50%):**
  - `document_processor.py` - 24% (AWS зависимые компоненты)
  - `lab_parsers.py` - 41% (требует реальных документов)
  - `ocr_aws.py` - 9% (AWS Textract интеграция)

### 💡 Причины низкого покрытия некоторых компонентов:
1. **AWS зависимости** - требуют реальных ключей и документов
2. **Файловые операции** - сложно мокать в тестах
3. **Внешние API** - Textract, S3 bucket операции

## 🎯 Альтернативные решения

### 1. Собственный badge без внешних сервисов:

```markdown
[![Coverage](https://img.shields.io/badge/coverage-48%25-yellow.svg)](./htmlcov/)
```

### 2. Coverage с GitHub Pages:

Можно настроить автоматическую публикацию HTML отчетов на GitHub Pages.

## ✅ Проверка работы

После настройки:

1. **Сделайте commit и push**
2. **Проверьте GitHub Actions** - должен появиться coverage шаг
3. **Убедитесь что badge обновился** в README
4. **Проверьте Codecov dashboard** (если используете)

## 🚀 Готовые команды

```bash
# Обновление зависимостей
pip install pytest-cov

# Локальный тест coverage
pytest tests/ --cov=src --cov-report=html --cov-report=term-missing -v

# Проверка HTML отчета
open htmlcov/index.html
```

## 📋 Чеклист настройки

- [ ] ✅ Добавлен `pytest-cov` в requirements.txt
- [ ] ✅ Создан `.coveragerc`
- [ ] ✅ Обновлен GitHub workflow
- [ ] ✅ Создан README с badges
- [ ] ⏳ Зарегистрироваться в Codecov
- [ ] ⏳ Добавить CODECOV_TOKEN в GitHub Secrets
- [ ] ⏳ Обновить URLs в README
- [ ] ⏳ Сделать push для проверки

**🎉 После выполнения всех шагов у вас будет красивый coverage badge в README!** 