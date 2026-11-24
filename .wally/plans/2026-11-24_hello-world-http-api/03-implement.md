# 03. Implement + UT + Docs

## 项目规则

实际读取：`.wally/rules/README.md`（目录内唯一文件，明确其本身不是编码规范）、`AGENTS.md`（§1 协作原则、§12 Branching & release、§13 Communication 与 SOP 入口）、`.agents/skills/sop-aware-code-review/SKILL.md` 及 `references/sop.md`。

结论：`.wally/rules/` 无额外项目规则；Core 门禁生效。本任务落实方式：最小改动、不改公共 API/数据模型、测试先行、只做与任务相关的文档最小修订、不提交。

## 实际改动与 Plan 差异

与 02 Plan 一致，无范围偏差：

- 新增 `src/octop_gateway/hello.py`：`HOST=127.0.0.1`、`PORT=8080`、`HELLO_MESSAGE`、`hello()`、`create_app()`、`main()`。
- 新增 `tests/test_hello.py`（5 个 UT）。
- 新增 `tests/test_hello_integration.py`（1 个 IT）。
- 新增 `.wally/docs/apis/hello/Hello.md`。
- 最小修订 `.wally/docs/apis/index.md`、`.wally/docs/overview/system-architecture.md`。
- 未新增依赖、未改 `pyproject.toml`、未改 `octop_gateway.api` 导出。

## Red → Green → Refactor

环境：Python 3.12.11、`aiohttp` 3.14.5、`pytest` 9.2.0、`pytest-asyncio` 1.5.0、`pytest-cov` 7.1.0；工作树 HEAD `0c5327a`（含未提交改动）；命令均带 `PYTHONPATH=src`（本机未安装包）。

- **Red**：先写 `tests/test_hello.py`，再以 stub `create_app()`（未注册 `/hello`）运行 `PYTHONPATH=src python3.12 -m pytest tests/test_hello.py -q`。结果 `3 failed, 1 passed`：UT-01 `assert 404 == 200`、UT-03 `assert 404 == 405`、UT-04 `assert False`（无 GET 路由）——均为预期断言失败。
- **Green**：实现路由与 handler 后同组运行。首次出现 `ClientConnectionError: Connection closed`，定位为测试在 `TestClient` 上下文外读取响应体，修正测试断言位置后复跑：`5 passed in 0.12s`。
- **Refactor**：无需重构；模块保持最小实现。
- **Smoke**：`PYTHONPATH=src python3.12 -m octop_gateway.hello` 真实进程启动，`urllib` 请求 `http://127.0.0.1:8080/hello` → `200`、`application/json; charset=utf-8`、`{"message": "hello world"}`；进程随后 terminate。

## UT 与增量覆盖率

- 命令：`PYTHONPATH=src python3.12 -m pytest --cov=octop_gateway.hello --cov-branch --cov-report=term-missing tests/test_hello.py -q` → `5 passed`。
- 增量结果：`hello.py` 15 stmts / 14 covered（行覆盖 93.3%），2 branch / 1 partial（分支覆盖 50%，组合覆盖 88%），唯一未覆盖行 30 为 `if __name__ == "__main__"` 下的 `main()` 调用，导入式测试不可达，记 N/A。
- 阈值对照：Profile 普通业务行 80% / 分支 70%；行覆盖达标。分支覆盖 50% 未达 70%，原因仅为 `__main__` 守卫这一不可达分支；已通过独立进程 smoke 实际启动验证，但未把 smoke 计作覆盖率。如实记录为「分支阈值未完全达标，理由已记录」。
- Unicode：响应为固定 ASCII 字面量，无用户输入/中文序列化路径，UT-01 已覆盖 JSON 解析，Unicode 用例 N/A。
- 回归：`PYTHONPATH=src pytest tests/test_*.py -q` → `278 passed`（顶层测试文件，含新增 UT）。全量 `pytest -m "not integration"` 在本机无法收集：`telegram`、`discord` 等平台 SDK 未安装，属环境缺口，与本次改动无关。

## 缺陷回归（适用时）

不适用：非 Bug / 性能任务，无 A/B 基线要求。

## Docs

- 新增 `.wally/docs/apis/hello/Hello.md`：按 `_template.md` 记录方法/路径、出参、错误语义、启动方式与变更记录。
- 更新 `.wally/docs/apis/index.md`：修订「不暴露 HTTP 服务」为「库本身不暴露，另有可选服务」，新增模块清单、接口清单与入口/验证行。
- 更新 `.wally/docs/overview/system-architecture.md`：修订 `:54` 陈述、`source_paths` 增补新模块、`Last-verified` 改为当前工作树、§6 增补影响定位行；保留 `origin: human` / `status: verified` 与既有正文，未重写人工维护页。
- 未更新 `README.md` / `README_CN.md`：检索确认无冲突陈述。
- 缺口：`.wally/docs/INDEX.md` 不存在，按 Profile 路径回查权威页，已记录。

## 增量 CR

审查范围：工作树 diff（HEAD `0c5327a` + 未提交改动），新增 `hello.py`、两份测试、`Hello.md` 与两处文档最小修订；依据 `AGENTS.md`、`.wally/rules/README.md`、`.agents/skills/sop-aware-code-review/SKILL.md` 与 `references/sop.md`。

发现：无代码缺陷。核对点如下：
- 路由只注册 `GET /hello`，404/405 由 aiohttp 默认语义提供，与文档一致。
- 未引入新依赖，未触碰 `ChannelManager` / `parse_inbound` / `_send_*` / 限流路径，无重复占用额度风险。
- `main()` 仅绑定回环地址，不对外暴露；无鉴权符合澄清结论。
- 文档陈述与实现一致；verified 页仅做事实性最小修订。

未解决 / 未验证：
- `make lint`（`ruff check src tests`）与 `ruff format --check src tests` 均通过（88 files already formatted）。
- `make typecheck`（`mypy src`）失败于 4 个既有错误：`channels/mqtt.py` 缺 `paho`、`channels/discord.py` 缺 `discord` 及其 `unused-ignore`；均与本次新增 `hello.py` 无关，本机缺可选 SDK。
- 全量单测与 IT 受平台 SDK 缺失影响无法完整收集，见上文与 05 IT 记录。

CR 结论：可合并（代码层面）；SOP 证据存在环境性未验证项，不记为通过。

## 完成结论

- TDD：通过（Red 为预期断言失败，Green 同组断言全绿）。
- 增量覆盖率：行覆盖达标；分支阈值因 `__main__` 守卫未完全达标，理由与 smoke 证据已记录。
- Docs：已更新权威文档，索引缺失缺口已记录。
- 增量 CR：无代码发现；环境性未验证项如实记录。
- Deploy / IT： Deploy 因 `readiness: pending` 标记 BLOCKED；IT 见后续阶段。

## 知识库证据

- 读取：`.wally/docs/INDEX.md`（缺失）、`overview/system-architecture.md`、`apis/index.md`、`apis/_template.md`、`src/octop_gateway/api/__init__.py`、`tests/test_api_contracts.py`、`pyproject.toml`、`Makefile`、`.wally/config.json`。
- 源码核验：`aiohttp` 在仓库中原仅作客户端；新增服务端实现后，相关文档陈述已同步修订。
- 受影响文档：`apis/hello/Hello.md`（新增）、`apis/index.md`、`overview/system-architecture.md`（已更新并复核 diff）；`README*` 无需更新。
- 校验：文档 diff 已对照实现复查，链接与源码锚点一致；Docs 在最终 Review 复查前不标最终通过。
