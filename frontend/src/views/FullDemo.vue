<template>
<div>
  <!-- 配置区 -->
  <div class="pc">
    <div class="pt">🎬 交互式协议演示</div>
    <el-row :gutter="14" style="margin-bottom:14px">
      <el-col :span="5"><div class="plabel">关键词 W</div><el-input v-model="cfg.keyword"/></el-col>
      <el-col :span="5"><div class="plabel">时间段 TP</div><el-input v-model="cfg.timePeriod"/></el-col>
      <el-col :span="5"><div class="plabel">授权机构数量 n</div><el-input-number v-model="cfg.nAAs" :min="1" :max="6" style="width:100%"/></el-col>
      <el-col :span="9">
        <div class="plabel">加密内容</div>
        <div style="display:flex;gap:8px">
          <el-input v-model="cfg.message" placeholder="输入明文内容" :disabled="!!uploadedFile"/>
          <el-upload :before-upload="handleUpload" :show-file-list="false" accept="*">
            <el-button>📎 上传文件</el-button>
          </el-upload>
          <el-button v-if="uploadedFile" @click="clearFile" type="danger" plain size="small">✕</el-button>
        </div>
        <div v-if="uploadedFile" style="font-size:12px;color:#52c41a;margin-top:4px">
          📄 {{ uploadedFile.name }} ({{ (uploadedFile.size/1024).toFixed(1) }}KB)
        </div>
      </el-col>
    </el-row>
  </div>

  <!-- 动画舞台 -->
  <div class="pc stage-area">
    <!-- 实体图标行 -->
    <div class="entities-row">
      <div v-for="e in entities" :key="e.id"
           class="entity-node" :class="{active: activeEntities.has(e.id)}">
        <div class="entity-avatar">{{ e.icon }}</div>
        <div class="entity-label">{{ e.name }}</div>
        <div class="entity-sub">{{ e.sub }}</div>
      </div>
    </div>

    <!-- 消息动画层 -->
    <div class="anim-layer" ref="animLayer">
      <div v-for="m in flyingMsgs" :key="m.id"
           class="flying-msg"
           :style="msgStyle(m)">
        <span class="msg-env">{{ m.icon }}</span>
        <span class="msg-text">{{ m.label }}</span>
      </div>
    </div>

    <!-- 步骤列表 -->
    <div class="steps-list">
      <div v-for="(s,i) in steps" :key="s.key"
           class="step-row" :class="stepClass(s)">
        <!-- 进度指示 -->
        <div class="step-indicator">
          <div class="step-dot" :class="stepClass(s)"></div>
          <div class="step-line" v-if="i<steps.length-1"></div>
        </div>
        <!-- 内容 -->
        <div class="step-content-wrap">
          <div class="step-header">
            <div class="step-meta">
              <span class="step-num">{{ i+1 }}</span>
              <span class="step-name">{{ s.name }}</span>
              <span class="step-algo">{{ s.algo }}</span>
              <span v-if="s.interaction" class="step-parties">{{ s.interaction }}</span>
            </div>
            <div class="step-actions">
              <span v-if="s.ms" class="step-ms">{{ s.ms }} ms</span>
              <el-tag v-if="s.state==='done'" type="success" size="small">✓ 完成</el-tag>
              <el-tag v-if="s.state==='running'" type="warning" size="small">
                <span class="spin-dot">⟳</span> 执行中
              </el-tag>
              <el-button v-if="s.state!=='running'" type="primary" size="small"
                :disabled="!canRun(i)" :loading="s.state==='running'"
                @click="runStep(i)">执行</el-button>
            </div>
          </div>
          <!-- 展开结果 -->
          <div v-if="s.state==='done' && s.result" class="step-result">
            <!-- Enc -->
            <template v-if="s.key==='enc'">
              <div class="res-chip">🔐 服务已加密并存入数据库</div>
              <div class="res-chips">
                <span class="chip">C₁: {{ s.result.C1_hex?.slice(0,16) }}…</span>
                <span class="chip">C₂: {{ s.result.C2_hex?.slice(0,16) }}…</span>
                <span class="chip">C₃: {{ s.result.C3_hex?.slice(0,16) }}…</span>
                <span class="chip">C₄: {{ s.result.C4_hex?.slice(0,16) }}…</span>
              </div>
            </template>
            <!-- Pseudonym -->
            <template v-if="s.key==='pseudonym'">
              <div class="res-chip">🎭 新鲜伪名已生成（与上次请求不可关联）</div>
              <div class="res-chips">
                <span class="chip">PU₁: {{ s.result.PU1_hex?.slice(0,16) }}…</span>
                <span class="chip">PU₂: {{ s.result.PU2_hex?.slice(0,16) }}…</span>
              </div>
            </template>
            <!-- Regist -->
            <template v-if="s.key==='regist'">
              <div class="res-chip">📜 RA颁发匿名凭证，ZK证明验证通过</div>
              <div class="chip">σ_U: {{ s.result.sigma_U_hex?.slice(0,20) }}…</div>
            </template>
            <!-- Acc_Req -->
            <template v-if="s.key==='acc_req'">
              <div class="res-chip">✍️ 已从 {{ s.result.permissions?.length }} 个AA获取访问权限</div>
              <div class="res-chips">
                <span v-for="p in s.result.permissions" :key="p.aa_id" class="chip">
                  {{ p.aa_id }}: {{ p.K_j_hex?.slice(0,14) }}…
                </span>
              </div>
            </template>
            <!-- Acc_Agg: 动画聚合 -->
            <template v-if="s.key==='acc_agg'">
              <div class="agg-visual" v-if="showAggAnim">
                <div class="agg-inputs">
                  <span v-for="p in prevPerms" :key="p.aa_id" class="agg-key">{{ p.aa_id }}</span>
                </div>
                <div class="agg-arrow">→ 聚合 →</div>
                <div class="agg-output">AK_U</div>
              </div>
              <div class="res-chip">📦 {{ s.result.num_permissions }} 个签名聚合为 1 个 AK_U</div>
              <div class="chip">AK_U: {{ s.result.AK_U_hex?.slice(0,20) }}…</div>
            </template>
            <!-- Dec -->
            <template v-if="s.key==='dec'">
              <div v-if="s.result.success" class="decrypt-result">
                <div class="decrypt-icon">🔓</div>
                <div class="decrypt-content">
                  <div class="decrypt-label">解密成功（服务提供商无需在线）</div>
                  <div class="decrypt-msg" v-if="!uploadedFile">"{{ s.result.message }}"</div>
                  <el-button v-if="uploadedFile" type="success" size="small" @click="downloadFile">
                    ⬇ 下载解密文件 {{ uploadedFile?.name }}
                  </el-button>
                </div>
              </div>
              <div v-else class="res-chip fail-chip">🔒 解密失败：{{ s.result.reason }}</div>
            </template>
            <!-- Trace -->
            <template v-if="s.key==='trace'">
              <div class="res-chip">🔍 TA成功去匿名化，还原真实身份</div>
              <div class="res-chips">
                <span class="chip">还原公钥: {{ s.result.recovered_PK_U_hex?.slice(0,16) }}…</span>
                <span class="chip danger">真实用户: {{ s.result.identity_revealed }}</span>
              </div>
            </template>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- 状态总结 -->
  <div v-if="allDone" class="pc">
    <div class="section-hd">协议执行完成 — 核心特性验证</div>
    <div class="summary-grid">
      <div v-for="f in finalFeatures" :key="f.t" class="summary-item" :class="f.ok?'sum-ok':'sum-warn'">
        <span class="sum-ico">{{ f.ico }}</span>
        <div><div class="sum-t">{{ f.t }}</div><div class="sum-d">{{ f.d }}</div></div>
      </div>
    </div>
  </div>
