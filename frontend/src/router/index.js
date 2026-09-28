import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import HomeView from '../views/HomeView.vue'
import CatalogView from '../views/CatalogView.vue'
import PickView from '../views/PickView.vue'
import SimulationView from '../views/SimulationView.vue'
import AccountView from '../views/AccountView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/catalog',
      name: 'catalog',
      component: CatalogView,
      meta: { requiresAuth: true },
    },
    {
      path: '/pick',
      name: 'pick',
      component: PickView,
      meta: { requiresAuth: true },
    },
    {
      path: '/simulation',
      name: 'simulation',
      component: SimulationView,
      meta: { requiresAuth: true },
    },
    {
      path: '/account',
      name: 'account',
      component: AccountView,
      meta: { requiresAuth: true },
    },
  ],
})

router.beforeEach((to) => {
  if (!to.meta.requiresAuth) return true
  const auth = useAuthStore()
  if (auth.user) return true
  return {
    path: '/',
    query: { auth: 'login', redirect: to.fullPath },
  }
})

export default router
