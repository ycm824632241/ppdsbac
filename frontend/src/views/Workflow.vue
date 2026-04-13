<template>
<div>
  <div class="pc">
    <div class="pt">🔄 协议流程</div>
    <div class="pd">逐步执行加密、伪名生成、权限请求、聚合、解密和追踪完整流程。</div>
    <el-row :gutter="14" style="margin-bottom:14px">
      <el-col :span="6"><el-input v-model="form.userId" placeholder="用户ID（如Alice）"/></el-col>
      <el-col :span="6"><el-input v-model="form.keyword" placeholder="关键词 W"/></el-col>
      <el-col :span="6"><el-input v-model="form.timePeriod" placeholder="时间段 TP"/></el-col>
      <el-col :span="6"><el-input v-model="form.message" placeholder="服务内容 M"/></el-col>
    </el-row>

    <div v-for="(s,i) in stages" :key="s.key" class="stage">
      <div class="stage-head" @click="s.open=!s.open">
        <div class="stage-left">
          <div class="snum" :class="s.done?'done':s.running?'run':''">{{ i+1 }}</div>
          <div><div class="sname">{{ s.name }}</div><div class="salgo">{{ s.algo }}</div></div>
        </div>
        <div class="stage-right">
          <el-tag v-if="s.done" type="success" size="small">✓ 完成</el-tag>
          <el-button type="primary" size="small" :loading="s.running" @click.stop="runStage(s)">执行</el-button>
        </div>
      </div>
      <div v-show="s.open && s.result" class="stage-body">
        <template v-if="s.key==='enc'">
          <div class="formula">CT = (C₁,C₂,C₃,C₄) — OSBE加密服务于关键词和时间段</div>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="C₁"><span class="hex">{{ s.result?.C1_hex }}</span></el-descriptions-item>
            <el-descriptions-item label="C₂"><span class="hex">{{ s.result?.C2_hex }}</span></el-descriptions-item>
            <el-descriptions-item label="C₃"><span class="hex">{{ s.result?.C3_hex }}</span></el-descriptions-item>
            <el-descriptions-item label="C₄"><span class="hex">{{ s.result?.C4_hex }}</span></el-descriptions-item>
          </el-descriptions>
        </template>
        <template v-if="s.key==='pseudonym'">
          <div class="formula">{{ s.result?.formula }}</div>
          <el-alert type="info" :closable="false">每次请求使用全新随机 r_u，不同伪名间不可关联</el-alert>
        </template>
        <template v-if="s.key==='acc_req'">
          <div class="formula">K_j = (H₁(W‖TP)·h₀·h₁^H₂(PU))^(x_j·z_j)</div>
          <el-table :data="s.result?.permissions" size="small" stripe style="margin-top:10px">
            <el-table-column prop="aa_id" label="AA" width="70"/>
            <el-table-column label="访问权限 K_j">
              <template #default="{row}"><span class="hex" style="font-size:10px">{{ row.K_j_hex?.slice(0,36) }}…</span></template>
            </el-table-column>
          </el-table>
        </template>
        <template v-if="s.key==='acc_agg'">
          <div class="formula">{{ s.result?.formula }}</div>
          <el-tag type="success">{{ s.result?.storage_saving }}</el-tag>
          <div class="hex" style="margin-top:8px">{{ s.result?.AK_U_hex }}</div>
        </template>
        <template v-if="s.key==='dec'">
          <el-alert :type="s.result?.success?'success':'error'" :closable="false">
            <b>{{ s.result?.success ? '🔓 解密成功（服务提供商无需在线）' : '🔒 解密失败：'+s.result?.reason }}</b>
            <div v-if="s.result?.success" style="margin-top:6px;font-size:14px">"{{ s.result?.message }}"</div>
          </el-alert>
        </template>
        <template v-if="s.key==='trace'">
          <div class="formula">{{ s.result?.formula }}</div>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="还原公钥"><span class="hex">{{ s.result?.recovered_PK_U_hex }}</span></el-descriptions-item>
            <el-descriptions-item label="真实身份"><el-tag type="danger">{{ s.result?.identity_revealed }}</el-tag></el-descriptions-item>
            <el-descriptions-item label="追踪结果"><span :class="s.result?.pk_match?'ok':'fail'">{{ s.result?.pk_match?'✓ 成功':'✗ 失败' }}</span></el-descriptions-item>
          </el-descriptions>
        </template>
      </div>
    </div>
  </div>

  <div class="pc">
    <div class="section-hd">直接撤销演示（时间段不匹配）</div>
    <p style="font-size:13px;color:#666;margin-bottom:12px">修改时间段后尝试解密，系统将直接拒绝访问。</p>
    <el-input v-model="wrongTP" placeholder="填入与密文不同的时间段" style="width:300px;margin-right:10px"/>
    <el-button @click="testRevoke" :loading="revokeLoading">测试撤销</el-button>
    <el-alert v-if="revokeResult" :type="revokeResult.success?'success':'error'" :closable="false" style="margin-top:10px">
      {{ revokeResult.success ? '意外成功' : '🚫 访问被拒绝：'+revokeResult.reason }}
    </el-alert>
  </div>
