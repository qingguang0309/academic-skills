# web/ — 工作台

仓库的本地工作台(Next.js):清爽的 Claude 风格界面,四个视图——

- **概览**:技能/工作流卡片、统计、最新产物、最近运行
- **运行**:预置示例生成任务(白名单脚本,非任意命令),实时日志与进度,完成后核对产物并一键跳转预览
- **资源**:扫描 `examples/` 的全部产物(PNG/PDF/PPTX),按示例分组,点击即预览(PPTX 走同名 PDF)
- **技能**:把仓库内的 Agent Skills 安装/更新到 `~/.claude/skills`,并可直接阅读 SKILL.md 与规范文档

## 启动

```bash
cd web
npm install
npm run dev    # http://localhost:3620
```

任务的运行时依赖与各 skill 相同(Python + matplotlib/scikit-image、Node + pptxgenjs、LibreOffice、tectonic 等);缺依赖时任务会失败并在日志里给出提示,不影响其他功能。

## 结构

```
web/
├── app/
│   ├── page.tsx            # 概览
│   ├── runs/page.tsx       # 运行中心(轮询日志)
│   ├── resources/page.tsx  # 资源库(预览弹窗)
│   ├── skills/page.tsx     # 技能管理(安装/移除/看文档)
│   └── api/                # overview / skills / runs / artifacts / file
├── lib/
│   ├── paths.ts            # 仓库根定位与路径安全校验
│   ├── skills.ts           # 扫描 skills/、frontmatter 解析、安装状态
│   ├── artifacts.ts        # 扫描 examples/ 产物
│   └── runs.ts             # 任务白名单 + 进程注册表(内存)
└── components/ui.tsx       # Card/Badge/Modal/极简 Markdown 渲染
```

安全边界:文件服务仅限仓库内白名单扩展名;任务只能按 id 触发白名单脚本;运行记录存内存,dev server 重启即清空。
