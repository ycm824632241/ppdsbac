# PPDSBAC 方案完整技术实现细节

本文件包含了 PPDSBAC 方案中所有实体的计算过程、参数来源及生成逻辑。

---

## 1. 全局参数初始化 (Global_Setup)
由系统生成，所有实体共享：
- **双线性映射**：$\mathcal{BG}(1^{l}) \to (e, p, \mathbb{G}_1, \mathbb{G}_2, \mathbb{G}_T)$。
- **生成元**：随机选择 $g_0, g, g_1, g_2, h_0, h_1 \in \mathbb{G}_1$ 和 $\mathfrak{g} \in \mathbb{G}_2$。
- **哈希函数**：
  - $\mathcal{H}_1: \{0,1\}^* \to \mathbb{G}_1$
  - $\mathcal{H}_2: \{0,1\}^* \to \mathbb{Z}_p$
  - $\mathcal{H}_3: \{0,1\}^* \to \mathbb{Z}_p$
- **公共参数集**：$params = (e, p, \mathbb{G}_1, \mathbb{G}_2, \mathbb{G}_T, g_0, g, g_1, g_2, h_0, h_1, \mathfrak{g}, \mathcal{H}_1, \mathcal{H}_2, \mathcal{H}_3)$。

---

## 2. 实体建立阶段 (Setup)
- **RA (注册机构)**：随机选 $x_{ra} \in \mathbb{Z}_p$，计算公钥 $Y_{RA} = \mathfrak{g}^{x_{ra}}$。
- **AA_j (授权机构)**：随机选 $x_j \in \mathbb{Z}_p$，计算公钥 $Y_j = \mathfrak{g}^{x_j}$。
  - 令 $\mathbb{A} = \{AA_1, \dots, AA_n\}$，$\mathbb{Y}_A = \{Y_1, \dots, Y_n\}$。
- **TA (追踪机构)**：随机选 $x_{ta} \in \mathbb{Z}_p$，计算公钥 $Y_{TA} = g^{x_{ta}}$。
- **User (用户)**：随机选 $x_u \in \mathbb{Z}_p$，计算公钥 $Y_U = g^{x_u}$。

---

## 3. 用户注册 (Regist)
1. **身份绑定**：用户 $U$ 向 TA 发送 $(ID_U, Y_U)$。
2. **所有权证明**：$U$ 提供 $\Pi_U = \text{NIZK}\{(x_u) : Y_U = g^{x_u}\}$。TA 验证后记录 $(ID_U, Y_U)$。
3. **凭证分发**：RA 随机选择 $e_u, d_u \in \mathbb{Z}_p$（需满足 $d_u \neq -x_{ra}$），计算并发送给用户：
   $$\sigma_U = (g_0 Y_U g_1^{e_u})^{\frac{1}{x_{ra} + d_u}} \in \mathbb{G}_1$$

---

## 4. 加密阶段 (Enc)
数据拥有者加密消息 $M \in \mathbb{G}_T$：
1. **选择策略**：确定授权机构子集 $\mathbb{S} = \{AA_{\lambda_1}, \dots, AA_{\lambda_k}\}$。
2. **计算权重**：对每个 $i \in \mathcal{I}$，计算 $z_i = \mathcal{H}_2(Y_{\lambda_i} || Y_{\lambda_1} || \dots || Y_{\lambda_k}) \in \mathbb{Z}_p$。
3. **生成密文**：随机选择 $t \in \mathbb{Z}_p$，计算：
   - $C_1 = M \cdot e\left(\mathcal{H}_1(W || TP_E), \prod_{i \in \mathcal{I}} Y_{\lambda_i}^{z_i}\right)^t$
   - $C_2 = \mathfrak{g}^t$
   - $C_3 = h_0^t$
   - $C_4 = h_1^t$
4. **输出**：$CT = (C_1, C_2, C_3, C_4)$ 及策略 $\mathbb{S}$。

---

## 5. 访问请求 (Acc_Req)
用户 $U$ 为获取权限，需执行以下计算：

### 5.1 生成证明 $\Pi_U^A$
**输入**：$x_u, \sigma_U, e_u, d_u$。
1. **盲化处理**：随机选择 $r_u, s_u \in \mathbb{Z}_p$，计算：
   - 假名：$P_{U,1} = g^{r_u}$，$P_{U,2} = g^{x_u} Y_{TA}^{r_u}$。
   - 盲化凭证：$\sigma'_U = \sigma_U g_2^{s_u}$。
   - 辅助因子：$y_u = s_u \cdot d_u \pmod p$。
