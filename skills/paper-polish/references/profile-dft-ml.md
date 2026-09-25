# 领域配置:DFT + 机器学习期刊论文

适用:计算材料 / 计算化学中 DFT 与机器学习结合的期刊论文(npj Comput. Mater.、JACS、Chem. Mater.、
J. Phys. Chem.、Digital Discovery、JCTC 等)。`deai_lint.py --profile dft-ml` 会自动查下表里带 `spec/` 代码的项。

这类论文的 AI 初稿有一个共同特征:**方法写得像综述,结果写得像广告**。泛函、U 值、数据划分这些
审稿人一眼就找的细节没有,却有 `remarkable accuracy`、`DFT-level accuracy`、`generalizes well`。
改写的重点是把每个结论挂到可核对的数字上,缺的数字交给作者补。

## 必查清单(缺了就写 `[请确认: …]`,不替作者编)

### DFT 部分

| 项目 | 代码 | 审稿人期待的写法 |
|---|---|---|
| 程序与赝势 | — | `VASP 6.3 with PAW potentials (PBE_54)` |
| 交换关联泛函与色散校正 | `spec/dft-functional` | `PBE with D3(BJ) dispersion`;涉及能隙写明是否用 HSE06 |
| +U 值 | `spec/hubbard-u` | 逐元素给 `U_eff`,注明来源(如 Materials Project 的拟合值) |
| 截断能 | `spec/cutoff` | `520 eV` |
| k 点 | `spec/k-points` | `Γ-centered 4 × 4 × 1` 或 k 点密度 |
| 收敛判据 | `spec/convergence` | `10⁻⁵ eV`(电子步),`0.02 eV Å⁻¹`(离子步) |
| 表面模型 | — | 层数、固定层数、真空层厚度、偶极校正 |
| 自旋与磁构型 | — | 是否自旋极化,初始磁矩与测试过的构型 |
| 溶剂化 / 电位 | — | 隐式溶剂模型,计算氢电极(CHE)的参照 |

### 机器学习部分

| 项目 | 代码 | 审稿人期待的写法 |
|---|---|---|
| 数据量与来源 | `spec/dataset-size` | `12 480 structures from Materials Project (v2023.11)`,自算数据写清计算设置是否与上文一致 |
| 划分方式 | `spec/split` | 比例 + 方式(随机 / 按成分 / 按结构原型),以及怎么防止泄漏(同一体系的不同构型不跨集合) |
| 误差指标与单位 | `spec/metric`、`spec/metric-unit` | `MAE = 0.041 eV/atom`,最好同时给 RMSE 和误差分布 |
| 基线 | `spec/baseline` | 至少一个:线性模型、已发表模型(CGCNN、MEGNet、M3GNet、MACE…)或简单描述符 |
| 分布外测试 | `spec/generalization` | 声称可泛化就要有按化学体系留出的测试;没有就写 `on the held-out test set` |
| 可解释性方法 | `spec/interpretability` | SHAP、置换重要性、SISSO…,并写出具体得到了什么结论 |
| 不确定度 | — | 多次训练的方差、集成或主动学习中的不确定度估计 |
| 代码与数据 | — | 仓库地址与版本、数据的 DOI(npj / Digital Discovery 要求数据可用性声明) |

## 这个领域的高频 AI 病灶

| AI 初稿 | 问题 | 改法 |
|---|---|---|
| `achieves DFT-level accuracy` | 精度无数值、无参照 | `MAE of 0.03 eV/atom relative to PBE` |
| `remarkable/excellent predictive performance` | 空形容词 | 数值 + 基线:`vs. 0.067 eV/atom for CGCNN on the same split` |
| `generalizes to unseen materials` | 随机划分不能支撑泛化 | 有 OOD 测试就给结果,没有就收窄措辞 |
| `reveals the underlying mechanism` | 相关性写成机理 | `the O 2p band center correlates most strongly (r = …) with …`;机理要另有证据 |
| `provides physical insights` | 说有洞见不说洞见 | 写出洞见本身 |
| `accelerates materials discovery by orders of magnitude` | 无对比口径 | 给出时间或成本:每个结构 DFT 需 X CPU·h,模型需 Y s |
| `robust and transferable potential` | 两个未验证的属性 | 给出测试条件:温度范围、未见相、MD 稳定时长 |
| `high-throughput screening of a vast chemical space` | 空间多大? | `4 312 ABO₃ compositions` |
| `the synergistic effect of A and B` | 没有定义 synergy | 说清两者分别和共同带来的变化量 |

## 化学期刊的写法习惯

- 数字与单位之间留空格:`0.041 eV/atom`、`500 °C`;负指数写法:`eV Å⁻¹`、`mmol g⁻¹ h⁻¹`。
- 时态:做了什么用过去时(`We computed`),图表显示什么、已确立的事实用现在时(`Figure 3 shows`)。
- 引言的结构:领域问题 → 已知数字与已有方法 → 具体的空白(哪一类体系、哪个量算不准)→ 本文做了什么。
  AI 初稿最常见的问题是空白写成"existing methods have limitations",没有说哪种方法在哪种体系上差多少。
- 结论段不要复述摘要,写这项工作能用来做什么、适用范围到哪里、下一步需要什么数据。