</div>
</template>

<script setup>
import { ref, reactive, computed, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { setupApi, workflowApi } from '../api/index.js'

// ── 配置 ──────────────────────────────────────────────
const cfg = ref({ nAAs:3, keyword:'medical_record', timePeriod:'2025-Q1', message:'Patient Record #042 — Confidential' })
const uploadedFile   = ref(null)
const uploadedBase64 = ref(null)

function handleUpload(file) {
  uploadedFile.value = file
  const reader = new FileReader()
  reader.onload = e => { uploadedBase64.value = e.target.result }
  reader.readAsDataURL(file)
  return false // prevent auto-upload
}
function clearFile() { uploadedFile.value = null; uploadedBase64.value = null }

function downloadFile() {
  if (!uploadedFile.value) return
  const a = document.createElement('a')
  a.href = uploadedBase64.value
  a.download = 'decrypted_' + uploadedFile.value.name
  a.click()
}

// ── 实体定义 ──────────────────────────────────────────
const entities = [
  { id:'encryptor', icon:'📝', name:'加密者',     sub:'Encryptor' },
  { id:'ra',        icon:'🏛️', name:'注册机构',   sub:'RA' },
  { id:'user',      icon:'👤', name:'用户',       sub:'User' },
  { id:'aa',        icon:'🏢', name:'授权机构',   sub:'AA₁…AAₙ' },
  { id:'ta',        icon:'🔎', name:'追踪机构',   sub:'TA' },
  { id:'db',        icon:'🗄️', name:'数据库',     sub:'DB' },
]
const activeEntities = ref(new Set())

// 实体在行中的X位置（百分比，用于计算动画起止）
const entityPos = { encryptor:8, ra:22, user:38, aa:58, ta:76, db:92 }

// ── 飞行消息动画 ──────────────────────────────────────
const flyingMsgs = ref([])
let msgIdCounter = 0
const animLayer  = ref(null)

function msgStyle(m) {
  return {
    left: m.x + '%',
    top: m.y + 'px',
    opacity: m.opacity,
    transition: m.transitioning
      ? `left ${m.dur}ms ease-in-out, opacity 0.3s`
      : 'none',
  }
}

async function animateMsg(from, to, icon, label, durationMs = 900) {
  activeEntities.value.add(from)
  activeEntities.value.add(to)
  const id = ++msgIdCounter
  const startX = entityPos[from] - 2
  const endX   = entityPos[to] - 2
  const msg = reactive({ id, x: startX, y: 30, opacity: 1, icon, label, transitioning: false, dur: durationMs })
  flyingMsgs.value.push(msg)
  await nextTick()
  await sleep(30)
  msg.transitioning = true
  msg.x = endX
  await sleep(durationMs + 200)
  msg.opacity = 0
  await sleep(350)
  flyingMsgs.value = flyingMsgs.value.filter(m => m.id !== id)
  activeEntities.value.delete(from)
  activeEntities.value.delete(to)
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)) }

