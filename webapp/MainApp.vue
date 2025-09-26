<template>
  <div class="hr-app" :class="{ 'theme-dark': isDarkTheme }">
    <!-- Header -->
    <header class="app-header">
      <div class="header-content">
        <h1 class="app-title">HR Bot</h1>
        <div class="sync-status">
          <div
            class="sync-indicator"
            :class="{ 'syncing': isSyncing }"
            @click="handleSync"
          ></div>
        </div>
      </div>
    </header>

    <!-- Statistics Overview -->
    <section class="stats-section">
      <div class="stats-container">
        <StatCard
          :value="stats.total"
          label="Всего откликов"
          icon="📊"
          color="primary"
          :loading="loadingStats"
        />
        <StatCard
          :value="stats.processed"
          label="Обработано"
          icon="✅"
          color="success"
          :loading="loadingStats"
        />
        <StatCard
          :value="stats.unprocessed"
          label="Требует обработки"
          icon="⚠️"
          color="warning"
          :loading="loadingStats"
          :highlight="stats.unprocessed > 0"
        />
      </div>
    </section>

    <!-- Quick Actions -->
    <section class="actions-section">
      <div class="quick-actions">
        <ActionButton
          icon="🔄"
          label="Парсить письма"
          @click="handleParseEmails"
          :loading="parsing"
          primary
        />
        <ActionButton
          icon="📤"
          label="Экспорт Excel"
          @click="handleExport"
          :loading="exporting"
        />
      </div>
    </section>

    <!-- Main Navigation -->
    <section class="navigation-section">
      <div class="nav-cards">
        <!-- Vacancies -->
        <div class="nav-card" @click="navigateToVacancies">
          <div class="nav-card-content">
            <div class="nav-icon vacancy-icon">
              <span>📋</span>
            </div>
            <div class="nav-info">
              <div class="nav-title">Вакансии</div>
              <div class="nav-subtitle">{{ vacancies.length }} активных вакансий</div>
            </div>
          </div>
          <div class="nav-badge" v-if="stats.total > 0">{{ stats.total }}</div>
          <div class="nav-arrow">›</div>
        </div>

        <!-- Unprocessed Applications -->
        <div
          class="nav-card urgent"
          @click="navigateToUnprocessed"
          v-if="stats.unprocessed > 0"
        >
          <div class="nav-card-content">
            <div class="nav-icon unprocessed-icon">
              <span>❌</span>
            </div>
            <div class="nav-info">
              <div class="nav-title">Требуют обработки</div>
              <div class="nav-subtitle">Новые отклики ждут проверки</div>
            </div>
          </div>
          <div class="nav-badge urgent-badge">{{ stats.unprocessed }}</div>
          <div class="nav-arrow">›</div>
        </div>

        <!-- Recent Activity -->
        <div class="nav-card" @click="navigateToRecent">
          <div class="nav-card-content">
            <div class="nav-icon recent-icon">
              <span>🕒</span>
            </div>
            <div class="nav-info">
              <div class="nav-title">Последняя активность</div>
              <div class="nav-subtitle">{{ formatLastActivity }}</div>
            </div>
          </div>
          <div class="nav-arrow">›</div>
        </div>
      </div>
    </section>

    <!-- Recent Applications Preview -->
    <section class="recent-preview" v-if="recentApplications.length > 0">
      <div class="section-header">
        <h3 class="section-title">Последние отклики</h3>
        <button class="see-all-btn" @click="navigateToRecent">
          Все
        </button>
      </div>
      <div class="applications-preview">
        <ApplicationPreview
          v-for="app in recentApplications.slice(0, 3)"
          :key="app.id"
          :application="app"
          @click="viewApplication(app.id)"
        />
      </div>
    </section>

    <!-- Loading Overlay -->
    <div class="loading-overlay" v-if="globalLoading">
      <LoadingSpinner />
    </div>

    <!-- Toast Notifications -->
    <div class="toast-container">
      <Toast
        v-for="toast in toasts"
        :key="toast.id"
        :message="toast.message"
        :type="toast.type"
        @close="removeToast(toast.id)"
      />
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { useTelegram } from './composables/useTelegram'
import StatCard from './components/common/StatCard.vue'
import ActionButton from './components/common/ActionButton.vue'
import ApplicationPreview from './components/applications/ApplicationPreview.vue'
import LoadingSpinner from './components/common/LoadingSpinner.vue'
import Toast from './components/common/Toast.vue'
import config from './src/config.js'

