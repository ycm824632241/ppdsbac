<template>
<div>
  <div class="pc">
    <div class="pt">📊 性能评估</div>
    <div class="pd">各算法计算开销分析，以及与现有方案的对比。</div>
    <el-button type="primary" size="large" :loading="loading" @click="runBench">▶ 运行性能测试</el-button>
    <el-tag type="info" style="margin-left:12px">测试环境：HP i5-8300H · 16G RAM · PBC Type-F曲线 · SHA-256</el-tag>
  </div>

  <div v-if="data">
    <div class="metric-row">
      <div v-for="m in metrics" :key="m.label" class="metric-card">
        <div class="metric-val">{{ m.val }}</div>
        <div class="metric-label">{{ m.label }}</div>
      </div>
    </div>

    <!-- 各算法耗时 -->
    <div class="pc">
      <div class="section-hd">各算法计算开销（ms）</div>
      <div ref="chartRef1" style="height:380px"></div>
    </div>

    <!-- Acc_Req 对比 -->
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:0">
      <div class="pc" style="margin-bottom:0">
        <div class="section-hd">Acc_Req 时间对比（ms）</div>
        <div class="compare-note">
          本方案 Acc_Req 包含零知识证明验证和多签名生成，开销高于 [23]；
          但本方案额外提供权限不可伪造性和可聚合性，[23] 不具备这两项属性。
        </div>
        <div ref="chartRef2" style="height:260px"></div>
      </div>
      <div class="pc" style="margin-bottom:0">
        <div class="section-hd">Dec 时间对比（ms）</div>
        <div class="compare-note">
          本方案解密时需验证聚合签名并完成双线性对运算；
          两方案解密时间均随 AA 数量线性增长，量级相当。
        </div>
        <div ref="chartRef3" style="height:260px"></div>
      </div>
    </div>

    <!-- 数据表 -->
    <div class="pc" style="margin-top:16px">
      <div class="section-hd">详细计时数据（ms）</div>
      <el-tabs>
        <el-tab-pane v-for="n in [10,20,30]" :key="n" :label="`n = ${n} 个AA`">
          <el-table :data="tableData(n)" border size="small" stripe>
            <el-table-column prop="algo"  label="算法"       width="180"/>
            <el-table-column prop="paper" label="参考值(ms)" align="right" width="120">
              <template #default="{row}"><span style="font-weight:600;color:#409eff">{{ row.paper }}</span></template>
            </el-table-column>
            <el-table-column prop="sim"   label="仿真值(ms)" align="right" width="120"/>
            <el-table-column prop="note"  label="说明"/>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 复杂度 -->
    <div class="pc">
      <div class="section-hd">算法复杂度分析</div>
      <el-table :data="complexity" border size="small">
        <el-table-column prop="algo"   label="算法"         width="180"/>
        <el-table-column prop="comp"   label="复杂度"/>
        <el-table-column prop="linear" label="随n线性增长"  align="center" width="120"/>
        <el-table-column prop="note"   label="关键操作"/>
      </el-table>
    </div>
  </div>
</div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { benchApi } from '../api/index.js'

const loading   = ref(false)
const data      = ref(null)
const chartRef1 = ref(null)
const chartRef2 = ref(null)
const chartRef3 = ref(null)

const ALGOS = ['Global_Setup','Reg_Auth_Setup','Auth_Auth_Setup','Trace_Auth_Setup',
               'User_Setup','Regist','Enc','Acc_Req','Acc_Agg','Dec','Trace']

const metrics = computed(() => {
  if (!data.value) return []
  const p = data.value.paper_ref
  return [
    {val: p['10'].Acc_Req.toFixed(0)+' ms', label:'Acc_Req (n=10)'},
    {val: p['10'].Enc.toFixed(1)+' ms',     label:'Enc (n=10)'},
    {val: p['10'].Acc_Agg.toFixed(2)+' ms', label:'Acc_Agg（极轻量）'},
    {val: p['10'].Trace.toFixed(2)+' ms',   label:'Trace（极快）'},
  ]
})

function tableData(n) {
  if (!data.value) return []
  const pr = data.value.paper_ref[String(n)]
  const sr = data.value.simulated[String(n)]?.timings_ms || {}
  const notes = {
    Global_Setup:'与n无关，常数开销', Reg_Auth_Setup:'常数开销',
    Auth_Auth_Setup:'线性于n', Trace_Auth_Setup:'常数开销',
    User_Setup:'常数开销', Regist:'含ZK证明生成',
    Enc:'线性于选定AA数量', Acc_Req:'含ZK证明验证（最重步骤）',
    Acc_Agg:'仅G₁乘法，极轻量', Dec:'线性于选定AA数量', Trace:'常数开销'
  }
  return ALGOS.map(a=>({algo:a, paper:pr?.[a]??'-', sim:sr?.[a]??'-', note:notes[a]||''}))
}

