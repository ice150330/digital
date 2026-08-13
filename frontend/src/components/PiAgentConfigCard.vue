<script setup lang="ts">
import { computed, reactive, watch } from 'vue'
import {
  ElAlert,
  ElButton,
  ElCard,
  ElCheckbox,
  ElForm,
  ElFormItem,
  ElInput,
  ElInputNumber,
  ElOption,
  ElSelect,
  ElTag,
} from 'element-plus'
import type { PiAgentConfigData, PiAgentConfigUpdate, PiModelItemData } from '../api/agent'
import Icon from './Icon.vue'

const props = defineProps<{
  config: PiAgentConfigData | null
  loading?: boolean
  saving?: boolean
  error?: string | null
  models?: PiModelItemData[]
  modelsLoading?: boolean
  modelsError?: string | null
}>()

const emit = defineEmits<{
  save: [payload: PiAgentConfigUpdate]
  refresh: []
  refreshModels: []
}>()

const form = reactive({
  runtime: 'pi',
  bridge_model: 'deepseek/deepseek-chat',
  base_url: '',
  executable: 'tools/pi-cli/node_modules/.bin/pi',
  skills_dir: 'src/digital_marketing/agent/skills',
  session_dir: 'outputs/agent_sessions',
  pi_timeout_sec: 180,
  llm_timeout_sec: 60,
  api_key: '',
  clear_api_key: false,
})

watch(
  () => props.config?.settings,
  (settings) => {
    if (!settings) return
    form.runtime = settings.runtime || 'pi'
    form.bridge_model = settings.pi.bridge_model || 'deepseek/deepseek-chat'
    form.base_url = settings.llm.base_url || ''
    form.executable = settings.pi.executable || 'tools/pi-cli/node_modules/.bin/pi'
    form.skills_dir = settings.pi.skills_dir || 'src/digital_marketing/agent/skills'
    form.session_dir = settings.pi.session_dir || 'outputs/agent_sessions'
    form.pi_timeout_sec = settings.pi.timeout_sec || 180
    form.llm_timeout_sec = settings.llm.timeout_sec || 60
    form.api_key = ''
    form.clear_api_key = false
  },
  { immediate: true },
)

const status = computed(() => props.config?.status ?? null)
const settings = computed(() => props.config?.settings ?? null)
const apiKeyLabel = computed(() => {
  if (settings.value?.llm.api_key_configured) {
    return `已配置 ${settings.value.llm.api_key_preview || ''}`.trim()
  }
  return '未配置'
})
const healthType = computed(() => {
  if (!status.value) return 'info'
  if (status.value.installed && !status.value.is_stub && status.value.bridge_ready) return 'success'
  if (!status.value.valid_prefix) return 'danger'
  return 'warning'
})
const healthText = computed(() => {
  if (!status.value) return '读取中'
  if (!status.value.valid_prefix) return '路径非法'
  if (!status.value.installed) return '未安装'
  if (status.value.is_stub) return 'stub 占位'
  if (!status.value.bridge_ready) return '桥接未就绪'
  return 'Pi 可用'
})
const modelProvider = computed(() => {
  const raw = form.bridge_model.split('/')[0]?.trim()
  return raw || 'deepseek'
})
const modelOptions = computed(() => (props.models || []).map((item) => {
  const value = item.id.includes('/') ? item.id : `${modelProvider.value}/${item.id}`
  const owner = item.owned_by ? ` · ${item.owned_by}` : ''
  return { value, label: item.label || item.id, owner }
}))

function save() {
  const payload: PiAgentConfigUpdate = {
    runtime: form.runtime,
    llm: {
      base_url: form.base_url.trim(),
      timeout_sec: form.llm_timeout_sec,
    },
    pi: {
      executable: form.executable.trim(),
      skills_dir: form.skills_dir.trim(),
      session_dir: form.session_dir.trim(),
      timeout_sec: form.pi_timeout_sec,
      bridge_model: form.bridge_model.trim(),
    },
    clear_api_key: form.clear_api_key,
  }
  const apiKey = form.api_key.trim()
  if (apiKey && !form.clear_api_key) payload.api_key = apiKey
  emit('save', payload)
}
</script>

