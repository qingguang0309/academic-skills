# 退役磷酸铁锂电池湿法回收工艺评估报告 —— docxkit 生成脚本
# 数据为合成示意值，用于演示 Word 版式与编号机制；真实报告请替换为实测结果。
import sys
sys.path.insert(0, "/Users/shodan/project/academic-skills/skills/paper-word/scripts")
from docxkit import Doc

d = Doc(
    title="退役磷酸铁锂电池湿法回收工艺评估",
    subtitle="以锂回收率与单位处理成本为判据",
    author="李 明", school="材料科学与工程学院", major="材料物理与化学",
    advisor="王 立 教授", student_id="2201110001",
    date="二〇二六年七月",
    header_text="退役磷酸铁锂电池湿法回收工艺评估",
    photos_required=True,
)

d.cover(occasion="课题组技术评估报告")

d.abstract_zh(
    "本报告评估一条以硫酸—双氧水体系为核心的退役磷酸铁锂电池湿法回收路线，"
    "判据是锂回收率与单位处理成本。在 90 ℃、硫酸浓度 2 mol·L⁻¹、液固比 10∶1、"
    "浸出 90 min 的条件下，锂浸出率达 95.4%，继续提高酸浓度至 3 mol·L⁻¹ 只增加 0.5 个百分点，"
    "却使废液处理量上升四成，因此 2 mol·L⁻¹ 是本体系的合理上限。\n\n"
    "浸出过程符合收缩核模型的界面化学反应控制式，拟合决定系数 0.993，"
    "明显优于内扩散控制式的 0.951；表观活化能 48.6 kJ·mol⁻¹，与该判定一致。"
    "这意味着提高温度比延长时间更有效，也解释了为什么单纯延长浸出时间收益有限。\n\n"
    "经济性测算显示，本路线单位处理成本 6.41 万元·t⁻¹，较火法路线的 7.67 万元·t⁻¹ 低 16.4%，"
    "差异主要来自能耗项（1.36 对 4.82 万元·t⁻¹）。但湿法路线的废液处理成本是火法的 2.5 倍，"
    "若厂区不具备蒸发结晶配套，这一优势会被抵消。报告最后给出中试放大前需要补做的三项验证。",
    keywords=["磷酸铁锂", "湿法回收", "浸出动力学", "碳酸锂", "工艺评估"],
)

d.abstract_en(
    "This report evaluates a hydrometallurgical route for spent LiFePO4 batteries based on a "
    "sulfuric acid-hydrogen peroxide system, judged by lithium recovery and unit processing cost. "
    "Under 90 degrees Celsius, 2 mol per litre sulfuric acid, a liquid-to-solid ratio of 10 to 1 "
    "and 90 minutes of leaching, lithium extraction reached 95.4 percent. Raising the acid "
    "concentration to 3 mol per litre added only 0.5 percentage points while increasing effluent "
    "volume by about 40 percent.\n\n"
    "Leaching follows the shrinking-core model under interfacial chemical reaction control "
    "(R squared 0.993), clearly better than the internal diffusion form (0.951). The apparent "
    "activation energy of 48.6 kJ per mole agrees with this assignment, indicating that raising "
    "temperature is more effective than extending time.\n\n"
    "The unit processing cost is 6.41 x 10^4 CNY per tonne, 16.4 percent below the pyrometallurgical "
    "route, with the difference dominated by energy consumption. Effluent treatment, however, costs "
    "2.5 times as much, so the advantage disappears without on-site evaporative crystallisation.",
    keywords=["spent LiFePO4", "hydrometallurgy", "leaching kinetics", "lithium carbonate"],
)

d.toc()

# ============ 第一章 ============
d.chapter("引言")
d.section("评估背景")
d.para(
    "磷酸铁锂电池的退役量在 2025 年后进入快速上升期，而现行回收路线的经济性主要由钴镍支撑，"
    "磷酸铁锂体系不含钴镍，回收价值集中在锂上。这使得针对三元电池设计的火法路线"
    "在处理磷酸铁锂时利润空间很窄，行业实际处理量远低于退役量。"
)
d.para(
    "本报告要回答的问题只有一个：以硫酸—双氧水体系提锂，能否在锂回收率与单位处理成本上"
    "同时优于火法路线。报告不讨论正极材料的直接再生路线——该路线要求进料成分稳定，"
    "与混合来源的退役包实际情况不符{[yao2018]}。"
)
d.section("评估对象与边界")
d.para(
    "评估对象为某商用储能电站退役的磷酸铁锂电池模组，标称容量 280 A·h，"
    "循环 4 200 次后容量保持率 78%，见 {@fig:pack}。边界为从整包入厂到产出电池级碳酸锂，"
    "不含运输与包装环节；铝铜箔碎料按外售金属计入收益，不计其再生成本。"
)
d.figure("assets/electric_vehicle_battery_2.jpg",
         "退役磷酸铁锂电池模组（评估对象示例）", label="fig:pack", width_cm=10)

