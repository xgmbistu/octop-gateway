# SOP 任务路由

先读取 `.wally/core/scope.md` 判断当前请求是否属于开发工作。咨询、只读分析、非开发对话和轻量纯文档操作直接处理，不因当前分支已有/缺少任务就自动启动或推进 SOP。以下路由只在开发请求或用户明确要求开始/继续 SOP 时执行。

以仓库根目录运行 `python3 .wally/scripts/sop_context.py` 的结果为准。它按实际分支匹配 `plans/*/00-overview.md`。已知实际分支和任务状态时直接使用，避免重复列目录、查分支或搜索 overview。

- 无 SOP 版本的历史任务：先读取 `.wally/compat/v1/CODEBUDDY.md`（不存在则使用快照 AGENTS.md/CLAUDE.md）。旧 review/commit/docs、模板与 Clarify 指引均从 compat/v1 读取，旧路径引用映射到快照；工具执行仍在实际仓库。不得混用新版全局规则。快照缺失则说明阻塞，不自动迁移。
- 有版本的任务：读取其 SOP 规则路径下的 workflow.md，再读取 `.wally/profiles/project.md`、`.wally/rules/`（历史任务如自带 `profile.md` / `_rules/` 则兼容读取）和当前阶段。按阶段加载同版本 gates.md、interaction.md 及项目扩展。绑定文件缺失应报错，不回退最新版。
- 无任务且用户未选分支：按需从 `.wally/install-state.json` 确认当前安装版本，说明当前分支和任务待创建，询问是否新建任务分支并结束本轮。只有当前分支可用于开发时才提供沿用选项。发出分支选择前，只读取判断可选分支所需的项目约束。项目 Profile、创建脚本、阶段文件、模板、历史版本和实现细节留到分支选定后按需加载。
- 用户已选分支：新建并切换，或按明确选择留在当前非 main/master/HEAD 的可用分支。读取 `.wally/profiles/project.md` 后运行 `python3 .wally/scripts/create_task.py YYYY-MM-DD_title --branch <选定分支>`。脚本不切分支、不执行测试、不提交。本次请求已写明任务分支时直接按该选择执行。

现有项目指令、编码约束与用户授权边界继续生效；入口中被识别并替换的旧 SOP 章节仅对旧任务从 compat/v1 加载。其他项目自定义流程如与本任务契约冲突需明确解决，不能猜测覆盖。
