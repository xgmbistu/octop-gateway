# 01 Clarify — 原生 GET /welcome

## 目标与验收条件
- 在现有 Web 服务中新增**原生** `GET /welcome`，免登录。
- 响应：`200` + `Content-Type: application/json` + body `{"message":"welcome"}`。
- 既有行为不变；契约测试文件固定为 `tests/test_experience_welcome.py`。
- 本阶段不改源码、不跑 pytest、不启动服务（按要求）。

## 仓库事实核对（重要偏差）
- 平台给的事实描述的是 `wally_open` / `app.py` / `src/wally_open/`，但当前仓库实际是
  **`octop-gateway`**（Python 3.12+，`pyproject.toml` 中 `aiohttp>=3.9`）。
- 实际探查结果：仓库内**没有** `app.py`，**没有**任何 Web/HTTP 服务端与路由注册
  （无 FastAPI/Flask/Starlette/`web.Application`/`add_route`/`app.get` 等）。
- 全部 `aiohttp` 用法均为 `ClientSession` 客户端调用（channels 内部），不是服务端。
- 结论：题面“现有 Web 服务”在本仓库不成立；需**新增一个最小 Web 服务入口**来承载该原生路由。

## 框架选择
- 选 **aiohttp.web**：已是运行依赖，无需新增依赖；符合 AGENTS.md“新增运行依赖先说明理由”。
- 不引入 FastAPI/Flask/uvicorn，避免改变依赖面。

## 路由位置与改动范围
- 新增 `src/octop_gateway/web.py`：暴露 `create_app() -> aiohttp.web.Application`，
  内部注册 `GET /welcome`；提供可运行的 `run_app()`（host/port 由配置项或环境变量提供）。
- 可选：在 `src/octop_gateway/__init__.py` 导出 `create_app`，便于契约测试稳定导入。
- 新增 `tests/test_experience_welcome.py`（契约测试，平台验收用）。
- **不改** channels / manager / 任何既有业务逻辑；不硬编码内部地址（AGENTS.md 约束）。

## 关键假设（需在后续步骤确认）
- 契约测试通过导入 `create_app()` 并用 `aiohttp.test_utils` 客户端断言，而非猜测固定端口。
- 平台未提供 `runtime.json` 现状文件；Plan 中给出建议形状，最终以平台实际 schema 为准。

## 结论
- 偏差已显式记录且不影响目标可达性：**可以进入 Plan**，按上述最小新增方案实施。
