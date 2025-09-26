import { createApp } from 'vue'
import MainApp from '../MainApp.vue'
import './style.css'

// Инициализация Telegram WebApp
if (window.Telegram?.WebApp) {
  window.Telegram.WebApp.ready()
  window.Telegram.WebApp.expand()

  // Применяем тему Telegram
  document.documentElement.style.setProperty('--tg-theme-bg-color', window.Telegram.WebApp.themeParams.bg_color || '#ffffff')
  document.documentElement.style.setProperty('--tg-theme-text-color', window.Telegram.WebApp.themeParams.text_color || '#000000')
}

const app = createApp(MainApp)
app.mount('#app')