# paper-figures 评测:首次出图可用率

改 skill 之后,图到底是变好了还是变坏了?这套评测用一个数字回答:
**固定 5 道题,模型第一次交付的图里,有几张不用人改就能直接用。**

## 题目

| 题目 | 考什么 |
|---|---|
| `t1_xrd` | XRD 堆叠谱图 + 标准卡片竖线,标晶面,指出杂相峰(Angew 单栏) |
| `t2_cv_eis` | 多扫速 CV + Nyquist 双 panel,两轴等比例,标拟合参数(JACS 双栏) |
| `t3_isotherm` | N₂ 吸脱附等温线,实心/空心区分吸附与脱附,孔径分布插图(Elsevier 单栏) |
| `t4_roadmap` | 三泳道三年技术路线图,反馈虚线,节点和连线标签一个不少(Word 版心 16 cm) |
| `t5_toc` | JACS TOC 图,3.25 × 1.75 in,关键数字可读 |

数据是 `make_data.py` 按固定种子合成的,物理上合理,不代表任何真实样品。
题目文字和检查项在 `tasks/*/task.json`。**改题目会让历史分数不可比**,确有必要时再改。

## 三关

模型交付后立即**冻结**(记下全部文件的哈希、设为只读),之后任何改动都会被查出来并判不通过。

| 关 | 判定 | 怎么查 |
|---|---|---|
| 1 内容正确 | 交付齐全(脚本或流程图规格 + PDF + PNG),删掉图后在干净副本里重跑能复现,题目的内容检查项全部通过 | 自动:探针在重跑时给每张图拍快照,查轴标签与单位、标注、尺寸、字号、虚线、色标、PNG 分辨率 |
| 2 体检通过 | 0 条 error | 自动:探针用**被测版本**的 `check_layout` 独立再查一遍,脚本里写了 `strict=False` 也逃不掉 |
| 3 人工看过 | 有人打开 PNG,判定可以直接用 | `review` 子命令逐题打开图片、记录判定与理由 |

三关都过才算"首次可用"。自动两关只能说明没有已知缺陷,好不好看要人来判断,三者分开记录,不互相替代。

## 用法

```bash
cd evals/paper-figures
python3 run.py start --model claude-sonnet-5 --budget 5 --jobs 2   # 准备 + 运行 + 自动评分
python3 run.py review <run_id> --open                              # 人工判定
python3 run.py report <run_id> --record                            # 汇总并追加到 history.jsonl
```

- 默认用 `claude -p` 在每道题的独立工作区里运行,skill 装在工作区的 `.claude/skills/paper-figures`,
  并用 `--setting-sources project` 隔离本机用户级的 skill 与插件,测到的就是这份 skill。
- `--skill` 可以指向别的 skill 目录或打包好的 `.skill`,用来比较两个版本。
- `--agent-cmd` 可换成任意命令(模板变量 `{ws}`、`{prompt_file}`),用于接其它 agent 或自测评分器。
- 运行目录在 `runs/`(不入库);`history.jsonl` 每行一次运行,记录 skill 内容哈希、仓库提交、模型、各题三关结果和花费。

## 读结果

`report` 的备注列会列出没过的检查项和实测值,例如 `Nyquist 两轴等比例(单位像素比 x/y = 2.46)`、
`text/overlap: 文字互撞: …`。同一题反复失败在同一项上,说明 skill 的规则或工具该改;
"没看到读取工作区 skill" 表示模型这次没用 skill,这一题的分数不能说明 skill 的好坏。

每次改 skill 前后各跑一次,比较 `history.jsonl` 里的首次可用率;模型输出有随机性,
差一题以内不要下结论,需要时对同一版本多跑几次。
