# PPDSBAC 系统演示

**Privacy-Preserving Decentralized Signature-Based Access Control**

> Han, Chen, Susilo — IEEE Transactions on Dependable and Secure Computing, Vol.22 No.5, 2025

---

## 快速启动

### 1. 启动后端

```bash
cd backend
pip install flask flask-cors
python app.py
# 后端运行在 http://localhost:5000
```

### 2. 启动前端

```bash
cd frontend
npm install
npm run dev
# 前端运行在 http://localhost:3000
```

浏览器打开 http://localhost:3000 即可访问系统。

---

## 系统功能

| 页面 | 功能 |
|------|------|
| 系统概览 | 方案介绍、核心创新点、参与实体、安全定理 |
| 系统初始化 | Global_Setup → RA/TA/AA/User 密钥生成 → Regist |
| 协议流程 | Enc → Pseudonym → Acc_Req → Acc_Agg → Dec → Trace |
| 安全属性 | 不可链接性 & 不可伪造性交互演示，方案对比表 |
| 性能评估 | 复现论文 Fig.3 / Fig.4，n=10/20/30 对比 |
| 完整演示 | 一键端到端演示，实时步骤时序图 |

---

## 核心创新点（论文 Section I-B）

1. **不可链接访问请求** — ElGamal 伪名 + ZK 证明（DDH 假设）
2. **不可伪造访问权限** — BLS 紧凑多签名 [Boneh et al. 2018]（Co-CDH 假设）
3. **可聚合访问权限** — k 个签名聚合为 1 个 AK_U（BLS 乘法同态）
4. **非交互式认证** — OSBE 加密解耦 SP 在线要求（DBDH 假设）
5. **可追踪溯源** — TA 用 ElGamal 解密还原 PK_U（完美正确性）
6. **直接撤销** — 时间段绑定，TP_E ≠ TP_U 自动拒绝

---

## 目录结构

```
ppdsbac/
├── backend/
│   ├── app.py              # Flask 入口
│   ├── requirements.txt
│   ├── crypto/__init__.py  # 密码学核心（论文所有算法）
│   └── api/
│       ├── setup.py        # 初始化 API
│       ├── workflow.py     # 协议流程 API
│       ├── bench.py        # 性能测试 API
│       └── security.py     # 安全属性演示 API
└── frontend/
    ├── src/
    │   ├── views/          # 6个页面
    │   ├── api/index.js    # Axios 封装
    │   └── stores/         # Pinia 状态
    └── package.json
```
