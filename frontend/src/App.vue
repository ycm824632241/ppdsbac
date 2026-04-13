<template>
  <el-container class="app-root">
    <el-aside width="230px" class="sidebar">
      <div class="logo-area">
        <div class="logo-icon">🔐</div>
        <div>
          <div class="logo-name">PPDSBAC</div>
          <div class="logo-meta">IEEE TDSC 2025</div>
        </div>
      </div>

      <el-menu :default-active="route.path" router class="side-menu" background-color="transparent">
        <el-menu-item v-for="r in nav" :key="r.path" :index="r.path">
          <span class="nav-ico">{{ r.ico }}</span><span>{{ r.label }}</span>
        </el-menu-item>
      </el-menu>

      <div class="side-status">
        <div class="status-item">
          <span class="dot" :class="store.initialized?'on':'off'"/>
          系统{{ store.initialized ? '已初始化':'未初始化' }}
        </div>
        <div class="status-item">
          <span class="dot" :class="store.numAAs>0?'on':'off'"/>
          {{ store.numAAs }} 个授权机构 (AA)
        </div>
        <div class="status-item">
          <span class="dot" :class="store.users.length>0?'on':'off'"/>
          {{ store.users.length }} 个用户
        </div>
      </div>
    </el-aside>

    <el-main class="main-area">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useSystemStore } from './stores/system.js'
const route = useRoute()
const store = useSystemStore()
onMounted(() => store.refresh())

const nav = [
  { path:'/',          ico:'🏠', label:'系统概览'   },
  { path:'/setup',     ico:'⚙️', label:'系统初始化' },
  { path:'/workflow',  ico:'🔄', label:'协议流程'   },
  { path:'/security',  ico:'🛡️', label:'安全属性'   },
  { path:'/benchmark', ico:'📊', label:'性能评估'   },
  { path:'/demo',      ico:'🎬', label:'完整演示'   },
]
</script>

<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'PingFang SC','Microsoft YaHei',sans-serif;background:#f0f2f5}
.app-root{height:100vh}

.sidebar{background:#151d2e;display:flex;flex-direction:column;overflow:hidden}
.logo-area{display:flex;align-items:center;gap:10px;padding:20px 18px 16px;
  border-bottom:1px solid rgba(255,255,255,.07)}
.logo-icon{font-size:30px}
.logo-name{color:#fff;font-size:15px;font-weight:700;letter-spacing:.5px}
.logo-meta{color:#6b7a8d;font-size:11px;margin-top:2px}

.side-menu{border-right:none!important;flex:1;padding:8px 0}
.side-menu .el-menu-item{color:#8899aa!important;height:44px;margin:2px 8px;
  border-radius:8px!important;font-size:14px}
.side-menu .el-menu-item:hover,.side-menu .el-menu-item.is-active{
  background:rgba(64,158,255,.18)!important;color:#5aadff!important}
.nav-ico{margin-right:9px;font-size:15px}

.side-status{padding:12px 18px 20px;border-top:1px solid rgba(255,255,255,.07)}
.status-item{display:flex;align-items:center;gap:7px;color:#6b7a8d;font-size:12px;margin-bottom:6px}
.dot{width:7px;height:7px;border-radius:50%;flex-shrink:0}
.dot.on{background:#52c41a}.dot.off{background:#555}

.main-area{padding:24px;overflow-y:auto;background:#f0f2f5}

/* ── shared page components ── */
.pc{background:#fff;border-radius:12px;padding:24px;margin-bottom:18px;
  box-shadow:0 1px 4px rgba(0,0,0,.06)}
.pt{font-size:19px;font-weight:700;color:#151d2e;margin-bottom:6px}
.pd{color:#666;font-size:13px;line-height:1.7;margin-bottom:18px}
.section-hd{font-size:15px;font-weight:600;color:#151d2e;margin:0 0 12px;
  display:flex;align-items:center;gap:8px}
.section-hd::before{content:'';width:4px;height:16px;background:#409eff;
  border-radius:2px;display:inline-block}
.hex{font-family:'Courier New',monospace;font-size:11px;background:#f5f7fa;
  border:1px solid #e4e7ed;border-radius:6px;padding:7px 11px;color:#409eff;
  word-break:break-all;line-height:1.6}
.formula{background:#f0f9ff;border-left:3px solid #409eff;border-radius:4px;
  padding:9px 13px;font-family:'Courier New',monospace;font-size:12px;color:#1a6fa8;margin:8px 0}
.ok{color:#52c41a;font-weight:600} .fail{color:#f5222d;font-weight:600}
.tag-row{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}
</style>
