<!-- wally-init:entry:start -->
## 先判断是否属于开发任务

- 必须走开发 SOP：实现功能、修复缺陷、重构、性能优化，以及改变程序行为的接口、数据结构、配置、脚本、Agent 规则/Skill 等修改。开发需求中的方案、契约和配套文档也属于该任务；不能因为改动少或暂时只写文档而豁免。用户明确要求开始/继续 SOP 时按任务上下文执行。
- 直接处理、不创建 SOP 任务：问题咨询、原理解释、只读分析/独立审阅、状态查询、与开发无关的对话，以及纯文档措辞整理，以及暂存/提交已有改动（git add / git commit）。先核对实际请求和 diff；提交操作本身不要求新建 SOP 任务，不因已有改动包含代码而倒补六阶段产物；仍须遵守已有开发任务的交付门禁、项目提交规范与用户授权。
- 是否进入 SOP 取决于当前请求的工作性质，不取决于问句形式、文件扩展名、改动行数或当前分支是否已有任务。咨询过程中用户转而要求开发修改时，再进入开发 SOP；混有代码、运行配置、规则或行为变更时不套用纯文档豁免。已有开发任务的代码交付也不能通过改称“只做提交”绕过适用门禁；工具 Hook 对 Git 操作中立放行不代表门禁已完成或已获得 Commit/Push 授权。

## 开发任务的 SOP 启动检查

确认属于开发任务后，任务简单、改动少、只加一个页面都不是跳过 SOP 的理由。读取本入口不代表已完成任务路由；在探索实现方案、编辑业务文件或执行变更命令前，必须完成：

1. 读取 `.wally/core/entry.md`，运行 `python3 .wally/scripts/sop_context.py` 按实际分支定位任务。已有路由结果时直接使用；需要补查时只查缺失字段。
2. 已定位任务时，按脚本输出加载任务 overview、绑定规则、项目配置和当前阶段。无任务且用户未指定分支时，按入口发分支选择并等待。本轮的路由到此结束。缺文件、多任务匹配等其他问题须解决后再继续实现。
3. 在首次工作说明中报告实际分支、任务目录、规则版本和当前阶段。无任务时说明待创建，版本标注为当前安装版本。只报告已查证的事实。
4. 进入每个阶段前读取对应阶段文件与所需绑定规则，填写 Clarify 和 Plan 后再实现。压缩上下文、恢复会话、切换分支及委派子 Agent 后重新定位；委派时明确传入任务目录、规则版本和阶段，子 Agent 也执行本检查。

5. 知识库先读 `.wally/docs/INDEX.md`，按任务绑定版本的 `core/knowledge.md` 读取、更新和验收相关页。索引缺失时回查 Profile 的实际文档路径与源码，并记录缺口。
6. 仓库受管 Skills 固定存放在 `.agents/skills/`（如 `clarify`、`sop-aware-code-review`、`wally-open-cli`），各主流 IDE/CLI 的 `skills/` 目录通过软链复用。进入 `01 Clarify`（且未按 SOP 正式跳过）时，必须先读取 `.agents/skills/clarify/SKILL.md` 与绑定版本的 `core/clarify.md`，再提问或填写 `01-clarify.md`。

## 阶段与完成条件

仅用于已确认属于开发工作的新任务；咨询与轻量文档操作不激活本流程，已有开发任务始终以其绑定版本为准，本概览不能替代历史任务契约。

- 01 Clarify：目标、范围、成功判据、关键约束、未决业务问题。先读 `.agents/skills/clarify/SKILL.md` 与本规则版本中的 `clarify.md`；已有用户输入可直接整理与校验，不重复访谈。
- 02 Plan：影响范围、调用链/状态机、数据及协议兼容性、UT 和 IT 设计、风险与回滚。
- 03 Implement + UT + Docs：先遵守 `.wally/rules/` 中的项目规则，再 Red → Green → Refactor → 增量覆盖率 → Docs → 增量 CR。适用门禁未通过不得 Deploy。
- 04 Deploy：环境、基线、部署范围、生效验证、回滚。热更前保留缺陷基线。
- 05 IT：按 Plan 执行，核验逐用例结果与总体门禁，完成缺陷 A/B。
- 06 Review + Commit：先读 `.agents/skills/sop-aware-code-review/SKILL.md`（03 增量 CR 同样适用），复核变更后的证据、时间记录和遗留风险，完成外部系统/资源处置及提交准备，再按授权执行 Git。