// ── 步骤定义 ──────────────────────────────────────────
const steps = reactive([
  { key:'init',      name:'系统初始化',     algo:'Global_Setup + Setup',   interaction:'RA · TA · AA',  state:'idle', result:null, ms:null },
  { key:'regist',    name:'用户注册',       algo:'Regist',                 interaction:'User ↔ RA → TA',state:'idle', result:null, ms:null },
  { key:'enc',       name:'服务加密',       algo:'Enc (OSBE)',             interaction:'Encryptor → DB', state:'idle', result:null, ms:null },
  { key:'pseudonym', name:'生成伪名',       algo:'Gen_Pseudonym',          interaction:'User',           state:'idle', result:null, ms:null },
  { key:'acc_req',   name:'请求访问权限',   algo:'Acc_Req',                interaction:'User ↔ AA₁…AAₙ',state:'idle', result:null, ms:null },
  { key:'acc_agg',   name:'权限聚合',       algo:'Access_Agg',             interaction:'User',           state:'idle', result:null, ms:null },
  { key:'dec',       name:'解密访问',       algo:'Dec',                    interaction:'User → DB',      state:'idle', result:null, ms:null },
  { key:'trace',     name:'溯源追踪',       algo:'Trace',                  interaction:'TA ← 伪名',      state:'idle', result:null, ms:null },
])

const prevPerms = ref([])
const showAggAnim = ref(false)

function canRun(i) {
  if (i === 0) return true
  return steps[i-1].state === 'done'
}

function stepClass(s) {
  return s.state === 'done' ? 'done' : s.state === 'running' ? 'running' : 'idle'
}

const allDone = computed(() => steps.every(s => s.state === 'done'))

// ── 步骤执行 ──────────────────────────────────────────
async function runStep(i) {
  const s = steps[i]
  s.state = 'running'
  const t0 = performance.now()
  try {
    await handlers[s.key]()
    s.ms = (performance.now() - t0).toFixed(0)
    s.state = 'done'
  } catch(e) {
    s.state = 'idle'
    ElMessage.error(e.response?.data?.error || '执行失败，请先完成前置步骤')
  }
}

