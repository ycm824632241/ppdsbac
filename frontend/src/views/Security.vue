<template>
<div>
  <div class="pc">
    <div class="pt">🛡️ 安全属性演示</div>
    <div class="pd">交互式演示方案的四大安全属性。</div>
  </div>

  <div class="pc">
    <div class="section-hd">不可链接性（Unlinkability）</div>
    <div class="prop-desc">
      <b>安全目标：</b>即使注册机构、所有授权机构和部分用户联合攻击，也无法判断两次访问请求是否来自同一用户。<br>
      <b>核心机制：</b>每次请求随机选取新鲜随机数 r_u，生成不同伪名，使得不同伪名在计算上不可区分。
    </div>
    <div class="formula">PU = (g^r_u,  Y_U · Y_TA^r_u)  — ElGamal加密，r_u 每次新鲜随机</div>
    <el-button type="primary" :loading="ul.loading" @click="doUnlink" style="margin-bottom:14px">生成两次访问请求伪名</el-button>
    <div v-if="ul.result" class="demo-grid">
      <div class="demo-block">
        <div class="demo-label">第一次访问请求伪名</div>
        <div class="kv"><span class="kl">PU₁</span><div class="hex">{{ ul.result.request_1.PU1 }}</div></div>
        <div class="kv"><span class="kl">PU₂</span><div class="hex">{{ ul.result.request_1.PU2 }}</div></div>
      </div>
      <div class="demo-block">
        <div class="demo-label">第二次访问请求伪名</div>
        <div class="kv"><span class="kl">PU₁</span><div class="hex">{{ ul.result.request_2.PU1 }}</div></div>
        <div class="kv"><span class="kl">PU₂</span><div class="hex">{{ ul.result.request_2.PU2 }}</div></div>
      </div>
    </div>
    <div v-if="ul.result" style="margin-top:12px">
      <el-alert :type="ul.result.are_linked ? 'error' : 'success'" :closable="false">
        <b>两次伪名可关联：{{ ul.result.are_linked ? '是（安全漏洞）' : '否 ✓（方案安全）' }}</b><br>
        <span style="font-size:12px">{{ ul.result.explanation }}</span>
      </el-alert>
    </div>
  </div>

  <div class="pc">
    <div class="section-hd">不可伪造性（Unforgeability）</div>
    <div class="prop-desc">
      <b>安全目标：</b>没有授权机构私钥的攻击者，无法伪造出通过双线性对验证的访问权限。<br>
      <b>验证等式：</b>e(K_j, g') = e(H₁(W‖TP)·h₀·h₁^H₂(PU), Y_j^z_j)
    </div>
    <div class="formula">K_j = (H₁(W‖TP) · h₀ · h₁^H₂(PU))^(x_j · z_j)，z_j 防范流氓密钥攻击</div>
    <el-button type="primary" :loading="uf.loading" @click="doUnforge" style="margin-bottom:14px">尝试随机伪造访问权限</el-button>
    <div v-if="uf.result">
      <el-descriptions :column="1" border size="small" style="margin-bottom:10px">
        <el-descriptions-item label="伪造的 K_j（随机值）"><span class="hex">{{ uf.result.forged_K_hex }}</span></el-descriptions-item>
        <el-descriptions-item label="验证等式">{{ uf.result.verify_eq }}</el-descriptions-item>
        <el-descriptions-item label="伪造结果">
          <span :class="uf.result.forgery_succeeds ? 'fail' : 'ok'">
            {{ uf.result.forgery_succeeds ? '成功（安全漏洞！）' : '✗ 验证失败（方案安全 ✓）' }}
          </span>
        </el-descriptions-item>
      </el-descriptions>
      <el-alert type="success" :closable="false"><span style="font-size:12px">{{ uf.result.explanation }}</span></el-alert>
    </div>
  </div>

  <div class="pc">
    <div class="section-hd">方案安全属性对比</div>
    <el-table :data="compareData" border style="width:100%">
      <el-table-column prop="scheme"        label="方案"          width="200"/>
      <el-table-column prop="decentralized" label="去中心化"      align="center"/>
      <el-table-column prop="anonymous"     label="匿名性"        align="center"/>
      <el-table-column prop="unlinkable"    label="不可链接"      align="center"/>
      <el-table-column prop="unforgeable"   label="权限不可伪造"  align="center"/>
      <el-table-column prop="aggregatable"  label="权限可聚合"    align="center"/>
      <el-table-column prop="noninteractive"label="非交互认证"    align="center"/>
      <el-table-column prop="traceable"     label="可追踪"        align="center"/>
    </el-table>
  </div>

  <div class="pc">
    <div class="section-hd">安全证明结构</div>
    <div class="proof-grid">
      <div v-for="p in proofs" :key="p.thm" class="proof-card" :style="`border-left-color:${p.color}`">
        <div class="proof-thm" :style="`color:${p.color}`">{{ p.thm }}</div>
        <div class="proof-name">{{ p.name }}</div>
        <div class="proof-game">{{ p.game }}</div>
        <div class="proof-adv">优势上界：{{ p.adv }}</div>
        <div class="proof-reduction">归约至 {{ p.reduction }}</div>
      </div>
    </div>
  </div>
</div>
</template>

<script setup>
import { reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { securityApi } from '../api/index.js'
const ul = reactive({ loading:false, result:null })
const uf = reactive({ loading:false, result:null })
async function doUnlink() {
  ul.loading=true
  try { const {data}=await securityApi.unlinkability(); ul.result=data }
  catch(e) { ElMessage.error('请先完成系统初始化') }
  finally { ul.loading=false }
}
async function doUnforge() {
  uf.loading=true
  try { const {data}=await securityApi.unforgeability(); uf.result=data }
  catch(e) { ElMessage.error('请求失败') }
  finally { uf.loading=false }
}
const compareData = [
  {scheme:'Han et al. 2012',     decentralized:'✓',anonymous:'✓',unlinkable:'✗',unforgeable:'✗',aggregatable:'✗',noninteractive:'✗',traceable:'✗'},
  {scheme:'Ruj et al. 2014',     decentralized:'✓',anonymous:'✓',unlinkable:'✗',unforgeable:'✗',aggregatable:'✗',noninteractive:'✗',traceable:'✗'},
  {scheme:'Han et al. 2015',     decentralized:'✓',anonymous:'✓',unlinkable:'✓',unforgeable:'✗',aggregatable:'✗',noninteractive:'✗',traceable:'✗'},
  {scheme:'Nasiraee et al. 2022',decentralized:'✓',anonymous:'✓',unlinkable:'✗',unforgeable:'✗',aggregatable:'✗',noninteractive:'✓',traceable:'✗'},
  {scheme:'本方案 PPDSBAC',      decentralized:'✓',anonymous:'✓',unlinkable:'✓',unforgeable:'✓',aggregatable:'✓',noninteractive:'✓',traceable:'✓'},
]
const proofs = [
  {thm:'语义安全',color:'#409eff',name:'抗CPA攻击',game:'IND-CPA游戏',adv:'(1-1/q_H)^q_K · ε²',reduction:'DBDH假设'},
  {thm:'不可链接',color:'#52c41a',name:'伪名不可区分',game:'伪名区分游戏',adv:'ε²',reduction:'DDH假设'},
  {thm:'可追踪',color:'#722ed1',name:'非法访问追踪',game:'访问记录伪造游戏',adv:'(1-1/q₁)^q_AR · ε/(8q₂)',reduction:'Co-CDH + DL假设'},
  {thm:'凭证不可伪造',color:'#fa8c16',name:'匿名凭证安全',game:'凭证伪造游戏',adv:'(q+1)/(3q) · ε',reduction:'q-SDH + DL假设'},
]
</script>
<style scoped>
.prop-desc{font-size:13px;color:#555;line-height:1.8;margin-bottom:12px;padding:12px;background:#f9fafb;border-radius:8px}
.demo-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.demo-block{border:1px solid #e4e7ed;border-radius:8px;padding:14px}
.demo-label{font-size:13px;font-weight:600;color:#409eff;margin-bottom:10px}
.kv{display:flex;align-items:flex-start;gap:8px;margin-bottom:6px}
.kl{font-size:11px;font-weight:600;color:#909399;font-family:monospace;min-width:32px;margin-top:4px}
.proof-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.proof-card{background:#fafbfc;border-left:4px solid #409eff;border-radius:8px;padding:16px}
.proof-thm{font-size:13px;font-weight:700;margin-bottom:6px}
.proof-name{font-size:13px;font-weight:600;color:#151d2e;margin-bottom:8px}
.proof-game{font-size:11px;color:#666;margin-bottom:4px}
.proof-adv{font-size:11px;font-family:monospace;color:#555;margin-bottom:6px}
.proof-reduction{font-size:11px;color:#409eff;font-weight:600}
</style>
