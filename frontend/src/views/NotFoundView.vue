<script setup lang="ts">
import { useRouter } from 'vue-router'
import Button from '../components/Button.vue'
import EmptyState from '../components/EmptyState.vue'

const router = useRouter()
function goHome() {
  router.push('/screen')
}
</script>

<template>
  <div class="page">
    <EmptyState
      icon="uil:exclamation-triangle"
      title="页面不存在或地址有误"
      description="请检查 URL，或返回总览大屏继续。"
    >
      <Button variant="primary" icon="uil:desktop-alt" @click="goHome">
        返回总览大屏
      </Button>
    </EmptyState>
  </div>
</template>
