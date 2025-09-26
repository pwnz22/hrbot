import { ref, onMounted, computed } from 'vue'

export function useTelegram() {
  const tg = window.Telegram?.WebApp
  const user = ref(null)
  const isReady = ref(false)
  const themeParams = ref({})

  // Reactive theme detection
  const isDarkTheme = computed(() => {
    return tg?.colorScheme === 'dark' ||
           themeParams.value?.bg_color === '#1c1c1e' ||
           document.documentElement.classList.contains('dark-theme')
  })

  const initializeTelegram = () => {
    if (!tg) {
      console.warn('Telegram WebApp not available')
      return
    }

    // Get user data
    user.value = tg.initDataUnsafe?.user || null

    // Get theme parameters
    themeParams.value = tg.themeParams || {}

    // Set up theme CSS variables
    updateThemeVariables()

    // Listen for theme changes
    tg.onEvent('themeChanged', () => {
      themeParams.value = tg.themeParams
      updateThemeVariables()
    })

    // Set up viewport
    tg.ready()
    tg.expand()

    // Set main button if needed
    if (tg.MainButton) {
      tg.MainButton.hide()
    }

    // Set back button if needed
    if (tg.BackButton) {
      tg.BackButton.hide()
    }

    // Enable closing confirmation if needed
    tg.enableClosingConfirmation()

    isReady.value = true
  }

  const updateThemeVariables = () => {
    if (!tg?.themeParams) return

    const root = document.documentElement
    const params = tg.themeParams

    // Set CSS custom properties for Telegram theme
    if (params.bg_color) {
      root.style.setProperty('--tg-theme-bg-color', params.bg_color)
    }
    if (params.text_color) {
      root.style.setProperty('--tg-theme-text-color', params.text_color)
    }
    if (params.hint_color) {
      root.style.setProperty('--tg-theme-hint-color', params.hint_color)
    }
    if (params.link_color) {
      root.style.setProperty('--tg-theme-link-color', params.link_color)
    }
    if (params.button_color) {
      root.style.setProperty('--tg-theme-button-color', params.button_color)
    }
    if (params.button_text_color) {
      root.style.setProperty('--tg-theme-button-text-color', params.button_text_color)
    }
    if (params.secondary_bg_color) {
      root.style.setProperty('--tg-theme-secondary-bg-color', params.secondary_bg_color)
    }
    if (params.accent_text_color) {
      root.style.setProperty('--tg-theme-accent-text-color', params.accent_text_color)
    }

    // Add theme class to body
    document.body.className = isDarkTheme.value ? 'theme-dark' : 'theme-light'
  }

  // Utility functions
  const showMainButton = (text, onClick) => {
    if (!tg?.MainButton) return

    tg.MainButton.setText(text)
    tg.MainButton.show()
    tg.MainButton.onClick(onClick)
  }

  const hideMainButton = () => {
    if (!tg?.MainButton) return
    tg.MainButton.hide()
  }

  const showBackButton = (onClick) => {
    if (!tg?.BackButton) return
    tg.BackButton.show()
    tg.BackButton.onClick(onClick)
  }

  const hideBackButton = () => {
    if (!tg?.BackButton) return
    tg.BackButton.hide()
  }

  const showAlert = (message) => {
    if (tg?.showAlert) {
      tg.showAlert(message)
    } else {
      alert(message)
    }
  }

  const showConfirm = (message, callback) => {
    if (tg?.showConfirm) {
      tg.showConfirm(message, callback)
    } else {
      const result = confirm(message)
      callback(result)
    }
  }

  const showPopup = (params, callback) => {
    if (tg?.showPopup) {
      tg.showPopup(params, callback)
    } else {
      // Fallback for browsers
      const result = confirm(params.message)
      callback(result ? 'ok' : 'cancel')
    }
  }

  const hapticFeedback = (type = 'light') => {
    if (tg?.HapticFeedback) {
      switch (type) {
        case 'light':
          tg.HapticFeedback.impactOccurred('light')
          break
        case 'medium':
          tg.HapticFeedback.impactOccurred('medium')
          break
        case 'heavy':
          tg.HapticFeedback.impactOccurred('heavy')
          break
        case 'success':
          tg.HapticFeedback.notificationOccurred('success')
          break
        case 'warning':
          tg.HapticFeedback.notificationOccurred('warning')
          break
        case 'error':
          tg.HapticFeedback.notificationOccurred('error')
          break
        default:
          tg.HapticFeedback.selectionChanged()
      }
    }
  }

  const setHeaderColor = (color) => {
    if (tg?.setHeaderColor) {
      tg.setHeaderColor(color)
    }
  }

  const setBackgroundColor = (color) => {
    if (tg?.setBackgroundColor) {
      tg.setBackgroundColor(color)
    }
  }

  const close = () => {
    if (tg?.close) {
      tg.close()
    }
  }

  const sendData = (data) => {
    if (tg?.sendData) {
      tg.sendData(JSON.stringify(data))
    }
  }

  const openLink = (url, options = {}) => {
    if (tg?.openLink) {
      tg.openLink(url, options)
    } else {
      window.open(url, '_blank')
    }
  }

  const openTelegramLink = (url) => {
    if (tg?.openTelegramLink) {
      tg.openTelegramLink(url)
    } else {
      window.open(url, '_blank')
    }
  }

  onMounted(() => {
    initializeTelegram()
  })

  return {
    tg,
    user: computed(() => user.value),
    isReady: computed(() => isReady.value),
    isDarkTheme,
    themeParams: computed(() => themeParams.value),

    // Utility functions
    showMainButton,
    hideMainButton,
    showBackButton,
    hideBackButton,
    showAlert,
    showConfirm,
    showPopup,
    hapticFeedback,
    setHeaderColor,
    setBackgroundColor,
    close,
    sendData,
    openLink,
    openTelegramLink
  }
}