# ============ 第二章 ============
d.chapter("工艺路线与实验方法")
d.section("工艺路线")
d.para(
    "全流程分预处理与浸出提纯两段。预处理段按拆解规范的作业程序执行{[gb2017]}，"
    "任务是把黑粉从集流体上分离干净，见 {@fig:pre}；"
    "浸出液的处理见 {@fig:post}。两段之间以黑粉的铝含量为交接指标，要求低于 0.8%，"
    "该指标直接决定后续除杂的碱耗。"
)
d.figure("assets/flow_pre.png", "预处理段工艺流程", label="fig:pre", width_cm=9)
d.para(
    "破碎在负压惰性气氛下进行。磷酸铁锂本身不释氧，但电解液中的碳酸酯在破碎升温时会挥发，"
    "常压破碎会带来可燃气体积聚风险。"
)
d.figure("assets/flow_post.png", "浸出液处理与产品流程", label="fig:post", width_cm=10)

d.section("试剂与设备")
d.para("主要试剂与设备见 {@tab:mat}。所有浓度均以配制后的实际标定值计，不用标称值。")
d.table(
    [["名称", "规格 / 型号", "用途"],
     ["硫酸", "分析纯，98%", "浸出剂"],
     ["过氧化氢", "分析纯，30%", "还原 Fe(III)，促进锂溶出"],
     ["碳酸钠", "工业级，99.2%", "沉锂"],
     ["机械搅拌反应釜", "5 L，聚四氟内衬", "浸出"],
     ["电感耦合等离子体发射光谱仪", "Agilent 5110", "溶液锂铁铝定量"]],
    caption="主要试剂与设备", label="tab:mat",
    note="注：试剂均未做进一步纯化；ICP-OES 每批次随行标准曲线，相关系数不低于 0.999。")

d.section("浸出动力学的处理方法")
d.para(
    "以收缩核模型判定控制步骤。若过程由界面化学反应控制，浸出分数 x 与时间 t 满足式 {@eq:sc}；"
    "若由固膜内扩散控制，则满足式 {@eq:df}。两式分别拟合，取决定系数高者为控制步骤；"
    "无机酸浸出正极材料的动力学多按该模型处理{[chen2017]}。"
)
d.formula("assets/eq/shrink.png", label="eq:sc")
d.formula("assets/eq/diff.png", label="eq:df")
d.para(
    "锂回收率按式 {@eq:rec} 定义，以进料黑粉的锂总量为基准，"
    "而非以浸出液锂量为基准——后者会把沉锂环节的损失掩盖掉。"
)
d.formula("assets/eq/rec.png", label="eq:rec")
d.para(
    "浸出实验在通风橱内的恒温水浴中进行，见 {@fig:lab}。每个条件平行三次，"
    "报告极差而非标准差：三次重复不足以支撑标准差的统计意义{^平行样本量受釜位限制；"
    "中试阶段应提高到 n = 6 并改报标准差。}。"
)
d.figure("assets/laboratory_fume_hood_che_1.jpg",
         "浸出实验的操作环境", label="fig:lab", width_cm=9)

# ============ 第三章 ============
d.chapter("浸出结果与动力学")
d.section("温度与酸浓度的影响")
d.para(
    "2 mol·L⁻¹ 是本体系的合理上限。如 {@fig:leach} 所示，在 90 ℃ 下，"
    "硫酸浓度从 1.0 提高到 2.0 mol·L⁻¹ 使锂浸出率从 88.1% 升至 95.4%，"
    "继续提高到 3.0 mol·L⁻¹ 只再增加 0.5 个百分点。"
)
d.figure("assets/fig_leach.png", "温度与硫酸浓度对锂浸出率的影响（合成示意数据）",
         label="fig:leach", width_cm=15)
d.para(
    "多出来的那 0.5 个百分点代价不小：酸量增加 50% 意味着后续中和碱耗同步上升，"
    "实测废液体积增加约四成。按第四章的成本结构，这部分增量已经超过多回收的锂所对应的收益。"
)

d.section("控制步骤的判定")
d.para(
    "浸出由界面化学反应控制。两种模型的拟合结果见 {@fig:kin}：界面反应控制式的决定系数为 0.993，"
    "内扩散控制式为 0.951，前者在三个温度下都给出更接近直线的关系。"
)
d.figure("assets/fig_kinetics.png", "收缩核模型的两种控制形式拟合对比（合成示意数据）",
         label="fig:kin", width_cm=15)
d.para(
    "由 60—90 ℃ 三点的速率常数按阿伦尼乌斯关系求得表观活化能 48.6 kJ·mol⁻¹。"
    "该值落在化学反应控制的常见区间（40—100 kJ·mol⁻¹），与拟合判定互为印证。"
    "工程含义是：在该体系里提高温度比延长时间更有效——这与 {@tab:opt} 中"
    "延长时间的边际收益迅速衰减一致。"
)
d.table(
    [["条件", "浸出 60 min", "浸出 90 min", "浸出 120 min"],
     ["75 ℃ / 2.0 mol·L⁻¹", "86.2", "92.8", "93.5"],
     ["90 ℃ / 2.0 mol·L⁻¹", "91.7", "95.4", "95.8"],
     ["90 ℃ / 3.0 mol·L⁻¹", "93.0", "95.9", "96.2"]],
    caption="不同条件下的锂浸出率（%，n = 3 的均值）", label="tab:opt",
    note="注：极差均不超过 0.9 个百分点；合成示意数据。")