2. **选择盲化因子 (Blinding Factors)**：随机选择 $v_{x_u}, v_{r_u}, v_{s_u}, v_{e_u}, v_{d_u}, v_{y_u} \in \mathbb{Z}_p$。
3. **计算承诺 (Commitments)**：
   - $R_1 = g^{v_{r_u}}$
   - $R_2 = g^{v_{x_u}} Y_{TA}^{v_{r_u}}$
   - $R_3 = e(g, \mathfrak{g})^{v_{x_u}} \cdot e(g_1, \mathfrak{g})^{v_{e_u}} \cdot e(\sigma'_U, \mathfrak{g})^{-v_{d_u}} \cdot e(g_2, \mathfrak{g})^{v_{y_u}} \cdot e(g_2, Y_{RA})^{v_{s_u}}$
4. **计算挑战 (Challenge)**：
   - $c = \mathcal{H}_3(params || P_{U,1} || P_{U,2} || \sigma'_U || R_1 || R_2 || R_3) \in \mathbb{Z}_p$。
5. **计算响应 (Responses)**：
   - $z_{x_u} = v_{x_u} + c x_u$, $z_{r_u} = v_{r_u} + c r_u$, $z_{s_u} = v_{s_u} + c s_u$
   - $z_{e_u} = v_{e_u} + c e_u$, $z_{d_u} = v_{d_u} + c d_u$, $z_{y_u} = v_{y_u} + c y_u \pmod p$
6. **发送证明**：$\Pi_U^A = (c, z_{x_u}, z_{r_u}, z_{s_u}, z_{e_u}, z_{d_u}, z_{y_u})$。

### 5.2 AA 验证证明 (Verify)
授权机构恢复承诺并验证：
1. **恢复承诺**：
   - $R'_1 = g^{z_{r_u}} P_{U,1}^{-c}$
   - $R'_2 = g^{z_{x_u}} Y_{TA}^{z_{r_u}} P_{U,2}^{-c}$
   - $R'_3 = e(g, \mathfrak{g})^{z_{x_u}} e(g_1, \mathfrak{g})^{z_{e_u}} e(\sigma'_U, \mathfrak{g})^{-z_{d_u}} e(g_2, \mathfrak{g})^{z_{y_u}} e(g_2, Y_{RA})^{z_{s_u}} \left( \frac{e(\sigma'_U, Y_{RA})}{e(g_0, \mathfrak{g})} \right)^{-c}$
2. **验证逻辑**：检查 $c \stackrel{?}{=} \mathcal{H}_3(params || P_{U,1} || P_{U,2} || \sigma'_U || R'_1 || R'_2 || R'_3)$。

### 5.3 权限生成
验证通过后，$AA_{\lambda_i}$ 根据请求的 $(W, TP_U)$ 计算：
- $K_i = \left(\mathcal{H}_1(W || TP_U) \cdot h_0 \cdot h_1^{\mathcal{H}_3(P_{U,1} || P_{U,2})}\right)^{x_{\lambda_i} z_i}$
- 其中 $z_i$ 重新计算自 $\mathcal{H}_2(Y_{\lambda_i} || \mathbb{Y}_{\mathbb{S}})$。

---

## 6. 权限聚合 (Acc_Agg)
用户 U 收到所有 $K_i$ 后，计算聚合权限：
$$K_U = \prod_{i \in \mathcal{I}} K_i$$

---

## 7. 解密阶段 (Dec)
用户计算：
1. **哈希权重**：$h_{ID} = \mathcal{H}_3(P_{U,1} || P_{U,2})$。
2. **公钥乘积项**：$Y_{\Pi} = \prod_{i \in \mathcal{I}} Y_{\lambda_i}^{z_i}$。
3. **恢复消息**：
   $$M = \frac{C_1 \cdot e(C_3 \cdot C_4^{h_{ID}}, Y_{\Pi})}{e(K_U, C_2)}$$

---

## 8. 追踪阶段 (Trace)
TA 识别恶意用户：
1. **提取公钥**：使用私钥 $x_{ta}$ 计算 $Y_U = P_{U,2} \cdot (P_{U,1}^{x_{ta}})^{-1}$。
2. **身份映射**：根据 $Y_U$ 在注册表 `table` 中检索 $ID_U$。