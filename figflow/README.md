# figflow — 专门出图的分治工作流(多面板大图)

## 为什么需要它

实测规律:**单面板生成质量很高,但把多个面板塞进一个大脚本时,箭头、标注、
色带这些"关系性"元素必然出问题**——模型在大画布上手拍坐标,错一处毁全图。

figflow 把两类工作彻底分开:

| 工作 | 谁做 | 为什么 |
|---|---|---|
| 面板内容(显微图/散点/图结构/分割图…) | **并行子代理**,一人一板,各自渲染自检 | 单面板是模型的强项 |
| 箭头/色带/徽标/标题/图例/伪3D块 | **确定性排版引擎**(compose.py) | 箭头端点由元素矩形的锚点(`id.edge:t`)计算,机制上不可能悬空或错位 |
| 跨面板一致性(同一视场/同一配色) | **共享数据模块**(field.py 之类) | 所有面板 import 同一个种子固定的生成函数 |
| 终稿把关 | **对抗性审图代理** + 人 | 独立视角挑刺,反馈到 spec 或面板回炉 |

## 工作流四步

```
1. 写 spec(figure.json):画布/色带/面板矩形/徽标/箭头锚点/图例/脚注
2. Workflow 并行:每个面板一个代理(拿到共享数据模块 + 尺寸契约 + 调色板),
   产出满幅无边距 PNG,自己 Read 检查到满意
3. python -m figflow figure.json   ← 确定性合成,箭头永远贴锚点
4. 审图:自己逐区域看 + 派一个对抗性审稿代理;问题按归属修 spec 或回炉面板,重合成
```

面板契约(给每个面板代理的硬约束):`fig.add_axes([0,0,1,1])` 满幅、`axis('off')`、
`savefig(dpi=300)` 不带 bbox_inches、无边框无标题(关系性元素归引擎)、确定性种子、
用共享数据模块保证同视场。

## spec 一览(单位 mm,原点左下)

```jsonc
{
  "canvas_mm": [250, 132], "dpi": 300, "palette": {"blue": "#2563EB"},
  "bands":  [{"id": "b1", "rect": [6,10,58,114], "label": "① 输入与配准"}],
  "panels": [{"id": "bse", "file": "panels/panel_bse.png", "rect": [12,80,40,30],
              "title": "BSE 图", "subtitle": "…"}],
  "items":  [{"type": "badge|text|slabs|heatgrid", ...}],
  "arrows": [{"from": "bse.right:0.5", "to": "slabs.left:0.55", "color": "$blue", "rad": 0.18}],
  "legend": {"pos": [10,6.6], "entries": [["C-(A)-S-H 凝胶", "$csh"]]},
  "footnote": {"pos": [128,2.9], "text": "注:…"}
}
```

锚点语法 `id.edge[:t]`:`edge ∈ left/right/top/bottom`,`t` 为沿边比例(默认 0.5)。
伪3D 块(slabs)注册的是**有效绘制范围**,箭头贴末端棱边而非外包矩形。

## 使用

```bash
pip install numpy scipy matplotlib scikit-image
PYTHONPATH=figflow python -m figflow examples/figflow-demo/figure.json
```

完整示例见 [examples/figflow-demo](../examples/figflow-demo/):BSE–EDS 融合分割
网络四阶段架构图(与 examples/bse-eds-report 同一课题),含 5 个面板脚本、
共享相场模块、spec 与合成产物。paperflow 的图表链生成单图;需要**多面板架构图/
技术路线图**时用 figflow。
