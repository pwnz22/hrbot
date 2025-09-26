<template>
  <div
    class="stat-card"
    :class="[
      `color-${color}`,
      { 'loading': loading, 'highlight': highlight }
    ]"
  >
    <div class="stat-icon" v-if="icon">{{ icon }}</div>

    <div class="stat-content">
      <div class="stat-value" v-if="!loading">
        {{ formattedValue }}
      </div>
      <div class="stat-skeleton" v-else></div>

      <div class="stat-label">{{ label }}</div>
    </div>

    <div class="stat-indicator" v-if="highlight"></div>
  </div>
</template>

<script>
import { computed } from 'vue'

export default {
  name: 'StatCard',
  props: {
    value: {
      type: [Number, String],
      default: 0
    },
    label: {
      type: String,
      required: true
    },
    icon: {
      type: String,
      default: ''
    },
    color: {
      type: String,
      default: 'primary',
      validator: value => ['primary', 'success', 'warning', 'error'].includes(value)
    },
    loading: {
      type: Boolean,
      default: false
    },
    highlight: {
      type: Boolean,
      default: false
    }
  },
  setup(props) {
    const formattedValue = computed(() => {
      if (typeof props.value === 'number') {
        return props.value.toLocaleString()
      }
      return props.value
    })

    return {
      formattedValue
    }
  }
}
</script>

<style scoped>
.stat-card {
  background: var(--tg-theme-secondary-bg-color, #f2f2f7);
  border: 1px solid var(--tg-theme-hint-color, #e5e5ea);
  border-radius: 12px;
  padding: 16px 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 80px;
  position: relative;
  transition: all 0.3s ease;
  overflow: hidden;
}

.stat-card.highlight {
  border-color: var(--warning-color, #ff9500);
  background: linear-gradient(135deg, rgba(255, 149, 0, 0.05) 0%, var(--tg-theme-secondary-bg-color, #f2f2f7) 100%);
  animation: glow 2s infinite alternate;
}

@keyframes glow {
  from {
    box-shadow: 0 0 5px rgba(255, 149, 0, 0.3);
  }
  to {
    box-shadow: 0 0 15px rgba(255, 149, 0, 0.5);
  }
}

.stat-card.loading {
  pointer-events: none;
}

.stat-icon {
  font-size: 16px;
  margin-bottom: 4px;
  opacity: 0.8;
}

.stat-content {
  text-align: center;
  width: 100%;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  line-height: 1.1;
  margin-bottom: 4px;
  color: var(--tg-theme-text-color, #000000);
  transition: all 0.3s ease;
}

.stat-skeleton {
  height: 28px;
  background: var(--tg-theme-hint-color, #e5e5ea);
  border-radius: 6px;
  margin-bottom: 4px;
  animation: pulse 1.5s infinite;
  opacity: 0.3;
}

@keyframes pulse {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 0.6; }
}

.stat-label {
  font-size: 11px;
  color: var(--tg-theme-hint-color, #8e8e93);
  text-align: center;
  line-height: 1.2;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.stat-indicator {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--warning-color, #ff9500);
  animation: blink 1.5s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0.3; }
}

/* Color variants */
.stat-card.color-primary .stat-value {
  color: var(--tg-theme-accent-text-color, #3390ec);
}

.stat-card.color-success .stat-value {
  color: #00c73c;
}

.stat-card.color-warning .stat-value {
  color: #ff9500;
}

.stat-card.color-error .stat-value {
  color: #ff3b30;
}

/* Dark theme */
.stat-card {
  background: var(--tg-theme-secondary-bg-color, #1c1c1e);
  border-color: var(--tg-theme-hint-color, #38383a);
}

/* Responsive adjustments */
@media (max-width: 360px) {
  .stat-card {
    padding: 12px 8px;
    min-height: 70px;
  }

  .stat-value {
    font-size: 20px;
  }

  .stat-label {
    font-size: 10px;
  }

  .stat-icon {
    font-size: 14px;
  }
}

/* Accessibility */
@media (prefers-reduced-motion: reduce) {
  .stat-card,
  .stat-value,
  .stat-skeleton,
  .stat-indicator {
    animation: none;
    transition: none;
  }

  .stat-card.highlight {
    animation: none;
    box-shadow: 0 0 0 2px var(--warning-color, #ff9500);
  }
}

/* Touch feedback */
.stat-card:active {
  transform: scale(0.97);
  opacity: 0.8;
}
</style>