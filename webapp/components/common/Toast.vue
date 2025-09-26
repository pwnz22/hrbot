<template>
  <div
    class="toast"
    :class="[`toast-${type}`, { 'show': visible }]"
    @click="$emit('close')"
  >
    <div class="toast-icon">{{ iconForType }}</div>
    <div class="toast-message">{{ message }}</div>
    <button class="toast-close" @click.stop="$emit('close')">
      ✕
    </button>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'

export default {
  name: 'Toast',
  props: {
    message: {
      type: String,
      required: true
    },
    type: {
      type: String,
      default: 'info',
      validator: value => ['info', 'success', 'warning', 'error'].includes(value)
    },
    duration: {
      type: Number,
      default: 5000
    }
  },
  emits: ['close'],
  setup(props, { emit }) {
    const visible = ref(false)

    const iconForType = computed(() => {
      const icons = {
        info: 'ℹ️',
        success: '✅',
        warning: '⚠️',
        error: '❌'
      }
      return icons[props.type]
    })

    onMounted(() => {
      // Show toast with animation
      setTimeout(() => {
        visible.value = true
      }, 100)

      // Auto close after duration
      if (props.duration > 0) {
        setTimeout(() => {
          emit('close')
        }, props.duration)
      }
    })

    return {
      visible,
      iconForType
    }
  }
}
</script>

<style scoped>
.toast {
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--tg-theme-bg-color, #ffffff);
  border: 1px solid var(--tg-theme-hint-color, #e5e5ea);
  border-radius: 12px;
  padding: 12px 16px;
  margin-bottom: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transform: translateY(-20px);
  opacity: 0;
  transition: all 0.3s ease;
  pointer-events: auto;
  backdrop-filter: blur(20px);
  position: relative;
  overflow: hidden;
}

.toast.show {
  transform: translateY(0);
  opacity: 1;
}

.toast-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.toast-message {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
  color: var(--tg-theme-text-color, #000000);
  line-height: 1.3;
}

.toast-close {
  background: none;
  border: none;
  color: var(--tg-theme-hint-color, #8e8e93);
  font-size: 12px;
  cursor: pointer;
  padding: 4px;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.2s ease;
}

.toast-close:hover {
  background: var(--tg-theme-hint-color, #e5e5ea);
  color: var(--tg-theme-text-color, #000000);
}

/* Type-specific styling */
.toast-success {
  border-left: 4px solid #00c73c;
  background: linear-gradient(135deg, rgba(0, 199, 60, 0.05) 0%, var(--tg-theme-bg-color, #ffffff) 100%);
}

.toast-warning {
  border-left: 4px solid #ff9500;
  background: linear-gradient(135deg, rgba(255, 149, 0, 0.05) 0%, var(--tg-theme-bg-color, #ffffff) 100%);
}

.toast-error {
  border-left: 4px solid #ff3b30;
  background: linear-gradient(135deg, rgba(255, 59, 48, 0.05) 0%, var(--tg-theme-bg-color, #ffffff) 100%);
}

.toast-info {
  border-left: 4px solid var(--tg-theme-accent-text-color, #3390ec);
  background: linear-gradient(135deg, rgba(51, 144, 236, 0.05) 0%, var(--tg-theme-bg-color, #ffffff) 100%);
}

/* Dark theme adjustments */
.toast {
  background: var(--tg-theme-secondary-bg-color, #1c1c1e);
  border-color: var(--tg-theme-hint-color, #38383a);
}

.toast-success {
  background: linear-gradient(135deg, rgba(0, 199, 60, 0.1) 0%, var(--tg-theme-secondary-bg-color, #1c1c1e) 100%);
}

.toast-warning {
  background: linear-gradient(135deg, rgba(255, 149, 0, 0.1) 0%, var(--tg-theme-secondary-bg-color, #1c1c1e) 100%);
}

.toast-error {
  background: linear-gradient(135deg, rgba(255, 59, 48, 0.1) 0%, var(--tg-theme-secondary-bg-color, #1c1c1e) 100%);
}

.toast-info {
  background: linear-gradient(135deg, rgba(51, 144, 236, 0.1) 0%, var(--tg-theme-secondary-bg-color, #1c1c1e) 100%);
}

.toast-close:hover {
  background: var(--tg-theme-hint-color, #38383a);
}

/* Animation on exit */
.toast.fade-out {
  transform: translateX(100%);
  opacity: 0;
  transition: all 0.3s ease;
}

/* Responsive adjustments */
@media (max-width: 360px) {
  .toast {
    padding: 10px 12px;
    margin-bottom: 6px;
  }

  .toast-message {
    font-size: 13px;
  }

  .toast-icon {
    font-size: 14px;
  }
}

/* Accessibility */
@media (prefers-reduced-motion: reduce) {
  .toast {
    transition: none;
    transform: none;
    opacity: 1;
  }

  .toast.show {
    transform: none;
  }

  .toast.fade-out {
    transition: none;
  }
}

/* Touch feedback */
.toast:active {
  transform: scale(0.98);
  opacity: 0.8;
}
</style>