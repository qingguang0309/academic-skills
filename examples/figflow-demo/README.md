# figflow 示例:BSE–EDS 融合分割网络架构图(四阶段)

分治出图工作流的端到端示例:5 个面板由并行代理生成(共享 field.py 同一视场),
箭头/色带/徽标由排版引擎按 figure.json 的锚点确定性合成,经对抗性审图两轮修正。

- 产物:bse_eds_architecture.png(250×132mm @300dpi)
- 复现:`PYTHONPATH=../../figflow python -m figflow figure.json`
- 面板重生成:逐个运行 panels/panel_*.py(cwd 为本目录)
