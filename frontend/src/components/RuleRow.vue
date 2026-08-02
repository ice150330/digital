<script setup lang="ts">
import type { RuleRow as RuleDataRow } from '../api/rules'
import { formatMetric } from '../utils/format'
import Icon from './Icon.vue'
import Tag from './Tag.vue'

defineProps<{ rule: RuleDataRow }>()

function splitItems(value: string): string[] {
  return value.split(/[,，|]/).map((item) => item.trim()).filter(Boolean)
}
</script>

<template>
  <div class="rule-row">
    <div class="rule-expression">
      <div class="rule-items">
        <Tag v-for="item in splitItems(rule.antecedents)" :key="item" tone="neutral">{{ item }}</Tag>
      </div>
      <span class="rule-arrow"><Icon icon="uil:arrow-right" size="md" /><span class="sr-only">指向</span></span>
      <div class="rule-items">
        <Tag v-for="item in splitItems(rule.consequents)" :key="item" tone="primary">{{ item }}</Tag>
      </div>
    </div>
    <div class="rule-metrics">
      <div><span>support</span><strong>{{ formatMetric(rule.support) }}</strong></div>
      <div><span>confidence</span><strong>{{ formatMetric(rule.confidence) }}</strong></div>
      <div class="lift"><span>lift</span><strong>{{ formatMetric(rule.lift) }}</strong></div>
    </div>
  </div>
</template>

<style scoped>
.rule-row { display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: center; gap: var(--space-5); padding: var(--space-4); border: 1px solid var(--border-default); border-radius: var(--radius-card); background: var(--bg-card); }
.rule-expression { display: flex; min-width: 0; align-items: center; gap: var(--space-3); }
.rule-items { display: flex; min-width: 0; flex-wrap: wrap; gap: var(--space-2); }
.rule-arrow { display: inline-flex; flex: 0 0 auto; color: var(--color-primary-500); }
.rule-metrics { display: grid; grid-template-columns: repeat(3, minmax(76px, auto)); gap: var(--space-4); }
.rule-metrics div { padding-left: var(--space-3); border-left: 1px solid var(--border-default); }
.rule-metrics span, .rule-metrics strong { display: block; }
.rule-metrics span { color: var(--text-secondary); font-size: var(--font-size-xs); }
.rule-metrics strong { margin-top: var(--space-1); color: var(--text-title); font-family: var(--font-family-number); font-size: var(--font-size-sm); }
.rule-metrics .lift strong { color: var(--color-primary-700); }
@media (max-width: 860px) { .rule-row { grid-template-columns: 1fr; } .rule-metrics { justify-content: start; } }
</style>
