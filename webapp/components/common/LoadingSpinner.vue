<template>
  <div class="loading-spinner" :class="{ 'overlay': overlay }">
    <div class="spinner-container">
      <div class="spinner" :style="{ width: size, height: size }"></div>
      <div class="loading-text" v-if="text">{{ text }}</div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'LoadingSpinner',
  props: {
    size: {
      type: String,
      default: '32px'
    },
    text: {
      type: String,
      default: ''
    },
    overlay: {
      type: Boolean,
      default: false
    }
  }
}
</script>

<style scoped>
.loading-spinner {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.loading-spinner.overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(4px);
  z-index: 1000;
  padding: 0;
}

.spinner-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  background: var(--tg-theme-bg-color, #ffffff);
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.overlay .spinner-container {
  background: var(--tg-theme-bg-color, #ffffff);
  border: 1px solid var(--tg-theme-hint-color, #e5e5ea);
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--tg-theme-hint-color, #e5e5ea);
  border-top: 3px solid var(--tg-theme-accent-text-color, #3390ec);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-text {
  font-size: 14px;
  color: var(--tg-theme-text-color, #000000);
  font-weight: 500;
  text-align: center;
}

/* Dark theme */
.overlay .spinner-container {
  background: var(--tg-theme-bg-color, #1c1c1e);
  border-color: var(--tg-theme-hint-color, #38383a);
}

/* Accessibility */
@media (prefers-reduced-motion: reduce) {
  .spinner {
    animation: none;
    border: 3px solid var(--tg-theme-accent-text-color, #3390ec);
  }
}
</style>