# ============ 第四章 ============
d.chapter("经济性与环境影响")
d.section("单位处理成本")
d.para(
    "本路线单位处理成本 6.41 万元·t⁻¹，比火法路线低 16.4%。成本构成见 {@fig:cost}，"
    "差距几乎全部来自能耗：火法需要将物料加热到 1 000 ℃ 以上，能耗项占其总成本的 63%；"
    "湿法的最高温度是沉锂环节的 95 ℃。"
)
d.figure("assets/fig_cost.png", "两条路线的单位处理成本构成（合成示意数据）",
         label="fig:cost", width_cm=15)
d.para(
    "这个优势有前提。湿法路线的废液处理成本是火法的 2.5 倍（1.12 对 0.44 万元·t⁻¹），"
    "其中主要是硫酸钠母液的蒸发结晶。若厂区没有现成的蒸发配套而需外委处理，"
    "按当前市价每吨母液外委费用约 260 元计，成本优势将从 16.4% 收窄到 4% 以内。"
)

d.section("物料衡算与产品指标")
d.para("以 1 t 黑粉进料为基准的物料衡算见 {@tab:mb}。")
d.table(
    [["项目", "质量 / kg", "锂含量 / %", "锂分配 / %"],
     ["进料黑粉", "1 000", "3.62", "100.0"],
     ["浸出液", "—", "—", "95.4"],
     ["滤渣（石墨与磷酸铁）", "612", "0.17", "2.9"],
     ["碳酸锂产品", "182", "18.78", "91.2"],
     ["母液与洗液损失", "—", "—", "4.2"]],
    caption="以 1 t 黑粉计的锂物料衡算", label="tab:mb",
    note="注：锂分配以进料锂总量为基准；合成示意数据，衡算闭合差 1.7%。")
d.para(
    "浸出率 95.4% 与最终回收率 91.2% 之间的 4.2 个百分点损失在沉锂环节。"
    "这部分损失可以通过母液返浸回收，但会累积钠离子，三次循环后产品钠含量将超出电池级标准。"
)

# ============ 第五章 ============
d.chapter("结论与建议")
d.section("结论")
d.para(
    "在锂回收率与单位处理成本两项判据上，本路线均优于火法：90 ℃、2 mol·L⁻¹、90 min 条件下"
    "锂回收率 91.2%，单位处理成本 6.41 万元·t⁻¹，分别对应火法的 84% 与 7.67 万元·t⁻¹。"
    "浸出由界面化学反应控制，表观活化能 48.6 kJ·mol⁻¹，因此工艺优化应优先调温度而非时间。"
)
d.para(
    "成本优势依赖厂区具备蒸发结晶配套。缺少该配套时，两条路线的成本差距缩小到 4% 以内，"
    "不足以支撑路线切换。"
)
d.section("中试放大前需补做的验证")
d.para(
    "第一，母液返浸的钠累积上限。本报告只做到单次浸出，未验证循环三次后的产品钠含量，"
    "而这直接决定母液能否内循环，也就决定了废液量的真实水平。"
)
d.para(
    "第二，黑粉铝含量波动的影响。本报告的黑粉铝含量稳定在 0.6%—0.8%，"
    "实际混合来源的退役包该指标可能上到 2%，除杂碱耗与铝渣量都会显著变化。"
)
d.para(
    "第三，放大后的传热限制。5 L 釜可视为等温，吨级釜内的温度梯度会使实际反应温度低于设定值；"
    "既然过程由化学反应控制，温度偏差对速率的影响会被活化能放大。"
)

d.refs([
    dict(key="gb2017", type="S", authors=["全国有色金属标准化技术委员会"],
         title="车用动力电池回收利用 拆解规范: GB/T 33598-2017",
         place="北京", publisher="中国标准出版社", year=2017),
    dict(key="yao2018", type="J", authors=["YAO Y", "ZHU M", "ZHAO Z", "et al"],
         title="Hydrometallurgical processes for recycling spent lithium-ion batteries: a critical review",
         journal="ACS Sustainable Chem Eng", year=2018, volume=6, issue=11,
         pages="13611-13627"),
    dict(key="chen2017", type="J", authors=["CHEN X", "MA H", "LUO C", "et al"],
         title="Recovery of valuable metals from waste cathode materials of spent "
               "lithium-ion batteries using mild phosphoric acid",
         journal="J Hazard Mater", year=2017, volume=326, pages="77-86"),
])

d.acknowledge(
    "感谢王立教授在评估边界设定与动力学判据上的指导，避免了把浸出率直接当作回收率的误判。"
    "张华博士完成了全部 ICP-OES 定量，陈悦协助了物料衡算的复核。"
    "浸出实验在学院公共实验平台完成，感谢平台老师在釜位排期上的协调。",
    funding=[("国家重点研发计划", "2024YFB3812000"),
             ("北京大学基础科研种子基金", "BMU2026SEED")],
)

d.build("lfp_recycling_report.docx")