export default {
  name: 'MainApp',
  components: {
    StatCard,
    ActionButton,
    ApplicationPreview,
    LoadingSpinner,
    Toast
  },
  setup() {
    const { tg, user, isDarkTheme } = useTelegram()

    // Reactive data
    const stats = ref({
      total: 0,
      processed: 0,
      unprocessed: 0
    })

    const vacancies = ref([])
    const recentApplications = ref([])
    const loadingStats = ref(true)
    const parsing = ref(false)
    const exporting = ref(false)
    const globalLoading = ref(false)
    const isSyncing = ref(false)
    const lastActivity = ref(null)
    const toasts = ref([])

    // Computed
    const formatLastActivity = computed(() => {
      if (!lastActivity.value) return 'Нет активности'
      const now = new Date()
      const diff = now - new Date(lastActivity.value)
      const minutes = Math.floor(diff / 60000)

      if (minutes < 1) return 'Только что'
      if (minutes < 60) return `${minutes} мин назад`
      if (minutes < 1440) return `${Math.floor(minutes / 60)} ч назад`
      return new Date(lastActivity.value).toLocaleDateString()
    })

    // Methods
    const loadStats = async () => {
      try {
        loadingStats.value = true
        const response = await fetch(`${config.API_BASE_URL}/stats`)
        const data = await response.json()
        stats.value = {
          total: data.applications.total,
          processed: data.applications.processed,
          unprocessed: data.applications.unprocessed
        }
        lastActivity.value = new Date()
      } catch (error) {
        showToast('Ошибка загрузки статистики', 'error')
      } finally {
        loadingStats.value = false
      }
    }

    const loadVacancies = async () => {
      try {
        const response = await fetch(`${config.API_BASE_URL}/vacancies`)
        const data = await response.json()
        vacancies.value = data
      } catch (error) {
        showToast('Ошибка загрузки вакансий', 'error')
      }
    }

    const loadRecentApplications = async () => {
      try {
        const response = await fetch(`${config.API_BASE_URL}/applications?limit=3`)
        const data = await response.json()
        recentApplications.value = data
      } catch (error) {
        console.error('Error loading recent applications:', error)
      }
    }

    const handleParseEmails = async () => {
      showToast('Парсинг запускается через бот. Используйте команду /parse в Telegram', 'info')
    }

    const handleExport = async () => {
      showToast('Экспорт запускается через бот. Используйте команду /export в Telegram', 'info')
    }

    const handleSync = () => {
      if (!isSyncing.value) {
        handleParseEmails()
      }
    }

    const navigateToVacancies = () => {
      tg.HapticFeedback.impactOccurred('light')
      // Navigate to vacancies page
    }

    const navigateToUnprocessed = () => {
      tg.HapticFeedback.impactOccurred('medium')
      // Navigate to unprocessed page
    }

    const navigateToRecent = () => {
      tg.HapticFeedback.impactOccurred('light')
      // Navigate to recent page
    }

    const viewApplication = (id) => {
      tg.HapticFeedback.impactOccurred('light')
      // Navigate to application details
    }

    const showToast = (message, type = 'info') => {
      const id = Date.now()
      toasts.value.push({ id, message, type })
      setTimeout(() => removeToast(id), 5000)
    }

    const removeToast = (id) => {
      const index = toasts.value.findIndex(toast => toast.id === id)
      if (index > -1) toasts.value.splice(index, 1)
    }

    // Lifecycle
    onMounted(async () => {
      globalLoading.value = true
      try {
        await Promise.all([
          loadStats(),
          loadVacancies(),
          loadRecentApplications()
        ])
      } finally {
        globalLoading.value = false
      }

      // Set up Telegram WebApp
      tg.ready()
      tg.expand()
    })

    return {
      isDarkTheme,
      stats,
      vacancies,
      recentApplications,
      loadingStats,
      parsing,
      exporting,
      globalLoading,
      isSyncing,
      formatLastActivity,
      toasts,
      handleParseEmails,
      handleExport,
      handleSync,
      navigateToVacancies,
      navigateToUnprocessed,
      navigateToRecent,
      viewApplication,
      removeToast
    }
  }
}
</script>

