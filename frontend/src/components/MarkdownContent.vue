<script setup lang="ts">
import MarkdownIt from 'markdown-it'
import { computed } from 'vue'

const props = defineProps<{ content: string }>()

const markdown = new MarkdownIt({
  breaks: true,
  html: false,
  linkify: true,
  typographer: true,
})

const defaultLinkOpen = markdown.renderer.rules.link_open
markdown.renderer.rules.link_open = (tokens, idx, options, env, self) => {
  const token = tokens[idx]
  const targetIndex = token.attrIndex('target')
  const relIndex = token.attrIndex('rel')
  if (targetIndex < 0) token.attrPush(['target', '_blank'])
  else token.attrs![targetIndex][1] = '_blank'
  if (relIndex < 0) token.attrPush(['rel', 'noreferrer noopener'])
  else token.attrs![relIndex][1] = 'noreferrer noopener'
  return defaultLinkOpen ? defaultLinkOpen(tokens, idx, options, env, self) : self.renderToken(tokens, idx, options)
}

const html = computed(() => markdown.render(props.content || ''))
</script>

<template>
  <div class="markdown-content" v-html="html" />
</template>

<style scoped>
.markdown-content { min-width: 0; color: inherit; overflow-wrap: anywhere; word-break: break-word; }
.markdown-content :deep(*) { box-sizing: border-box; }
.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3),
.markdown-content :deep(h4),
.markdown-content :deep(h5),
.markdown-content :deep(h6) { margin: 1.1em 0 0.45em; color: var(--text-title); font-weight: var(--font-weight-semibold); line-height: 1.35; letter-spacing: 0; }
.markdown-content :deep(h1) { font-size: var(--font-size-xl); }
.markdown-content :deep(h2) { font-size: var(--font-size-lg); }
.markdown-content :deep(h3) { font-size: var(--font-size-md); }
.markdown-content :deep(h4),
.markdown-content :deep(h5),
.markdown-content :deep(h6) { font-size: var(--font-size-sm); }
.markdown-content :deep(h1:first-child),
.markdown-content :deep(h2:first-child),
.markdown-content :deep(h3:first-child),
.markdown-content :deep(p:first-child),
.markdown-content :deep(ul:first-child),
.markdown-content :deep(ol:first-child),
.markdown-content :deep(blockquote:first-child),
.markdown-content :deep(pre:first-child),
.markdown-content :deep(table:first-child) { margin-top: 0; }
.markdown-content :deep(p) { margin: 0.6em 0; }
.markdown-content :deep(p:last-child),
.markdown-content :deep(ul:last-child),
.markdown-content :deep(ol:last-child),
.markdown-content :deep(blockquote:last-child),
.markdown-content :deep(pre:last-child),
.markdown-content :deep(table:last-child) { margin-bottom: 0; }
.markdown-content :deep(a) { color: var(--color-primary-700); font-weight: var(--font-weight-medium); text-decoration: underline; text-underline-offset: 3px; }
.markdown-content :deep(strong) { color: var(--text-title); font-weight: var(--font-weight-semibold); }
.markdown-content :deep(em) { color: inherit; }
.markdown-content :deep(s) { color: var(--text-secondary); }
.markdown-content :deep(ul),
.markdown-content :deep(ol) { margin: 0.7em 0; padding-left: 1.35em; }
.markdown-content :deep(li) { margin: 0.28em 0; padding-left: 0.1em; }
.markdown-content :deep(li > ul),
.markdown-content :deep(li > ol) { margin: 0.35em 0; }
.markdown-content :deep(blockquote) { margin: 0.9em 0; padding: var(--space-2) var(--space-3); border-left: 3px solid var(--color-primary-300); border-radius: var(--radius-sm); background: var(--bg-subtle); color: var(--text-secondary); }
.markdown-content :deep(code) { padding: 0.12em 0.36em; border-radius: var(--radius-sm); background: var(--bg-subtle); color: var(--color-primary-700); font-family: var(--font-family-code); font-size: 0.92em; }
.markdown-content :deep(pre) { max-width: 100%; margin: 0.9em 0; padding: var(--space-3); overflow-x: auto; border: 1px solid var(--border-default); border-radius: var(--radius-md); background: var(--color-gray-900); color: var(--color-gray-50); line-height: 1.55; }
.markdown-content :deep(pre code) { display: block; min-width: max-content; padding: 0; background: transparent; color: inherit; white-space: pre; }
.markdown-content :deep(table) { display: block; width: max-content; max-width: 100%; margin: 0.9em 0; overflow-x: auto; border-collapse: collapse; border: 1px solid var(--border-default); border-radius: var(--radius-md); background: var(--bg-card); font-size: var(--font-size-sm); }
.markdown-content :deep(th),
.markdown-content :deep(td) { padding: var(--space-2) var(--space-3); border: 1px solid var(--border-default); text-align: left; vertical-align: top; }
.markdown-content :deep(th) { background: var(--bg-subtle); color: var(--text-title); font-weight: var(--font-weight-semibold); }
.markdown-content :deep(hr) { height: 1px; margin: var(--space-4) 0; border: 0; background: var(--border-default); }
.markdown-content :deep(img) { max-width: 100%; height: auto; border-radius: var(--radius-md); }
</style>
