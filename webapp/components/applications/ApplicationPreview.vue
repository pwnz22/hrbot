<template>
  <div
    class="application-preview"
    :class="{ 'unprocessed': !application.is_processed }"
    @click="$emit('click')"
  >
    <div class="preview-content">
      <div class="applicant-info">
        <div class="applicant-header">
          <div class="applicant-name">{{ application.name }}</div>
          <div class="status-badge" :class="statusClass">
            {{ statusText }}
          </div>
        </div>

        <div class="applicant-details">
          <div class="contact-info">
            <span class="email" v-if="application.email">
              📧 {{ application.email }}
            </span>
            <span class="phone" v-if="application.phone">
              📱 {{ application.phone }}
            </span>
          </div>

          <div class="vacancy-info" v-if="application.vacancy">
            📋 {{ application.vacancy.title }}
          </div>
        </div>
      </div>

      <div class="preview-meta">
        <div class="timestamp">{{ formattedDate }}</div>
        <div class="attachment-indicator" v-if="hasAttachment">
          📎
        </div>
      </div>
    </div>

    <div class="preview-message" v-if="application.applicant_message">
      {{ truncatedMessage }}
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'

export default {
  name: 'ApplicationPreview',
  props: {
    application: {
      type: Object,
      required: true
    }
  },
  emits: ['click'],
  setup(props) {
    const statusClass = computed(() => {
      return props.application.is_processed ? 'processed' : 'unprocessed'
    })

    const statusText = computed(() => {
      return props.application.is_processed ? '✅' : '❌'
    })

    const formattedDate = computed(() => {
      const date = new Date(props.application.created_at)
      const now = new Date()
      const diffInHours = (now - date) / (1000 * 60 * 60)

      if (diffInHours < 1) {
        const minutes = Math.floor(diffInHours * 60)
        return minutes < 1 ? 'Только что' : `${minutes}м`
      } else if (diffInHours < 24) {
        return `${Math.floor(diffInHours)}ч`
      } else if (diffInHours < 48) {
        return 'Вчера'
      } else {
        return date.toLocaleDateString('ru-RU', {
          day: '2-digit',
          month: '2-digit'
        })
      }
    })

    const hasAttachment = computed(() => {
      return !!(props.application.attachment_filename || props.application.file_path || props.application.file_url)
    })

    const truncatedMessage = computed(() => {
      const message = props.application.applicant_message
      if (!message) return ''
      return message.length > 80 ? message.substring(0, 80) + '...' : message
    })

    return {
      statusClass,
      statusText,
      formattedDate,
      hasAttachment,
      truncatedMessage
    }
  }
}
</script>

<style scoped>
.application-preview {
  background: var(--tg-theme-secondary-bg-color, #f2f2f7);
  border: 1px solid var(--tg-theme-hint-color, #e5e5ea);
  border-radius: 12px;
  padding: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
}

.application-preview:active {
  transform: scale(0.98);
  background: var(--tg-theme-hint-color, #e5e5ea);
}

.application-preview.unprocessed {
  border-left: 4px solid #ff3b30;
  background: linear-gradient(135deg, rgba(255, 59, 48, 0.02) 0%, var(--tg-theme-secondary-bg-color, #f2f2f7) 100%);
}

.preview-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.applicant-info {
  flex: 1;
  min-width: 0;
}

.applicant-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 6px;
}

.applicant-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--tg-theme-text-color, #000000);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.status-badge {
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 8px;
  flex-shrink: 0;
}

.status-badge.processed {
  background: rgba(0, 199, 60, 0.1);
  color: #00c73c;
}

.status-badge.unprocessed {
  background: rgba(255, 59, 48, 0.1);
  color: #ff3b30;
}

.applicant-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.contact-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.email,
.phone,
.vacancy-info {
  font-size: 12px;
  color: var(--tg-theme-hint-color, #8e8e93);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.vacancy-info {
  font-weight: 500;
  color: var(--tg-theme-accent-text-color, #3390ec);
}

.preview-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  flex-shrink: 0;
}

.timestamp {
  font-size: 11px;
  color: var(--tg-theme-hint-color, #8e8e93);
  font-weight: 500;
}

.attachment-indicator {
  font-size: 14px;
  opacity: 0.7;
}

.preview-message {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--tg-theme-hint-color, #e5e5ea);
  font-size: 13px;
  color: var(--tg-theme-text-color, #000000);
  line-height: 1.3;
  opacity: 0.8;
}

/* Dark theme adjustments */
.application-preview {
  background: var(--tg-theme-secondary-bg-color, #1c1c1e);
  border-color: var(--tg-theme-hint-color, #38383a);
}

.application-preview:active {
  background: var(--tg-theme-hint-color, #38383a);
}

.application-preview.unprocessed {
  background: linear-gradient(135deg, rgba(255, 59, 48, 0.05) 0%, var(--tg-theme-secondary-bg-color, #1c1c1e) 100%);
}

.preview-message {
  border-top-color: var(--tg-theme-hint-color, #38383a);
}

/* Responsive adjustments */
@media (max-width: 360px) {
  .application-preview {
    padding: 10px;
  }

  .applicant-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }

  .applicant-name {
    font-size: 14px;
  }

  .preview-content {
    flex-direction: column;
    gap: 8px;
  }

  .preview-meta {
    flex-direction: row;
    justify-content: space-between;
    width: 100%;
  }

  .contact-info {
    flex-direction: row;
    gap: 8px;
    flex-wrap: wrap;
  }
}

/* Accessibility */
@media (prefers-reduced-motion: reduce) {
  .application-preview {
    transition: none;
  }

  .application-preview:active {
    transform: none;
  }
}

/* Focus styles */
.application-preview:focus {
  outline: 2px solid var(--tg-theme-accent-text-color, #3390ec);
  outline-offset: 2px;
}

/* Hover effects for non-touch devices */
@media (hover: hover) {
  .application-preview:hover {
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  .application-preview.unprocessed:hover {
    box-shadow: 0 2px 8px rgba(255, 59, 48, 0.2);
  }
}
</style>