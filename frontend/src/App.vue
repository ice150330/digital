<script setup lang="ts">
import AppLayout from './layouts/AppLayout.vue'
</script>

<template>
  <AppLayout>
    <!-- Stage 6：路由切换轻 fade（150ms，reduced-motion 关闭） -->
    <router-view v-slot="{ Component }">
      <Transition name="route-fade" mode="out-in">
        <component :is="Component" />
      </Transition>
    </router-view>
  </AppLayout>
</template>
