---
name: docker-config
description: При создании и измении конфигурации Docker
---

# docker-config

## Purpose
- Изменяет конфигурацию Docker для приложения.

## Steps
1. При добавлении сервисов в docker-compose.yml дублируй изменения в docker-compose.prod.yml с учетом продакшн-настроек (порты, volumes, переменные окружения).
2. Все новые секреты выноси в .env.example, оставляя заглушки. Реальные значения бери из .env.
3. Обновляй конфигурацию Nginx, если добавляются новые статические пути или медиа-папки
4. В README поддерживай актуальную инструкцию по запуску приложения через Docker.

## Notes
- Keep instructions specific and actionable.