### 阶段依赖速查（Skill / Rules / 工具与检查点）

| 阶段 | 依赖 Skill（`.agents/skills/`） | 依赖 Rules（绑定版本 / 任务快照） | 工具 / 检查点 |
|---|---|---|---|
| 01 Clarify | `clarify/SKILL.md` | `core/clarify.md`、`core/gates.md`、`core/knowledge.md` | `sop_context.py`、`create_task.py`、`date` |
| 02 Plan | — | `core/workflow.md`、`core/gates.md`、`core/knowledge.md` | `.wally/docs/INDEX.md`、`date` |
| 03 Implement + UT + Docs | `sop-aware-code-review/SKILL.md`（增量 CR） | `.wally/rules/`、`core/gates.md`、`core/knowledge.md` | `sop_context.py --checkpoint implement`、UT/覆盖率命令 |
| 04 Deploy | 可选 `wally-open-cli/SKILL.md` | `core/gates.md` | `sop_context.py --checkpoint deploy`、任务快照 `execution.json` |
| 05 IT | 可选 `wally-open-cli/SKILL.md` | `core/gates.md` | `sop_context.py --checkpoint it`、任务快照 `execution.json` |
| 06 Review + Commit | `sop-aware-code-review/SKILL.md` | `.wally/review.md`、`.wally/commit.md`、`core/gates.md` | 客户端 `token_report.py`、`git`、`date` |

新任务始终保留 01–06 六阶段。 显式标记 `readiness: pending` 的方法即使有 guide/command 也不完整，标记 BLOCKED 并按 `gaps` 向用户询问补齐，不能自动跳过；只有 ready 方法（或未带 readiness 的旧配置）按下述 command/guide 规则判断，ready 不等于执行通过。每次进入 Deploy/IT 前读取本任务 `execution.json`：对应 command 与 guide 都为空时自动跳过，不准备环境、不调用工具；使用创建任务时已生成的 SKIPPED 记录与零耗时行。配置了任一方法则按客户实际命令/指南执行，缺环境、权限、工具或执行失败均不得伪装成未配置而跳过。跳过不是通过，必须在 Review 说明未完成部署/集成验证；其他适用门禁继续执行。历史任务按自己的绑定版本恢复，不因新规则改写。

在开始 Implement、Deploy、IT 的实际操作前，分别运行 `python3 .wally/scripts/sop_context.py --checkpoint implement`、`--checkpoint deploy`、`--checkpoint it`。Clarify/Plan 未记录完成或仍为空模板，以及用户准备执行未配置方法的 Deploy/IT 时，必须先展示缺失项、拟执行操作和影响，等待用户确认后才继续。默认自动跳过未配置的 Deploy/IT 不需要确认；确认例外也不提供执行方法，仍须取得真实命令/指南，不能猜测。

检查点退出码 3 表示等待确认。在回复正文清楚展示原因与 `CONFIRM SOP <编号>`，同一决定不要再调用提问工具或另发提问卡；前端会收成一张决定卡。用户仍需在聊天中明确发送该文本，输入 Hook 才会记录确认。Agent 不得自行发送确认、修改 `.wally/local/sop-confirmations.json`、伪造产物或反复重试。拒绝、无回复、无效或过期编号均不视为确认。同任务/阶段且相关材料未变时不重复询问；分支、任务、阶段、绑定规则或相关材料变化后重新检查。缺少输入 Hook 的环境只能保留等待状态或先补齐前置材料，不能声称自动确认。

确认允许带缺项继续当前阶段，须在 overview 记录实际用户授权、缺失证据和未验证范围；不自动勾选前置阶段，不把 SKIPPED/未验证改为通过，不免除其他适用验收。质量要求由阶段检查与 Review 持续核验。普通工具操作不因 SOP 白名单或上下文错误被强制拒绝；Shell/MCP 不做全面拦截，阶段检查点由 Agent 主动调用，已有客户端权限和用户授权继续生效。

Hook 负责加载上下文，并仅对已识别业务编辑触发上述两类确认；普通 Shell、Git、date 等不做 SOP 白名单拦截。实现/部署/IT 前必须主动运行对应 `--checkpoint`，等待明确用户确认或补齐前置条件后继续。确认只允许带已披露缺项继续，不能把未验证阶段记为完成。Hook 未启用、不支持或未受信任时保留指令约束，不声称强制覆盖。已有客户端权限、用户约束与授权边界继续生效。
<!-- wally-init:entry:end -->