// Helper function to check if running in Telegram
export function isTelegramWebApp() {
  return !!(window.Telegram?.WebApp)
}

// Mock Telegram WebApp for development
export function mockTelegramWebApp() {
  if (window.Telegram?.WebApp) return

  window.Telegram = {
    WebApp: {
      ready: () => console.log('Telegram WebApp ready (mock)'),
      expand: () => console.log('Telegram WebApp expanded (mock)'),
      close: () => console.log('Telegram WebApp closed (mock)'),

      colorScheme: 'light',
      themeParams: {
        bg_color: '#ffffff',
        text_color: '#000000',
        hint_color: '#8e8e93',
        link_color: '#3390ec',
        button_color: '#3390ec',
        button_text_color: '#ffffff',
        secondary_bg_color: '#f2f2f7',
        accent_text_color: '#3390ec'
      },

      initDataUnsafe: {
        user: {
          id: 12345,
          first_name: 'Test',
          last_name: 'User',
          username: 'testuser',
          language_code: 'ru'
        }
      },

      MainButton: {
        text: '',
        color: '#3390ec',
        textColor: '#ffffff',
        isVisible: false,
        isActive: true,
        setText: (text) => console.log('MainButton setText:', text),
        show: () => console.log('MainButton show'),
        hide: () => console.log('MainButton hide'),
        onClick: (callback) => console.log('MainButton onClick set'),
        offClick: (callback) => console.log('MainButton offClick'),
      },

      BackButton: {
        isVisible: false,
        show: () => console.log('BackButton show'),
        hide: () => console.log('BackButton hide'),
        onClick: (callback) => console.log('BackButton onClick set'),
        offClick: (callback) => console.log('BackButton offClick'),
      },

      HapticFeedback: {
        impactOccurred: (style) => console.log('Haptic impact:', style),
        notificationOccurred: (type) => console.log('Haptic notification:', type),
        selectionChanged: () => console.log('Haptic selection changed'),
      },

      showAlert: (message, callback) => {
        alert(message)
        if (callback) callback()
      },

      showConfirm: (message, callback) => {
        const result = confirm(message)
        if (callback) callback(result)
      },

      showPopup: (params, callback) => {
        const result = confirm(params.message)
        if (callback) callback(result ? 'ok' : 'cancel')
      },

      enableClosingConfirmation: () => console.log('Closing confirmation enabled'),
      disableClosingConfirmation: () => console.log('Closing confirmation disabled'),

      onEvent: (eventType, callback) => {
        console.log('Event listener added:', eventType)
      },

      offEvent: (eventType, callback) => {
        console.log('Event listener removed:', eventType)
      },

      sendData: (data) => console.log('Data sent:', data),

      openLink: (url, options) => {
        console.log('Opening link:', url, options)
        window.open(url, '_blank')
      },

      openTelegramLink: (url) => {
        console.log('Opening Telegram link:', url)
        window.open(url, '_blank')
      }
    }
  }
}