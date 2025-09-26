<template>
  <button
    class="action-button"
    :class="[
      { 'primary': primary, 'loading': loading, 'disabled': disabled }
    ]"
    :disabled="loading || disabled"
    @click="handleClick"
  >
    <div class="button-content" v-if="!loading">
      <div class="button-icon" v-if="icon">{{ icon }}</div>
      <div class="button-label">{{ label }}</div>
    </div>

    <div class="loading-spinner" v-else>
      <div class="spinner"></div>
      <div class="loading-text">{{ loadingText || 'Загрузка...' }}</div>
    </div>
  </button>
</template>

<script>
export default {
  name: 'ActionButton',
  props: {
    icon: {
      type: String,
      default: ''
    },
    label: {
      type: String,
      required: true
    },
    loading: {
      type: Boolean,
      default: false
    },
    loadingText: {
      type: String,
      default: ''
    },
    disabled: {
      type: Boolean,
      default: false
    },
    primary: {
      type: Boolean,
      default: false
    }
  },
  emits: ['click'],
  setup(props, { emit }) {
    const handleClick = (event) => {
      if (!props.loading && !props.disabled) {
        emit('click', event)
      }
    }

    return {
      handleClick
    }
  }
}
</script>

<style scoped>
.action-button {
  flex: 1;
  height: 60px;
  border: none;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
  min-width: 0;

  /* Default secondary style */
  background: var(--tg-theme-secondary-bg-color, #f2f2f7);
  color: var(--tg-theme-text-color, #000000);
  border: 1px solid var(--tg-theme-hint-color, #e5e5ea);
}

.action-button.primary {
  background: var(--tg-theme-button-color, #3390ec);
  color: var(--tg-theme-button-text-color, #ffffff);
  border: 1px solid var(--tg-theme-button-color, #3390ec);
}

.action-button:active:not(.disabled):not(.loading) {
  transform: scale(0.96);
  opacity: 0.8;
}

.action-button.disabled,
.action-button.loading {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.button-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.button-icon {
  font-size: 20px;
  line-height: 1;
}

.button-label {
  font-size: 12px;
  font-weight: 500;
  line-height: 1.2;
  text-align: center;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid currentColor;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.action-button:not(.primary) .spinner {
  border-color: rgba(0, 0, 0, 0.2);
  border-top-color: currentColor;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-text {
  font-size: 11px;
  font-weight: 500;
  opacity: 0.8;
}

/* Dark theme adjustments */
.action-button {
  background: var(--tg-theme-secondary-bg-color, #1c1c1e);
  border-color: var(--tg-theme-hint-color, #38383a);
}

.action-button.primary {
  background: var(--tg-theme-button-color, #3390ec);
  border-color: var(--tg-theme-button-color, #3390ec);
}

/* Responsive adjustments */
@media (max-width: 360px) {
  .action-button {
    height: 52px;
  }

  .button-icon {
    font-size: 18px;
  }

  .button-label {
    font-size: 11px;
  }

  .spinner {
    width: 16px;
    height: 16px;
  }

  .loading-text {
    font-size: 10px;
  }
}

/* Accessibility */
@media (prefers-reduced-motion: reduce) {
  .action-button {
    transition: none;
  }

  .spinner {
    animation: none;
    border: 2px solid currentColor;
    border-radius: 50%;
  }
}

/* Focus styles for keyboard navigation */
.action-button:focus {
  outline: 2px solid var(--tg-theme-accent-text-color, #3390ec);
  outline-offset: 2px;
}

/* Hover effects for non-touch devices */
@media (hover: hover) {
  .action-button:hover:not(.disabled):not(.loading) {
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  }

  .action-button.primary:hover:not(.disabled):not(.loading) {
    box-shadow: 0 2px 8px rgba(51, 144, 236, 0.3);
  }
}
</style>