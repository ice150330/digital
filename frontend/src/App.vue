<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppLayout from './layouts/AppLayout.vue'

const route = useRoute()
// /screen 大屏绕过工作台布局（meta.fullscreen）
const fullscreen = computed(() => Boolean(route.meta.fullscreen))
</script>

<template>
  <router-view v-if="fullscreen" />
  <AppLayout v-else>
    <!-- Stage 6：路由切换轻 fade（150ms，reduced-motion 关闭） -->
    <router-view v-slot="{ Component }">
      <Transition name="route-fade" mode="out-in">
        <component :is="Component" />
      </Transition>
    </router-view>
  </AppLayout>
</template>
