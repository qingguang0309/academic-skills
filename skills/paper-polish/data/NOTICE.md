# 数据来源与许可

`lexicon.json` 中 `excess` 词族的倍数(ratio)由以下数据计算得到:

Kobak D., González-Márquez R., Horvát E.-Á., Lause J. Delving into LLM-assisted writing in biomedical
publications through excess vocabulary. *Science Advances* 11, eadt3813 (2025).
数据仓库:https://github.com/berenslab/llm-excess-vocab(`results/excess_words.csv`、`results/yearly-counts.csv.gz`)

计算方法:取 `excess_words.csv` 中标注为 style 的词,以含该词的摘要比例 p 计算
ratio = p(2024) / q,其中 q = p(2022) + 2·max(p(2022) − p(2021), 0)(按论文的线性外推反事实),
再按词族归并、剔除功能词与领域术语,人工分为 marker / density 两档。

原数据许可如下:

```
MIT License

Copyright (c) 2024 Dmitry Kobak, Rita González-Márquez

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
