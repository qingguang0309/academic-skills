#!/bin/sh
# 收集 gen_deck.js 需要的三张图素材(不入库,按需生成):
#   assets/bse_eds_architecture.png  来自 figflow-demo 的架构图
#   assets/fig-000.png / fig-002.png 从 paper_article.pdf 抽取的 Fig.1 / Fig.2
set -e
cd "$(dirname "$0")"
mkdir -p assets
cp ../../figflow-demo/bse_eds_architecture.png assets/
pdfimages -png -f 3 -l 4 ../paper_article.pdf assets/fig
