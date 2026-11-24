# 01 · Clarify — 原生 GET /welcome

## 观察到的仓库事实
- 仓库实际为 `octop-gateway`（pyproject `name = octop-gateway`，`src/octop_gateway/`），
  与注入的 `AGENTS.md`（wally-open）描述不一致；以当前仓库实际内容为准。
- 项目是 IM 网关库（asyncio + aiohttp），依赖见 `pyproject.toml`。
- **未发现任何 Web 服务入口或路由注册表**：`src/`、`examples/`、`tests/` 内
  均无 `Flask/FastAPI/aiohttp.web/HTTPServer/do_GET/@app.route` 等服务端路由代码；
  也无 `app.py`、`static/`、`tests/test_experience_welcome.py`。
- `.wally/experiences/<id>/` 目前仅有 `baseline-sha`。

## 框架 / 路由位置（结论）
- 目标框架：**Python 标准库 `http.server`**（ThreadingHTTPServer + BaseHTTPRequestHandler），
  属“原生”实现，不新增运行依赖；备选为已存在的 aiohttp.web。
- 路由挂载点：新增独立模块 `src/octop_gateway/web.py` 作为 Web 入口，
  在请求处理器中按 `self.path` 分派 `GET /welcome`。这是唯一新增的路由注册处。

## 改动范围
- 新增 `src/octop_gateway/web.py`（HTTP 服务 + /welcome 处理）。
- 新增 `tests/test_experience_welcome.py`（契约测试，平台侧提供/验收）。
- 新增/更新 runtime 描述（启动命令、端口/环境变量、声明路由）。
- **不修改**任何现有业务源码与依赖；无鉴权改动。

## 验收条件
1. `GET /welcome` → 200，`Content-Type: application/json`，响应体
   `{"message":"welcome"}`（精确 JSON，无多余包装）。
2. 免登录：无需任何认证头/会话即可访问。
3. 其他路径不回归：未匹配路径返回 404，不暴露新路由以外的行为。
4. Host/Port 走配置或环境变量，不硬编码任何内部地址。
5. 契约测试 `tests/test_experience_welcome.py` 通过（本阶段不运行）。

## 结论
事实已澄清，契约与改动边界明确，**可进入 02 Plan**。
