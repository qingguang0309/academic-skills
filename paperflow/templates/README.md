# templates 目录布局

本目录存放 paperflow 流水线的 LaTeX 输出模板。`article/` 是现成模板:单栏
SCI 期刊投稿样式,`template.tex` 内含 `@@NAME@@` 占位符,由流水线用 Python
字符串替换填入标题、摘要、正文与参考文献配置,占位符契约详见
`article/README.md`。`pkuthss/`(北大学位论文)不在此处存放静态模板文件,
而是由流水线在运行时基于 vendor 目录中的 pkuthss 宏包动态渲染生成,因此
本目录只保留这份说明,不含 pkuthss 模板本体。
