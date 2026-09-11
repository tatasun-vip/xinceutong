import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/pages/Home.vue'),
      meta: { title: '首页' },
    },
    {
      path: '/banks',
      name: 'banks',
      component: () => import('@/pages/BankSelect.vue'),
      meta: { title: '选择银行' },
    },
    {
      path: '/assess/:bankCode',
      name: 'assess',
      component: () => import('@/pages/Assess.vue'),
      meta: { title: '测评' },
    },
    {
      path: '/loading',
      name: 'loading',
      component: () => import('@/pages/Loading.vue'),
      meta: { title: '测评中' },
    },
    {
      path: '/result/:id',
      name: 'result',
      component: () => import('@/pages/Result.vue'),
      meta: { title: '测评结果' },
    },
    {
      path: '/disclaimer',
      name: 'disclaimer',
      component: () => import('@/pages/Disclaimer.vue'),
      meta: { title: '免责声明' },
    },
  ],
  scrollBehavior() {
    return { top: 0 }
  },
})

router.afterEach((to) => {
  document.title = `${to.meta.title || ''} · 信测通`
})

export default router
