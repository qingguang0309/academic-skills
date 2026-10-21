# 上游来源

- 上游：<https://github.com/wheresryan22/anatomy>（MIT，版权 © 2026 Ryan，见 `LICENSE`）
- 同步到：`1482e84`（2026-10-18，Printable sheets: A4 and Letter PDFs from any figure）

## 与上游的差别

- `SKILL.md` 的 description 改写：补了中文触发词（等轴测图、装置示意图、仪器结构图……），并压到 1024 字以内；正文未动。
- 去掉了只服务于上游仓库开发的文件：`README.md`、`CHANGELOG.md`、`CONTRIBUTING.md`、`CODE_OF_CONDUCT.md`、`SECURITY.md`、`.github/`、`agents/`、`evals/`、`tests/`、`scripts/*.test.mjs`。
- 去掉了 `examples/` 里构建出的 `.html` 与 `.pdf`（约 25 MB）。它们都能重建：`node examples/<name>/build.mjs [--light]`，打印版再跑 `node scripts/print.mjs examples/<name>/sheet.mjs --format all`。

## 跟上游同步

```bash
git clone --depth 1 https://github.com/wheresryan22/anatomy /tmp/anatomy-src
rsync -a --delete --exclude-from=- /tmp/anatomy-src/ skills/anatomy/ <<'EOF'
.git
.github
tests
agents
evals
*.test.mjs
examples/**/*.html
examples/**/*.pdf
README.md
CHANGELOG.md
CONTRIBUTING.md
CODE_OF_CONDUCT.md
SECURITY.md
.gitignore
.gitattributes
UPSTREAM.md
EOF
```

同步后重新改 `SKILL.md` 的 description，并更新上面的提交号。