<style scoped>
.hr-app {
  min-height: 100vh;
  background: var(--tg-theme-bg-color, #ffffff);
  color: var(--tg-theme-text-color, #000000);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  overflow-x: hidden;
}

/* Header */
.app-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--tg-theme-bg-color, #ffffff);
  border-bottom: 1px solid var(--tg-theme-hint-color, #e5e5ea);
  backdrop-filter: blur(20px);
}

.header-content {
  height: 64px;
  padding: 0 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.app-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--tg-theme-text-color, #000000);
  margin: 0;
}

.sync-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sync-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--tg-theme-accent-text-color, #3390ec);
  cursor: pointer;
  transition: all 0.3s ease;
}

.sync-indicator.syncing {
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(1.2); }
  100% { opacity: 1; transform: scale(1); }
}

/* Statistics */
.stats-section {
  padding: 20px;
}

.stats-container {
  display: flex;
  gap: 12px;
}

/* Quick Actions */
.actions-section {
  padding: 0 20px 20px;
}

.quick-actions {
  display: flex;
  gap: 12px;
}

/* Navigation */
.navigation-section {
  padding: 0 20px 20px;
}

.nav-cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.nav-card {
  background: var(--tg-theme-secondary-bg-color, #f2f2f7);
  border: 1px solid var(--tg-theme-hint-color, #e5e5ea);
  border-radius: 12px;
  padding: 16px;
  display: flex;
  align-items: center;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
}

.nav-card:active {
  background: var(--tg-theme-hint-color, #e5e5ea);
  transform: scale(0.98);
}

.nav-card.urgent {
  border-color: #ff3b30;
  background: linear-gradient(135deg, rgba(255, 59, 48, 0.05) 0%, var(--tg-theme-secondary-bg-color, #f2f2f7) 100%);
}

.nav-card-content {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.nav-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  background: var(--tg-theme-accent-text-color, #3390ec);
  color: white;
}

.nav-icon.vacancy-icon {
  background: linear-gradient(135deg, #3390ec, #4ea5f5);
}

.nav-icon.unprocessed-icon {
  background: linear-gradient(135deg, #ff3b30, #ff6b5b);
}

.nav-icon.recent-icon {
  background: linear-gradient(135deg, #ff9500, #ffad33);
}

.nav-info {
  flex: 1;
}

.nav-title {
  font-size: 16px;
  font-weight: 500;
  color: var(--tg-theme-text-color, #000000);
  margin-bottom: 2px;
  line-height: 1.2;
}

.nav-subtitle {
  font-size: 14px;
  color: var(--tg-theme-hint-color, #8e8e93);
  line-height: 1.2;
}

.nav-badge {
  background: var(--tg-theme-accent-text-color, #3390ec);
  color: white;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  min-width: 24px;
  text-align: center;
  margin-right: 8px;
}

.nav-badge.urgent-badge {
  background: #ff3b30;
  animation: badge-pulse 2s infinite;
}

@keyframes badge-pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

.nav-arrow {
  color: var(--tg-theme-hint-color, #8e8e93);
  font-size: 18px;
  font-weight: 300;
}

/* Recent Preview */
.recent-preview {
  padding: 0 20px 20px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--tg-theme-text-color, #000000);
  margin: 0;
}

.see-all-btn {
  background: none;
  border: none;
  color: var(--tg-theme-accent-text-color, #3390ec);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: background-color 0.2s ease;
}

.see-all-btn:active {
  background: rgba(51, 144, 236, 0.1);
}

.applications-preview {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* Loading & Toast */
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.toast-container {
  position: fixed;
  top: 80px;
  left: 20px;
  right: 20px;
  z-index: 1001;
  pointer-events: none;
}

/* Dark theme adjustments */
.theme-dark .nav-card {
  background: var(--tg-theme-secondary-bg-color, #1c1c1e);
  border-color: var(--tg-theme-hint-color, #38383a);
}

.theme-dark .nav-card:active {
  background: var(--tg-theme-hint-color, #38383a);
}

/* Responsive adjustments */
@media (max-width: 360px) {
  .stats-container {
    gap: 8px;
  }

  .quick-actions {
    gap: 8px;
  }

  .nav-cards {
    gap: 8px;
  }

  .header-content,
  .stats-section,
  .actions-section,
  .navigation-section,
  .recent-preview {
    padding-left: 16px;
    padding-right: 16px;
  }
}

/* Accessibility */
@media (prefers-reduced-motion: reduce) {
  .sync-indicator.syncing,
  .nav-badge.urgent-badge {
    animation: none;
  }

  .nav-card {
    transition: none;
  }
}
</style>