# 02 Plan — 原生 GET /welcome 实现方案

> 前置：本仓库无现成 Web 服务（见 01-clarify.md），采用 aiohttp.web 新增最小服务入口。

## 实现步骤
1. 新增 `src/octop_gateway/web.py`：
   - `async def _welcome(request): return web.json_response({"message": "welcome"})`
   - `def create_app() -> web.Application`：`app = web.Application(); app.router.add_get("/welcome", _welcome); return app`
   - `def run_app()`：用 `web.AppRunner` + `web.TCPSite`，host/port 取自配置/环境变量
     （默认 `127.0.0.1:8080`），**不硬编码任何内部平台地址**。
   - `if __name__ == "__main__": run_app()`，提供 `python -m octop_gateway.web` 启动方式。
2. 可选：在 `src/octop_gateway/__init__.py` 增加 `from .web import create_app` 导出，
   保持契约测试导入路径稳定。
3. 新增 `tests/test_experience_welcome.py`（见下）。不改任何既有模块。

## 契约测试方案（tests/test_experience_welcome.py）
- 使用 `aiohttp.test_utils.TestServer(create_app())` + `TestClient`，用 `asyncio.run(...)` 驱动，
  **不引入 pytest-aiohttp 等新依赖**；亦可优先用现成的 `aiohttp_client` fixture（若环境已装）。
- 断言：
  1. `GET /welcome` → `status == 200`
  2. `Content-Type` 以 `application/json` 开头
  3. `await resp.json() == {"message": "welcome"}`
  4. 不附带任何鉴权头即可通过（免登录）
  5. 附带 `POST /welcome` → 405（aiohttp 原生行为，证明是原生路由）
- 验证命令：`uv run pytest tests/test_experience_welcome.py -q`
- 手动冒烟：`python -m octop_gateway.web` 后 `curl -i http://127.0.0.1:8080/welcome`

## runtime.json 形状（建议；本仓库当前不存在该文件，以平台 schema 为准）
```json
{
  "name": "octop-gateway-welcome",
  "entrypoint": "octop_gateway.web:create_app",
  "command": "python -m octop_gateway.web",
  "host": "127.0.0.1",
  "port": 8080,
  "healthcheck": { "method": "GET", "path": "/welcome", "expect_status": 200 }
}
```

## 回滚要点
- 纯新增改动：删除 `web.py`、删除 `tests/test_experience_welcome.py`、
  撤销 `__init__.py` 的导出即可完全回滚。
- 无数据库/迁移/外部配置变更；不影响 channels、manager 及既有测试。

## 边界
- 本阶段（Clarify+Plan）不写源码、不跑测试、不启服务/探活；实施与验证留待后续步骤。
