import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('../views/HomeView.vue'),
      meta: { title: '总览' },
    },
    {
      path: '/models',
      name: 'models',
      component: () => import('../views/ModelsView.vue'),
      meta: { title: '模型实验室' },
    },
    {
      path: '/customers',
      name: 'customers',
      component: () => import('../views/CustomersView.vue'),
      meta: { title: '客户洞察' },
    },
    {
      path: '/segments',
      name: 'segments',
      component: () => import('../views/SegmentsView.vue'),
      meta: { title: '分群画像' },
    },
    {
      path: '/rules',
      name: 'rules',
      component: () => import('../views/RulesView.vue'),
      meta: { title: '关联规则' },
    },
    {
      path: '/agent',
      name: 'agent',
      component: () => import('../views/AgentView.vue'),
      meta: { title: 'AI 分析台' },
    },
    {
      path: '/about',
      name: 'about',
      component: () => import('../views/AboutView.vue'),
      meta: { title: '关于与复现' },
    },
  ],
})

router.afterEach((to) => {
  const title = (to.meta.title as string) || '营销转化分析'
  document.title = `${title} · 营销转化分析`
})

export default router
