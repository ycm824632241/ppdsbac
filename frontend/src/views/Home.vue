<template>
<div>
  <div class="hero">
    <h1 class="hero-h1">隐私保护去中心化签名访问控制系统</h1>
    <p class="hero-en">Privacy-Preserving Decentralized Signature-Based Access Control</p>
    <p class="hero-desc">针对现有去中心化访问控制方案<b>访问权限不可伪造性缺失、服务提供商必须在线、非法用户无法溯源</b>三大问题，
      本方案通过多签名技术、OSBE加密和伪名机制，实现<b>不可链接访问请求、不可伪造可聚合访问权限、非交互式认证和可追踪溯源</b>。</p>
    <div style="display:flex;gap:12px;flex-wrap:wrap">
      <el-button type="primary" size="large" @click="$router.push('/demo')">🎬 运行完整演示</el-button>
      <el-button size="large" plain @click="$router.push('/setup')">⚙️ 开始初始化</el-button>
      <el-button size="large" plain @click="$router.push('/benchmark')">📊 性能评估</el-button>
    </div>
  </div>

  <div class="section-hd">核心创新点</div>
  <div class="feat-grid">
    <div v-for="f in feats" :key="f.t" class="feat-card" :style="`border-top-color:${f.c}`">
      <div class="feat-ico">{{ f.ico }}</div>
      <div class="feat-t">{{ f.t }}</div>
      <div class="feat-d">{{ f.d }}</div>
      <div class="feat-tech">{{ f.tech }}</div>
    </div>
  </div>

  <div class="section-hd">系统参与实体</div>
  <div class="ent-grid">
    <div v-for="e in ents" :key="e.name" class="ent-card">
      <div class="ent-ico">{{ e.ico }}</div>
      <div class="ent-name">{{ e.name }}</div>
      <div class="ent-full">{{ e.full }}</div>
      <div class="ent-desc">{{ e.desc }}</div>
    </div>
  </div>

  <div class="section-hd">协议工作流程</div>
  <div class="pc">
    <div class="flow-wrap">
      <template v-for="(s,i) in flow" :key="i">
        <div class="flow-step">
          <div class="flow-num">{{ i+1 }}</div>
          <div>
            <div class="flow-name">{{ s.name }}</div>
            <div class="flow-algo">{{ s.algo }}</div>
          </div>
        </div>
        <div class="flow-arr" v-if="i<flow.length-1">→</div>
      </template>
    </div>
  </div>

  <div class="section-hd">安全性保证</div>
  <div class="sec-grid">
    <div v-for="s in secs" :key="s.t" class="sec-card">
      <div class="sec-badge" :style="`background:${s.c}22;color:${s.c}`">{{ s.thm }}</div>
      <div class="sec-t">{{ s.t }}</div>
      <div class="sec-d">{{ s.d }}</div>
      <div class="sec-assum">归约假设：{{ s.assum }}</div>
    </div>
  </div>

  <div class="section-hd">典型应用场景</div>
  <div class="scene-grid">
    <div v-for="s in scenes" :key="s.t" class="scene-card">
      <div class="scene-ico">{{ s.ico }}</div>
      <div class="scene-t">{{ s.t }}</div>
      <div class="scene-d">{{ s.d }}</div>
    </div>
  </div>
</div>
</template>

