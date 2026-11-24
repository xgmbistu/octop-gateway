# 01. Clarify

## 需求卡片

**一句话目标**：在 `octop-gateway` 仓库中新增一个独立可运行的 HTTP 服务，提供 `GET /hello` 返回 `{"message": "hello world"}`。
**核心用户**：需要在本仓库验证 HTTP 服务接入 / 健康检查的开发者。
**做什么**：
- 新增可本地启动的 aiohttp 服务入口。
- 提供 `GET /hello`，HTTP 200，JSON 响应 `{"message": "hello world"}`。
- 补充对应 UT 与接口文档。
**不做什么**：不接入现有 `ChannelManager` 通道体系，不改公共 Python API 契约，不加鉴权、持久化、配置化或外部依赖，不部署到任何环境。
**成功标准**：本地启动服务后 `GET /hello` 返回约定 JSON；相关 UT 通过；仓库质量门禁（`make all`）不被破坏。

## 目标与成功判据

- 可验证目标：启动服务后请求 `GET /hello` 得到 `200` 与 JSON `{"message": "hello world"}`；未知路径返回 `404`；对 `/hello` 的非 GET 方法返回 `405`。
- 成功指标：新增 UT 全绿；`make test` / `make lint` / `make typecheck` 通过；接口文档与架构文档不再与实现冲突。

## 范围、约束与依赖

- 背景：仓库定位为同进程内嵌的多平台 IM 通道桥接库（`.wally/docs/overview/system-architecture.md:54`），架构文档与接口索引均明确「没有/不暴露 HTTP 服务」（`system-architecture.md:54`、`.wally/docs/apis/index.md:6`）。本任务是对仓库能力边界的显式扩展。
- 约束：仅本地运行，默认绑定 `127.0.0.1:8080`，不对公网暴露；无鉴权、无持久化、无外部服务依赖。
- 依赖：`aiohttp>=3.9` 已是 `pyproject.toml` 运行时依赖，无需新增依赖；测试用 `aiohttp.test_utils` 与 `pytest-asyncio`（dev 依赖，`asyncio_mode=auto`）。
- 不改动：`src/octop_gateway/api/__init__.py` 公共 API 面、`ChannelManager`、各适配器、数据模型。

## 问题与决策

| 问题 | 明确结论 | 决策人 |
|------|----------|--------|
| 任务分支 | 新建 `feature/hello-world-http-api`（基线 `main`，因仓库无 `develop`） | 用户 |
| 接口定位 | 独立可运行服务（非库内 handler、非 examples demo、非新通道） | 用户 |
| 路径与返回 | `GET /hello` → JSON `{"message": "hello world"}` | 用户 |
| 鉴权 / 外部依赖 | 无鉴权、无持久化、无外部服务依赖（合理默认，未被用户否定） | 任务假设 |
| 文件结构与启动方式 | 留待 02 Plan 提出方案并获用户确认 | 待定 |

## 风险点

| 风险 | 严重度 | 缓解 / 兜底 |
|------|--------|-------------|
| 项目定位从「纯库」扩展为「库 + 可选服务」，两处既有文档陈述变为过期 | 中 | 在 02 Plan 明确提出最小修订方案并获用户确认；仅修订冲突陈述，不重写人工维护页 |
| 新增运行依赖 | 低 | `aiohttp>=3.9` 已是 `pyproject.toml` 运行时依赖，无需新增依赖 |
| 端口占用 / 仅本机可访问 | 低 | 默认绑定 `127.0.0.1:8080`，仅本地验证，不对公网暴露 |
| Deploy / IT 阶段无法真实执行 | 中 | `deploy.readiness=pending`（无环境/回滚/凭证），按门禁标记 BLOCKED 并向用户说明；`it.command=make test-integration` 依赖平台凭证，缺凭证时如实报告，不伪装通过 |

## 完成结论

目标、范围、成功判据与关键决策均已明确；剩余设计取舍转入 02 Plan，由用户确认后再实施。

## 知识库证据

按绑定版本 `core/knowledge.md` 执行，实际读取记录：

- `.wally/docs/INDEX.md`：缺失（记录缺口）。按 Profile 的文档路径回查以下权威页。
- `.wally/docs/overview/system-architecture.md`：已读正文与 frontmatter（`origin: human` / `status: verified`），确认「没有自带 HTTP 服务」陈述及模块职责 / 变更影响表。
- `.wally/docs/apis/index.md`：已读，确认「不暴露 HTTP 服务」陈述、接口清单与命名约定。
- `.wally/docs/apis/_template.md`：已读，作为新增接口文档结构依据。
- `src/octop_gateway/api/__init__.py`、`tests/test_api_contracts.py`：已读，确认公共 API 契约面与本任务不冲突。
- 源码核验：`src/**/*.py` 中 `aiohttp` 仅作 HTTP 客户端使用，无 `web.Application` / `add_get` / 服务端路由实现。
- 受影响文档（预计）：`.wally/docs/apis/index.md`、`.wally/docs/overview/system-architecture.md`，以及新增 `.wally/docs/apis/hello/Hello.md`。
- 缺口：`.wally/docs/INDEX.md` 不存在；`deploy` 执行方法未就绪。均如实记录，不伪造通过。
