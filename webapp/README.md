# 📱 HR Bot Telegram Mini App

Telegram Mini App для управления вакансиями и откликами.

## 🚀 Быстрый старт

### Локальная разработка

```bash
# Установка зависимостей
npm install

# Запуск в режиме разработки
npm run dev

# Сборка для продакшена
npm run build
```

## 🌐 Деплой на GitHub Pages

1. **Обновите конфигурацию:**
   - В `vite.config.js` замените `REPOSITORY_NAME` на имя вашего репозитория
   - В `src/config.js` обновите `API_BASE_URL` для продакшена

2. **Настройте GitHub Pages:**
   - Settings → Pages
   - Source: Deploy from a branch
   - Branch: gh-pages

3. **После деплоя ваше приложение будет доступно по адресу:**
   `https://USERNAME.github.io/REPOSITORY_NAME/`

## 🤖 Настройка Telegram Bot

### 1. Создайте Mini App через @BotFather:

```
/newapp
Выберите бота
Название: HR Bot Mini App
Описание: Управление вакансиями и откликами
URL: https://USERNAME.github.io/REPOSITORY_NAME/
```

### 2. Настройте меню бота:

```
/mybots
Выберите бота
Bot Settings → Menu Button → Configure Menu Button
Text: 📱 Открыть приложение
```

## 📋 Структура проекта

```
webapp/
├── src/
│   ├── main.js          # Точка входа
│   ├── style.css        # Глобальные стили
│   └── config.js        # Конфигурация API
├── components/          # Vue компоненты
├── composables/         # Vue composables
├── MainApp.vue         # Главный компонент
├── index.html          # HTML шаблон
└── vite.config.js      # Конфигурация Vite
```

## 🔧 API интеграция

Приложение подключается к FastAPI бэкенду:
- `/stats` - статистика откликов
- `/vacancies` - список вакансий
- `/applications` - список откликов

## 📱 Функционал

- ✅ Просмотр статистики откликов
- ✅ Список вакансий с количеством откликов
- ✅ Навигация между разделами
- ✅ Поддержка тем Telegram (светлая/темная)
- ✅ Адаптивный дизайн для мобильных устройств
- ✅ Toast уведомления
- ✅ Loading состояния