</div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { workflowApi } from '../api/index.js'
const form = ref({userId:'Alice',keyword:'medical_record',timePeriod:'2025-Q1',message:'Patient Record #042 — Confidential'})
const wrongTP = ref('2024-Q4')
const revokeLoading = ref(false)
const revokeResult = ref(null)
const stages = reactive([
  {key:'enc',      name:'服务加密',      algo:'Enc',          done:false,running:false,open:false,result:null},
  {key:'pseudonym',name:'生成伪名',      algo:'Gen_Pseudonym',done:false,running:false,open:false,result:null},
  {key:'acc_req',  name:'请求访问权限',  algo:'Acc_Req',      done:false,running:false,open:false,result:null},
  {key:'acc_agg',  name:'权限聚合',      algo:'Access_Agg',   done:false,running:false,open:false,result:null},
  {key:'dec',      name:'解密访问',      algo:'Dec',          done:false,running:false,open:false,result:null},
  {key:'trace',    name:'溯源追踪',      algo:'Trace',        done:false,running:false,open:false,result:null},
])
const apiMap = {
  enc:       ()=>workflowApi.enc({keyword:form.value.keyword,time_period:form.value.timePeriod,message:form.value.message}),
  pseudonym: ()=>workflowApi.pseudonym(form.value.userId),
  acc_req:   ()=>workflowApi.accReq({user_id:form.value.userId,keyword:form.value.keyword,time_period:form.value.timePeriod}),
  acc_agg:   ()=>workflowApi.accAgg(form.value.userId),
  dec:       ()=>workflowApi.dec({user_id:form.value.userId,keyword:form.value.keyword,time_period:form.value.timePeriod}),
  trace:     ()=>workflowApi.trace(form.value.userId),
}
async function runStage(s) {
  s.running=true
  try { const {data}=await apiMap[s.key](); s.result=data; s.done=true; s.open=true; ElMessage.success(data.msg||'执行成功') }
  catch(e) { ElMessage.error(e.response?.data?.error||'执行失败，请先完成前置步骤') }
  finally { s.running=false }
}
async function testRevoke() {
  revokeLoading.value=true
  try { const {data}=await workflowApi.dec({user_id:form.value.userId,keyword:form.value.keyword,time_period:wrongTP.value}); revokeResult.value=data }
  catch(e) { ElMessage.error('请先完成Enc和Dec步骤') }
  finally { revokeLoading.value=false }
}
</script>
<style scoped>
.stage{border:1px solid #e8ecf0;border-radius:10px;margin-bottom:12px;overflow:hidden}
.stage-head{display:flex;justify-content:space-between;align-items:center;padding:14px 16px;cursor:pointer;background:#fafbfc}
.stage-head:hover{background:#f0f4f8}
.stage-left{display:flex;align-items:center;gap:12px}
.stage-right{display:flex;align-items:center;gap:8px}
.snum{width:30px;height:30px;border-radius:50%;background:#dde3ea;color:#666;font-size:13px;font-weight:700;display:flex;align-items:center;justify-content:center}
.snum.done{background:#52c41a;color:#fff} .snum.run{background:#409eff;color:#fff}
.sname{font-size:14px;font-weight:600;color:#151d2e} .salgo{font-size:11px;color:#909399;font-family:monospace}
.stage-body{padding:16px;background:#fff;border-top:1px solid #e8ecf0}
</style>