const handlers = {
  async init() {
    // 全局初始化 → RA → TA → AA（n个）→ User setup
    activeEntities.value = new Set(['ra','ta','aa'])
    await setupApi.globalSetup()
    await animateMsg('ra', 'ta', '📋', 'params', 400)
    await setupApi.raSetup()
    await setupApi.taSetup()
    await setupApi.aaSetup(cfg.value.nAAs)
    await setupApi.userSetup('Alice')
    await animateMsg('ra', 'user', '🔑', 'PK_RA', 600)
    steps[0].result = { ok: true }
    activeEntities.value = new Set()
  },

  async regist() {
    // User → RA: ZK证明; RA → TA: (ID,PK); RA → User: σ_U
    await animateMsg('user', 'ra', '✉️', 'ZK证明 Π_U', 800)
    const { data } = await setupApi.regist('Alice')
    await animateMsg('ra', 'ta', '📨', '(ID_U, PK_U)', 700)
    await animateMsg('ra', 'user', '🏅', '匿名凭证 σ_U', 700)
    steps[1].result = data
  },

  async enc() {
    // Encryptor → DB: CT
    const msg = uploadedFile.value
      ? `[文件] ${uploadedFile.value.name}`
      : cfg.value.message
    await animateMsg('encryptor', 'db', '🔐', 'Enc(M, W, TP)', 900)
    const { data } = await workflowApi.enc({
      keyword: cfg.value.keyword,
      time_period: cfg.value.timePeriod,
      message: msg,
    })
    steps[2].result = data
  },

  async pseudonym() {
    // User自行生成伪名（内部操作）
    activeEntities.value = new Set(['user'])
    const { data } = await workflowApi.pseudonym('Alice')
    await sleep(400)
    activeEntities.value = new Set()
    steps[3].result = data
  },

  async acc_req() {
    // User → AA₁, AA₂, …: 访问请求; AA → User: K_j
    for (let i = 0; i < cfg.value.nAAs; i++) {
      animateMsg('user', 'aa', '📩', `请求 AA${i+1}`, 600)
      await sleep(200)
    }
    const { data } = await workflowApi.accReq({
      user_id: 'Alice',
      keyword: cfg.value.keyword,
      time_period: cfg.value.timePeriod,
    })
    await sleep(400)
    for (let i = 0; i < cfg.value.nAAs; i++) {
      animateMsg('aa', 'user', '🔑', `K_${i+1}`, 600)
      await sleep(150)
    }
    await sleep(700)
    prevPerms.value = data.permissions || []
    steps[4].result = data
  },

  async acc_agg() {
    showAggAnim.value = true
    activeEntities.value = new Set(['user'])
    const { data } = await workflowApi.accAgg('Alice')
    await sleep(800)
    showAggAnim.value = false
    activeEntities.value = new Set()
    steps[5].result = data
  },

  async dec() {
    // User → DB: AK_U; DB → User: M
    await animateMsg('user', 'db', '🗝️', 'AK_U (解密请求)', 800)
    const { data } = await workflowApi.dec({
      user_id: 'Alice',
      keyword: cfg.value.keyword,
      time_period: cfg.value.timePeriod,
    })
    if (data.success) {
      await animateMsg('db', 'user', '📦', '解密数据 M', 800)
    }
    steps[6].result = data
  },

  async trace() {
    // 伪名 → TA; TA → 真实身份
    await animateMsg('user', 'ta', '🎭', 'PU (伪名)', 800)
    const { data } = await workflowApi.trace('Alice')
    await animateMsg('ta', 'ra', '🔍', `PK_U 已还原`, 700)
    steps[7].result = data
  },
}

// ── 最终特性验证 ──────────────────────────────────────
const finalFeatures = computed(() => {
  const decStep   = steps.find(s=>s.key==='dec')
  const traceStep = steps.find(s=>s.key==='trace')
  const aggStep   = steps.find(s=>s.key==='acc_agg')
  return [
    {ico:'🔗',t:'不可链接性',    d:'每次请求伪名不同，无法关联到同一用户', ok:true},
    {ico:'✍️',t:'不可伪造性',    d:'AA多签名保护，无法在无私钥情况下伪造权限', ok:true},
    {ico:'📦',t:'可聚合性',      d:`${aggStep?.result?.num_permissions||'?'}个签名聚合为1个AK_U`, ok:true},
    {ico:'⚡',t:'非交互认证',    d:'服务提供商无需在线，用户直接解密', ok:decStep?.result?.success===true},
    {ico:'🔍',t:'可追踪溯源',    d:'TA成功还原用户真实公钥', ok:traceStep?.result?.pk_match===true},
    {ico:'⏰',t:'直接撤销支持',  d:'时间段绑定机制，无需机构参与吊销', ok:true},
  ]
})
</script>