<template>
  <ElCard shadow="never" class="pi-config-card">
    <template #header>
      <div class="card-head">
        <div>
          <div class="eyebrow">PiAgent Settings</div>
          <h2>运行配置</h2>
        </div>
        <div class="head-actions">
          <ElTag :type="healthType" effect="light" round>{{ healthText }}</ElTag>
          <ElButton :loading="loading" @click="emit('refresh')">
            <Icon icon="uil:sync" size="sm" />
          </ElButton>
        </div>
      </div>
    </template>

    <ElAlert
      v-if="error"
      :title="error"
      type="error"
      show-icon
      :closable="false"
      class="config-alert"
    />

    <div class="status-strip">
      <div class="status-item">
        <span>runtime</span>
        <strong class="mono">{{ settings?.runtime || '—' }}</strong>
      </div>
      <div class="status-item">
        <span>model</span>
        <strong class="mono">{{ settings?.pi.bridge_model || '—' }}</strong>
      </div>
      <div class="status-item">
        <span>api key</span>
        <strong>{{ apiKeyLabel }}</strong>
      </div>
      <div class="status-item">
        <span>bridge</span>
        <strong>{{ status?.bridge_ready ? 'ready' : (status?.bridge_note || 'pending') }}</strong>
      </div>
    </div>

    <ElForm label-position="top" class="config-form" @submit.prevent>
      <div class="form-grid">
        <ElFormItem label="Runtime">
          <ElSelect v-model="form.runtime" class="w-full">
            <ElOption label="pi" value="pi" />
            <ElOption label="local" value="local" />
            <ElOption label="template" value="template" />
          </ElSelect>
        </ElFormItem>

        <ElFormItem label="Bridge Model">
          <template #label>
            <div class="field-label">
              <span>Bridge Model</span>
              <ElButton
                size="small"
                link
                type="primary"
                :loading="modelsLoading"
                @click="emit('refreshModels')"
              >
                刷新模型
              </ElButton>
            </div>
          </template>
          <ElSelect
            v-model="form.bridge_model"
            filterable
            allow-create
            default-first-option
            :reserve-keyword="false"
            :loading="modelsLoading"
            class="w-full"
            placeholder="deepseek/deepseek-chat"
          >
            <ElOption
              v-for="item in modelOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            >
              <span class="model-option-main mono">{{ item.value }}</span>
              <span v-if="item.owner" class="model-option-owner">{{ item.owner }}</span>
            </ElOption>
          </ElSelect>
          <p v-if="modelsError" class="field-error">{{ modelsError }}</p>
          <p v-else-if="modelOptions.length" class="field-note">已从上游获取 {{ modelOptions.length }} 个模型。</p>
        </ElFormItem>

        <ElFormItem label="Base URL">
          <ElInput v-model="form.base_url" placeholder="https://api.deepseek.com" />
        </ElFormItem>

        <ElFormItem label="Pi executable">
          <ElInput v-model="form.executable" placeholder="tools/pi-cli/node_modules/.bin/pi" />
        </ElFormItem>

        <ElFormItem label="Skills 目录">
          <ElInput v-model="form.skills_dir" placeholder="src/digital_marketing/agent/skills" />
        </ElFormItem>

        <ElFormItem label="Session 目录">
          <ElInput v-model="form.session_dir" placeholder="outputs/agent_sessions" />
        </ElFormItem>

        <ElFormItem label="Pi timeout（秒）">
          <ElInputNumber v-model="form.pi_timeout_sec" :min="30" :max="300" :step="10" class="w-full" />
        </ElFormItem>

        <ElFormItem label="LLM timeout（秒）">
          <ElInputNumber v-model="form.llm_timeout_sec" :min="5" :max="180" :step="5" class="w-full" />
        </ElFormItem>
      </div>

      <div class="secret-row">
        <ElFormItem label="DEEPSEEK_API_KEY">
          <ElInput
            v-model="form.api_key"
            type="password"
            show-password
            autocomplete="new-password"
            :disabled="form.clear_api_key"
            placeholder="留空则保持现有密钥"
          />
        </ElFormItem>
        <ElCheckbox v-model="form.clear_api_key" class="clear-key">
          清除本地密钥
        </ElCheckbox>
      </div>

      <div class="form-actions">
        <span class="muted">
          密钥只写入本地 .env；接口只返回是否配置与掩码。
        </span>
        <ElButton type="primary" :loading="saving" @click="save">
          保存配置
        </ElButton>
      </div>
    </ElForm>
  </ElCard>
</template>

<style scoped>
.pi-config-card {
  border-radius: var(--radius-card);
  overflow: hidden;
}
.card-head,
.head-actions,
.form-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}
.eyebrow {
  color: var(--color-primary-600);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  text-transform: uppercase;
}
h2 {
  margin: var(--space-1) 0 0;
  font-size: var(--font-size-xl);
  line-height: 1.2;
}
.config-alert {
  margin-bottom: var(--space-3);
}
.status-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--space-3);
  margin-bottom: var(--space-4);
}
.status-item {
  min-width: 0;
  padding: var(--space-3);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  background: var(--bg-tile);
}
.status-item span {
  display: block;
  color: var(--text-secondary);
  font-size: var(--font-size-xs);
  margin-bottom: var(--space-1);
  text-transform: uppercase;
}
.status-item strong {
  display: block;
  min-width: 0;
  overflow: hidden;
  color: var(--text-title);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  text-overflow: ellipsis;
  white-space: nowrap;
}
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-3);
}
.field-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}
.field-note,
.field-error {
  margin: var(--space-1) 0 0;
  font-size: var(--font-size-xs);
  line-height: 1.4;
}
.field-note {
  color: var(--text-secondary);
}
.field-error {
  color: var(--color-danger-text);
}
.model-option-main {
  font-size: var(--font-size-xs);
}
.model-option-owner {
  float: right;
  color: var(--text-secondary);
  font-size: var(--font-size-xs);
}
.secret-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: end;
  gap: var(--space-3);
}
.clear-key {
  margin-bottom: 18px;
}
.form-actions {
  padding-top: var(--space-2);
}
@media (max-width: 992px) {
  .status-strip,
  .form-grid,
  .secret-row {
    grid-template-columns: 1fr;
  }
  .card-head,
  .form-actions {
    align-items: flex-start;
    flex-direction: column;
  }
  .head-actions {
    width: 100%;
    justify-content: space-between;
  }
  .clear-key {
    margin-bottom: 0;
  }
}
</style>
