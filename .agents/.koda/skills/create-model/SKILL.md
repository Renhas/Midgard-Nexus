---
name: create-model
description: Добавление новых моделей
---

# create-model

## Purpose
- Для создания новой модели в приложении.

## Steps
1. Определи все модели в models.py. Сигналы выноси в signals.py.
2. Зарегестрируй модель в админке.
3. Если модель использует choices — вынеси их в constants.py соответствующего приложения.
5. После завершения всех моделей выполни makemigrations и migrate.
6. Если модель связана через GenericForeignKey — удостоверься, что сигналы для каскадного удаления обновлены.

## Notes
- Keep instructions specific and actionable.
