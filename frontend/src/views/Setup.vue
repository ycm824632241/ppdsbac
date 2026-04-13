<template>
<div>
  <div class="pc">
    <div class="pt">⚙️ 系统初始化</div>
    <div class="pd">按顺序完成全局参数生成和各实体密钥建立。</div>

    <el-steps :active="step" finish-status="success" style="margin-bottom:24px">
      <el-step title="全局参数" description="双线性群初始化"/>
      <el-step title="RA / TA 密钥" description="注册/追踪机构"/>
      <el-step title="AA 密钥群" description="授权机构"/>
      <el-step title="用户注册" description="密钥生成与注册"/>
    </el-steps>

    <el-card class="step-card" shadow="never">
      <template #header>
        <span class="step-title">Step 1 — 全局参数初始化</span>
        <el-tag v-if="res.global" type="success" size="small" style="float:right">✓ 完成</el-tag>
      </template>
      <p class="step-desc">生成双线性群公共参数，包含群生成元、哈希函数参数等系统级公开参数。</p>
      <el-button type="primary" :loading="loading.global" @click="doGlobal">执行初始化</el-button>
      <div v-if="res.global" style="margin-top:14px">
        <div class="section-hd" style="font-size:13px">公共参数</div>
        <div v-for="(v,k) in res.global.params" :key="k" style="margin-bottom:6px">
          <span class="param-key">{{ k }}</span>
          <span class="hex" style="display:inline">{{ v }}</span>
        </div>
      </div>
    </el-card>

    <el-card class="step-card" shadow="never">
      <template #header>
        <span class="step-title">Step 2 — 注册机构 & 追踪机构密钥生成</span>
        <el-tag v-if="res.ra && res.ta" type="success" size="small" style="float:right">✓ 完成</el-tag>
      </template>
      <p class="step-desc">注册机构（RA）和追踪机构（TA）各自生成独立的密钥对。</p>
      <el-button type="primary" :loading="loading.ra" @click="doRA" :disabled="!res.global">RA 密钥生成</el-button>
      <el-button type="primary" :loading="loading.ta" @click="doTA" :disabled="!res.global" style="margin-left:10px">TA 密钥生成</el-button>
      <div v-if="res.ra" style="margin-top:12px">
        <div class="section-hd" style="font-size:13px">RA 公钥</div>
        <div class="hex">{{ res.ra.PK_RA_hex }}</div>
      </div>
      <div v-if="res.ta" style="margin-top:10px">
        <div class="section-hd" style="font-size:13px">TA 公钥</div>
        <div class="hex">{{ res.ta.PK_TA_hex }}</div>
      </div>
    </el-card>

    <el-card class="step-card" shadow="never">
      <template #header>
        <span class="step-title">Step 3 — 授权机构密钥生成</span>
        <el-tag v-if="res.aas" type="success" size="small" style="float:right">✓ 完成（{{ res.aas.length }} 个）</el-tag>
      </template>
      <p class="step-desc">各授权机构（AA）独立生成密钥对，机构之间无需任何交互。</p>
      <el-input-number v-model="nAA" :min="1" :max="10" style="width:120px;margin-right:12px"/>
      <el-button type="primary" :loading="loading.aa" @click="doAA" :disabled="!res.ra">生成 AA 密钥群</el-button>
      <div v-if="res.aas" style="margin-top:14px">
        <el-table :data="res.aas" size="small" stripe>
          <el-table-column prop="aa_id" label="机构ID" width="80"/>
          <el-table-column label="公钥（截取）">
            <template #default="{row}">
              <span class="hex" style="font-size:11px">{{ row.PK_j_hex.slice(0,34) }}…</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>

    <el-card class="step-card" shadow="never">
      <template #header>
        <span class="step-title">Step 4 — 用户密钥生成与注册</span>
        <el-tag v-if="res.regist" type="success" size="small" style="float:right">✓ 注册完成</el-tag>
      </template>
      <p class="step-desc">用户生成密钥对，向注册机构提交零知识证明，获取匿名凭证。</p>
      <el-input v-model="userId" placeholder="用户ID（如 Alice）" style="width:160px;margin-right:10px"/>
      <el-button type="primary" :loading="loading.user" @click="doUser" :disabled="!res.aas">生成用户密钥</el-button>
      <el-button type="success" :loading="loading.regist" @click="doRegist" :disabled="!res.userKey" style="margin-left:8px">向RA注册</el-button>
      <div v-if="res.userKey" style="margin-top:12px">
        <div class="section-hd" style="font-size:13px">用户公钥</div>
        <div class="hex">{{ res.userKey.PK_U_hex }}</div>
      </div>
      <div v-if="res.regist" style="margin-top:10px">
        <el-alert type="success" :closable="false">
          <div>零知识证明验证：<b class="ok">{{ res.regist.zk_verified ? '通过 ✓' : '失败' }}</b></div>
          <div style="margin-top:6px">匿名凭证 σ_U：</div>
          <div class="hex" style="margin-top:4px">{{ res.regist.sigma_U_hex }}</div>
        </el-alert>
      </div>
    </el-card>

    <el-alert v-if="step >= 4" type="success" :closable="false" style="margin-top:8px">
      🎉 系统初始化完成！
      <el-button type="primary" size="small" @click="$router.push('/demo')" style="margin-left:12px">前往完整演示 →</el-button>
    </el-alert>
  </div>
</div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { setupApi } from '../api/index.js'
import { useSystemStore } from '../stores/system.js'
const store = useSystemStore()
const nAA = ref(3)
const userId = ref('Alice')
const res = ref({ global:null, ra:null, ta:null, aas:null, userKey:null, regist:null })
const loading = ref({ global:false, ra:false, ta:false, aa:false, user:false, regist:false })
const step = computed(() => {
  if (res.value.regist) return 4
  if (res.value.aas)    return 3
  if (res.value.ra && res.value.ta) return 2
  if (res.value.global) return 1
  return 0
})
async function call(key, fn) {
  loading.value[key] = true
  try {
    const { data } = await fn()
    ElMessage.success(data.msg || '操作成功')
    return data
  } catch(e) {
    ElMessage.error(e.response?.data?.error || '请求失败')
    return null
  } finally { loading.value[key] = false; store.refresh() }
}
async function doGlobal() { const d = await call('global', setupApi.globalSetup); if(d) res.value.global = d }
async function doRA()     { const d = await call('ra', setupApi.raSetup);         if(d) res.value.ra = d }
async function doTA()     { const d = await call('ta', setupApi.taSetup);         if(d) res.value.ta = d }
async function doAA()     { const d = await call('aa', ()=>setupApi.aaSetup(nAA.value)); if(d) res.value.aas = d.aas }
async function doUser()   { const d = await call('user', ()=>setupApi.userSetup(userId.value)); if(d) res.value.userKey = d }
async function doRegist() { const d = await call('regist', ()=>setupApi.regist(userId.value)); if(d) res.value.regist = d }
</script>
<style scoped>
.step-card{margin-bottom:16px;border:1px solid #e8ecf0;border-radius:10px}
.step-title{font-size:14px;font-weight:600;color:#151d2e}
.step-desc{font-size:12px;color:#666;margin-bottom:12px;line-height:1.6}
.param-key{display:inline-block;width:40px;font-size:11px;color:#909399;font-family:monospace;font-weight:600;margin-right:8px}
</style>