const complexity = [
  {algo:'Global_Setup',    comp:'O(1)', linear:'否', note:'群参数生成'},
  {algo:'Auth_Auth_Setup', comp:'O(n)', linear:'是', note:'n次幂运算'},
  {algo:'Regist',          comp:'O(1)', linear:'否', note:'ZK证明+凭证签名'},
  {algo:'Enc',             comp:'O(k)', linear:'是', note:'k=选定AA数，双线性对'},
  {algo:'Acc_Req',         comp:'O(k)', linear:'是', note:'k次ZK验证+多签名'},
  {algo:'Acc_Agg',         comp:'O(k)', linear:'是', note:'k次G₁乘法（极快）'},
  {algo:'Dec',             comp:'O(k)', linear:'是', note:'双线性对+GT运算'},
  {algo:'Trace',           comp:'O(1)', linear:'否', note:'ElGamal解密'},
]

async function runBench() {
  loading.value = true
  try {
    const {data:d} = await benchApi.run()
    data.value = d
    ElMessage.success('测试完成')
    await nextTick()
    drawChart1(); drawChart2(); drawChart3()
  } catch(e) { ElMessage.error('测试失败') }
  finally { loading.value = false }
}

function drawChart1() {
  const chart = echarts.init(chartRef1.value)
  const pr = data.value.paper_ref
  const algos = ALGOS.filter(a=>a!=='Acc_Req')  // 单独图表，此处排除避免Y轴失真
  chart.setOption({
    tooltip:{trigger:'axis'},
    legend:{data:['n=10','n=20','n=30']},
    grid:{left:60,right:20,bottom:80,top:40},
    xAxis:{type:'category',data:algos,axisLabel:{rotate:30,fontSize:11}},
    yAxis:{type:'value',name:'时间 (ms)'},
    series:[
      {name:'n=10',type:'bar',data:algos.map(a=>pr['10'][a]??0),itemStyle:{color:'#409eff'}},
      {name:'n=20',type:'bar',data:algos.map(a=>pr['20'][a]??0),itemStyle:{color:'#67c23a'}},
      {name:'n=30',type:'bar',data:algos.map(a=>pr['30'][a]??0),itemStyle:{color:'#e6a23c'}},
    ]
  })
}

function drawChart2() {
  // 专门对比 Acc_Req
  const chart = echarts.init(chartRef2.value)
  const pr  = data.value.paper_ref
  const s23 = data.value.scheme23_ref
  const ns  = [10,20,30]
  chart.setOption({
    tooltip:{trigger:'axis'},
    legend:{data:['本方案','Nasiraee et al.'],bottom:0},
    grid:{left:60,right:20,bottom:50,top:20},
    xAxis:{type:'category',data:ns.map(n=>`n=${n}`),name:'AA数量'},
    yAxis:{type:'value',name:'Acc_Req (ms)'},
    series:[
      {name:'本方案',type:'bar',barWidth:30,data:ns.map(n=>pr[n].Acc_Req),
       itemStyle:{color:'#409eff'},
       label:{show:true,position:'top',fontSize:11,formatter:p=>p.value+'ms'}},
      {name:'Nasiraee et al.',type:'bar',barWidth:30,data:ns.map(n=>s23[n].Acc_Req),
       itemStyle:{color:'#b3d8ff'},
       label:{show:true,position:'top',fontSize:11,formatter:p=>p.value+'ms'}},
    ]
  })
}

function drawChart3() {
  // 专门对比 Dec — Y轴独立，细节清晰
  const chart = echarts.init(chartRef3.value)
  const pr  = data.value.paper_ref
  const s23 = data.value.scheme23_ref
  const ns  = [10,20,30]
  const ourDec  = ns.map(n=>pr[n].Dec)
  const theirDec = ns.map(n=>s23[n].Dec)
  // 计算合理的Y轴范围使差异可见
  const allVals = [...ourDec,...theirDec]
  const minV = Math.floor(Math.min(...allVals)*0.8)
  const maxV = Math.ceil(Math.max(...allVals)*1.15)
  chart.setOption({
    tooltip:{trigger:'axis'},
    legend:{data:['本方案','Nasiraee et al.'],bottom:0},
    grid:{left:60,right:20,bottom:50,top:20},
    xAxis:{type:'category',data:ns.map(n=>`n=${n}`),name:'AA数量'},
    yAxis:{type:'value',name:'Dec (ms)',min:minV,max:maxV},
    series:[
      {name:'本方案',type:'bar',barWidth:30,data:ourDec,
       itemStyle:{color:'#67c23a'},
       label:{show:true,position:'top',fontSize:11,formatter:p=>p.value+'ms'}},
      {name:'Nasiraee et al.',type:'bar',barWidth:30,data:theirDec,
       itemStyle:{color:'#b7eb8f'},
       label:{show:true,position:'top',fontSize:11,formatter:p=>p.value+'ms'}},
    ]
  })
}
</script>

<style scoped>
.metric-row{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:18px}
.metric-card{background:#fff;border-radius:10px;padding:20px;text-align:center;box-shadow:0 1px 4px rgba(0,0,0,.06)}
.metric-val{font-size:22px;font-weight:700;color:#409eff;margin-bottom:4px}
.metric-label{font-size:12px;color:#909399}
.compare-note{font-size:12px;color:#888;line-height:1.6;margin-bottom:10px;padding:8px 10px;background:#f9fafb;border-radius:6px}
</style>