<script setup>
const feats = [
  {ico:'🔗',c:'#409eff',t:'不可链接访问请求',
   d:'每次访问生成新鲜伪名，不同请求无法被关联到同一用户，即使注册机构和所有授权机构联合攻击也无法关联。',
   tech:'技术基础：ElGamal伪名加密 + Fiat-Shamir零知识证明'},
  {ico:'✍️',c:'#52c41a',t:'不可伪造访问权限',
   d:'访问权限是授权机构在关键词、时间段和伪名上的多签名，可验证、不可伪造、不可抵赖。',
   tech:'技术基础：BLS紧凑多签名方案'},
  {ico:'📦',c:'#fa8c16',t:'可聚合访问权限',
   d:'来自多个授权机构的权限可聚合为单一密钥，存储开销恒定，验证效率大幅提升。',
   tech:'技术基础：BLS聚合签名（乘法同态）'},
  {ico:'⚡',c:'#f5222d',t:'非交互式认证',
   d:'服务加密时绑定访问条件，用户持有聚合密钥即可直接解密，服务提供商无需在线参与验证。',
   tech:'技术基础：OSBE（基于签名的遗忘传输信封）'},
  {ico:'🔍',c:'#722ed1',t:'可追踪溯源',
   d:'追踪机构可用私钥对伪名去匿名化，还原用户真实公钥，对非法用户进行追踪问责。',
   tech:'技术基础：ElGamal加密完美正确性'},
  {ico:'⏰',c:'#13c2c2',t:'直接撤销',
   d:'访问权限嵌入时间段，时间段不匹配时自动拒绝，无需注册机构或授权机构参与撤销。',
   tech:'技术基础：时间段绑定加密机制'},
]
const ents = [
  {ico:'🏛️',name:'RA',full:'Registration Authority',desc:'验证用户零知识证明，颁发匿名凭证，并将用户真实身份发送给追踪机构'},
  {ico:'🔎',name:'TA',full:'Trace Authority',desc:'存储用户真实身份，在必要时对伪名去匿名化，还原用户真实公钥'},
  {ico:'🏢',name:'AA₁…AAₙ',full:'Authorization Authority',desc:'独立运行无需交互，对用户伪名颁发多签名访问权限'},
  {ico:'👤',name:'User',full:'用户',desc:'用匿名凭证向各授权机构请求权限，聚合后直接解密服务，无需与服务提供商交互'},
  {ico:'📝',name:'Encryptor',full:'加密者',desc:'用OSBE在关键词和时间段下加密服务数据，密文上传数据库'},
  {ico:'🗄️',name:'DB',full:'Database',desc:'存储加密后的服务密文'},
]
const flow = [
  {name:'全局初始化',algo:'Global_Setup'},
  {name:'各方密钥生成',algo:'Setup'},
  {name:'用户注册',algo:'Regist'},
  {name:'服务加密',algo:'Enc'},
  {name:'生成伪名',algo:'Gen_Pseudonym'},
  {name:'请求访问权限',algo:'Acc_Req'},
  {name:'权限聚合',algo:'Access_Agg'},
  {name:'解密访问',algo:'Dec'},
  {name:'溯源追踪',algo:'Trace'},
]
const secs = [
  {thm:'语义安全',c:'#409eff',t:'抗选择明文攻击',d:'即使用户与注册机构、追踪机构和部分授权机构勾结，也无法访问未授权服务。',assum:'DBDH假设'},
  {thm:'不可链接',c:'#52c41a',t:'访问请求匿名性',d:'即使所有机构联合，也无法判断两次访问是否来自同一用户。',assum:'DDH假设'},
  {thm:'可追踪',c:'#722ed1',t:'非法用户追踪',d:'即使用户与部分授权机构勾结，也无法生成无法追踪的访问记录。',assum:'Co-CDH + DL假设'},
  {thm:'不可伪造',c:'#fa8c16',t:'匿名凭证安全',d:'即使用户与授权机构和追踪机构联合，也无法伪造合法匿名凭证。',assum:'q-SDH + DL假设'},
]
const scenes = [
  {ico:'🏥',t:'医疗健康数据共享',d:'患者数据由多家医院联合授权，医生需同时获得主治医院、保险机构等多方签名才能访问完整病历，支持异常行为追踪。'},
  {ico:'🌐',t:'IoT物联网设备访问',d:'工业IoT中，设备访问权由多个管理域联合控制，支持细粒度时间段授权和匿名身份接入，非法设备可被追踪溯源。'},
  {ico:'☁️',t:'云计算多租户数据',d:'多云环境下用户匿名获取多个服务商的访问授权，持聚合密钥直接解密数据，消除服务提供商在线依赖。'},
]
</script>

<style scoped>
.hero{background:linear-gradient(135deg,#151d2e 0%,#0f3460 100%);border-radius:14px;padding:38px;margin-bottom:24px;color:#fff}
.hero-h1{font-size:26px;font-weight:700;margin-bottom:6px}
.hero-en{font-size:13px;color:#7a8fa6;margin-bottom:12px;font-style:italic}
.hero-desc{color:#9aabb8;font-size:13px;line-height:1.8;max-width:700px;margin-bottom:22px}
.feat-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:22px}
.feat-card{background:#fff;border-radius:10px;padding:18px;border-top:3px solid #409eff;box-shadow:0 1px 4px rgba(0,0,0,.06)}
.feat-ico{font-size:22px;margin-bottom:7px}
.feat-t{font-size:14px;font-weight:600;color:#151d2e;margin-bottom:5px}
.feat-d{font-size:12px;color:#555;line-height:1.6;margin-bottom:8px}
.feat-tech{font-size:11px;color:#8c96a3;background:#f5f7fa;padding:4px 8px;border-radius:4px}
.ent-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:22px}
.ent-card{background:#fff;border-radius:10px;padding:16px;box-shadow:0 1px 4px rgba(0,0,0,.06);text-align:center}
.ent-ico{font-size:26px;margin-bottom:5px}
.ent-name{font-size:15px;font-weight:700;color:#409eff}
.ent-full{font-size:11px;color:#909399;margin-bottom:5px}
.ent-desc{font-size:12px;color:#555;line-height:1.5}
.flow-wrap{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.flow-step{display:flex;align-items:center;gap:7px}
.flow-num{width:26px;height:26px;border-radius:50%;background:#409eff;color:#fff;font-size:11px;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.flow-name{font-size:12px;font-weight:600;color:#151d2e}
.flow-algo{font-size:10px;color:#909399;font-family:monospace}
.flow-arr{color:#c0c4cc;font-size:16px}
.sec-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:22px}
.sec-card{background:#fff;border-radius:10px;padding:16px;box-shadow:0 1px 4px rgba(0,0,0,.06)}
.sec-badge{display:inline-block;font-size:11px;font-weight:600;padding:3px 10px;border-radius:12px;margin-bottom:8px}
.sec-t{font-size:13px;font-weight:600;color:#151d2e;margin-bottom:5px}
.sec-d{font-size:12px;color:#555;line-height:1.5;margin-bottom:7px}
.sec-assum{font-size:11px;color:#909399;font-family:monospace}
.scene-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:8px}
.scene-card{background:#fff;border-radius:10px;padding:20px;box-shadow:0 1px 4px rgba(0,0,0,.06)}
.scene-ico{font-size:30px;margin-bottom:8px}
.scene-t{font-size:14px;font-weight:600;color:#151d2e;margin-bottom:6px}
.scene-d{font-size:12px;color:#555;line-height:1.6}
</style>