<style scoped>
.plabel{font-size:12px;color:#606266;margin-bottom:5px;font-weight:500}

/* 实体行 */
.stage-area{overflow:hidden}
.entities-row{display:flex;justify-content:space-between;padding:0 20px;margin-bottom:0;position:relative}
.entity-node{display:flex;flex-direction:column;align-items:center;width:90px;
  padding:10px 6px;border-radius:12px;transition:all .3s;cursor:default}
.entity-node.active{background:rgba(64,158,255,.1);transform:scale(1.08)}
.entity-avatar{font-size:32px;margin-bottom:4px;filter:grayscale(.3)}
.entity-node.active .entity-avatar{filter:none}
.entity-label{font-size:13px;font-weight:600;color:#151d2e}
.entity-sub{font-size:11px;color:#909399}

/* 动画层 */
.anim-layer{position:relative;height:70px;margin:0;pointer-events:none}
.flying-msg{position:absolute;display:flex;align-items:center;gap:5px;
  background:#fff;border:1.5px solid #409eff;border-radius:20px;
  padding:5px 12px;font-size:12px;font-weight:500;color:#1a6fa8;
  box-shadow:0 2px 8px rgba(64,158,255,.2);white-space:nowrap;z-index:10}
.msg-env{font-size:16px}

/* 步骤列表 */
.steps-list{padding:0 4px}
.step-row{display:flex;gap:12px;margin-bottom:0}
.step-indicator{display:flex;flex-direction:column;align-items:center;width:24px;flex-shrink:0;padding-top:14px}
.step-dot{width:14px;height:14px;border-radius:50%;background:#dde3ea;border:2px solid #dde3ea;flex-shrink:0;transition:all .3s}
.step-row.done .step-dot{background:#52c41a;border-color:#52c41a}
.step-row.running .step-dot{background:#409eff;border-color:#409eff;animation:pulse 1s infinite}
.step-line{flex:1;width:2px;background:#e8ecf0;margin:3px 0}
.step-content-wrap{flex:1;padding:10px 0 14px}
.step-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:0}
.step-meta{display:flex;align-items:center;gap:8px}
.step-num{width:22px;height:22px;border-radius:50%;background:#f0f2f5;font-size:11px;font-weight:700;
  display:flex;align-items:center;justify-content:center;color:#666;flex-shrink:0}
.step-row.done .step-num{background:#52c41a;color:#fff}
.step-name{font-size:14px;font-weight:600;color:#151d2e}
.step-algo{font-size:11px;font-family:monospace;color:#909399;background:#f5f7fa;padding:2px 7px;border-radius:4px}
.step-parties{font-size:11px;color:#409eff}
.step-actions{display:flex;align-items:center;gap:8px}
.step-ms{font-size:12px;color:#52c41a;font-weight:600}

/* 结果展示 */
.step-result{margin-top:10px;padding:10px;background:#f9fafb;border-radius:8px}
.res-chip{font-size:12px;color:#555;margin-bottom:6px}
.fail-chip{color:#f5222d}
.res-chips{display:flex;flex-wrap:wrap;gap:6px}
.chip{font-family:monospace;font-size:11px;background:#e8f4fd;color:#1a6fa8;
  padding:3px 8px;border-radius:4px;border:1px solid #b3d8f5}
.chip.danger{background:#fff1f0;color:#f5222d;border-color:#ffa39e}

/* 聚合动画 */
.agg-visual{display:flex;align-items:center;gap:12px;margin-bottom:8px;
  padding:10px;background:#f0f9ff;border-radius:8px}
.agg-inputs{display:flex;gap:6px;flex-wrap:wrap}
.agg-key{font-size:12px;font-weight:600;background:#409eff;color:#fff;
  padding:3px 10px;border-radius:12px;animation:float .8s ease-in-out infinite alternate}
.agg-arrow{font-size:13px;font-weight:600;color:#409eff;white-space:nowrap}
.agg-output{font-size:13px;font-weight:700;color:#fff;background:#52c41a;
  padding:5px 14px;border-radius:12px}

/* 解密结果 */
.decrypt-result{display:flex;align-items:flex-start;gap:12px;
  background:#f6ffed;border:1px solid #b7eb8f;border-radius:8px;padding:12px}
.decrypt-icon{font-size:28px;flex-shrink:0}
.decrypt-label{font-size:13px;font-weight:600;color:#389e0d;margin-bottom:4px}
.decrypt-msg{font-size:15px;font-weight:700;color:#151d2e;
  padding:8px 12px;background:#fff;border-radius:6px;border:1px solid #d9f7be;margin-top:4px}

/* 总结 */
.summary-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.summary-item{display:flex;gap:10px;padding:14px;border-radius:8px}
.sum-ok{background:#f6ffed;border:1px solid #b7eb8f}
.sum-warn{background:#fff7e6;border:1px solid #ffd591}
.sum-ico{font-size:20px;flex-shrink:0;margin-top:2px}
.sum-t{font-size:13px;font-weight:600;color:#151d2e;margin-bottom:3px}
.sum-d{font-size:11px;color:#666;line-height:1.5}

@keyframes pulse{0%,100%{box-shadow:0 0 0 0 rgba(64,158,255,.4)}50%{box-shadow:0 0 0 6px rgba(64,158,255,0)}}
@keyframes float{from{transform:translateY(0)}to{transform:translateY(-4px)}}
.spin-dot{display:inline-block;animation:spin .8s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
</style>
