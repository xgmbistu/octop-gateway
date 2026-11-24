# 02. Plan

## 方案与改动范围

关联 Clarify 判据：`GET /hello` → 200 + JSON `{"message": "hello world"}`；独立可运行；无鉴权/持久化/外部依赖。

**设计决定**：新增独立模块 `src/octop_gateway/hello.py`，基于已声明的运行时依赖 `aiohttp.web`；提供 `create_app()` 供测试与宿主复用，提供 `main()` 作为启动入口。启动方式 `python -m octop_gateway.hello`，默认绑定 `127.0.0.1:8080`（仅本地）。不新增 `[project.scripts]`、不改 `__all__`、不改 pyproject 依赖。

| 文件 | 动作 | 说明 |
|------|------|------|
| `src/octop_gateway/hello.py` | 新增 | `create_app()` 注册 `GET /hello`；`hello()` 返回 `web.json_response({"message": "hello world"})`；`main()` 调用 `web.run_app(..., host="127.0.0.1", port=8080)` |
| `tests/test_hello.py` | 新增 | 正向 / 逆向 / 边界 UT（见下） |
| `tests/test_hello_integration.py` | 新增 | `@pytest.mark.integration`，用 `aiohttp.test_utils` 在回环地址起停服务并请求 `/hello`，不依赖平台凭证 |
| `.wally/docs/apis/hello/Hello.md` | 新增 | 按 `_template.md` 记录方法/路径、出参、错误语义、示例、变更记录 |
| `.wally/docs/apis/index.md` | 最小修订 | 修订「不暴露 HTTP 服务」为「库本身不暴露；另提供可选独立 hello 服务」，并新增 hello 模块与接口清单行 |
| `.wally/docs/overview/system-architecture.md` | 最小修订 | 修订 `:54`「没有自带 HTTP 服务」为「库本身不是常驻服务；另有可选独立 hello 服务入口」，frontmatter `source_paths` 增补新模块，§6 增补影响定位行；保留 `origin: human` / `status: verified` 与既有正文 |

**风险等级：中**。理由：改变仓库能力边界陈述并触及人工维护的 verified 文档，但不改公共 Python API、数据结构、平台协议或现有通道行为；改动均可逆、可回滚。

## 调用链与兼容性

- 请求链：`web.run_app` → `create_app()` → `GET /hello` → `hello()` → `web.json_response` → 200 JSON。未知路径由 aiohttp 默认返回 404；已注册路径的非 GET 方法由 aiohttp 返回 405。
- 状态机 / fallback / retry / 多终态出口：无状态、无外部依赖，不涉及重试与副作用挂点；终态仅 200/404/405。
- 兼容性：既有 `octop_gateway.api` 导出与 `ChannelManager` 调用链不变；新模块按需导入，不影响库加载。
- 回滚：删除上述新增文件并还原两处文档的最小修订；无数据迁移、无配置变更。

## UT 设计

测试位置 `tests/test_hello.py`，使用 `aiohttp.test_utils.TestServer(create_app())` + `TestClient`。

| 编号 | 输入状态 | 预期断言 | 覆盖类型 |
|------|----------|----------|----------|
| UT-01 | `GET /hello` | 200；`Content-Type` 含 `application/json`；`await resp.json() == {"message": "hello world"}` | 正向 |
| UT-02 | `GET /not-found` | 404 | 逆向 |
| UT-03 | `POST /hello` | 405 | 边界 |
| UT-04 | 直接调用 `create_app()` | 返回 `web.Application` 且路由中含 `/hello` 的 GET | 契约 |

**Red → Green**：先写入全部测试；再以最小 stub（`create_app()` 返回未注册 `/hello` 的 app）使 UT-01 产生**预期断言失败**（200 未满足、返回 404），记录 Red 输出；随后实现正确 handler 使同组断言通过（Green）；如无需重构则说明。禁止把导入失败或语法错误当作 Red。

**Unicode / JSON 用例**：响应体为固定 ASCII 字面量，无用户输入、无中文数据参与序列化路径，Unicode 用例判为 N/A 并记录依据；UT-01 已覆盖 JSON 解析断言。

**覆盖率**：仓库未配置增量覆盖率命令；实现后以 `pytest --cov=octop_gateway.hello --cov-report=term-missing tests/test_hello.py` 生成局部报告并记录，按 Profile 普通业务行 80% / 分支 70% 参照核验，未达阈值如实记录，不以全量覆盖率替代。

## IT 设计（六步适用）

- 用例 IT-01：`tests/test_hello_integration.py`（`@pytest.mark.integration`），`TestServer` 在回环地址起停，`TestClient.get("/hello")` 断言 200 与 JSON；执行入口 `make test-integration`（`.wally/config.json` 的 `it.command`）。
- 环境：本机回环，无外部凭证；前置数据无。
- 判定：IT-01 通过为该用例通过；仓库既有平台集成用例依赖 `.env` 凭证，缺凭证时按其 `skipif` 规则处理并如实报告，不以退出码替代业务结果。
- 缺陷 A/B：不适用（非 Bug / 性能任务）。

## 风险与完成结论

- 关键决定：独立模块 + `python -m` 入口，不引入 console script、不改公共 API、不改依赖。
- 未覆盖边界：公网暴露、并发压测、端口冲突自动处理、鉴权——均不在本任务范围。
- 授权需求：Branch 已由用户确认；Deploy 无可执行环境（`readiness: pending`）将标记 BLOCKED；Commit/Push 需用户另行授权，本计划不执行。
- 兜底：文档最小修订若与人工维护意图冲突，回退文档改动并保留代码；不擅自改写 verified 页正文。
- 适用测试已在实现前设计完成；进入实现前须运行 `sop_context.py --checkpoint implement`。

## 知识库证据

按绑定版本 `core/knowledge.md` 执行，实际读取路径与结论：

- `.wally/docs/INDEX.md`：缺失，记录缺口；按 Profile 文档路径回查。
- `.wally/docs/overview/system-architecture.md`：已读，`status: verified` / `origin: human`，`:54` 陈述冲突；`source_paths` 与 §6 影响定位表需增补新模块。不重写正文，仅最小修订。
- `.wally/docs/apis/index.md`：已读，`:6` 陈述冲突；模块清单与接口清单需增补 hello 行。
- `.wally/docs/apis/_template.md`：已读，作为 `Hello.md` 结构依据。
- `pyproject.toml`、`Makefile`、`.wally/config.json`：已读，确认依赖、UT/lint/typecheck 命令、IT 与 Deploy 执行方法状态。
- 预计受影响文档：新增 `.wally/docs/apis/hello/Hello.md`；更新 `.wally/docs/apis/index.md`、`.wally/docs/overview/system-architecture.md`。`README.md` / `README_CN.md` 经检索无冲突陈述，不更新。
- 校验方式：实现完成后对照任务 diff 复查上述路径、链接与源码锚点；Docs 未验证前不标通过。
