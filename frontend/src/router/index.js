import { createRouter, createWebHistory } from 'vue-router'
import Home      from '../views/Home.vue'
import Setup     from '../views/Setup.vue'
import Workflow  from '../views/Workflow.vue'
import Security  from '../views/Security.vue'
import Benchmark from '../views/Benchmark.vue'
import FullDemo  from '../views/FullDemo.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/',          component: Home      },
    { path: '/setup',     component: Setup     },
    { path: '/workflow',  component: Workflow  },
    { path: '/security',  component: Security  },
    { path: '/benchmark', component: Benchmark },
    { path: '/demo',      component: FullDemo  },
  ]
})
