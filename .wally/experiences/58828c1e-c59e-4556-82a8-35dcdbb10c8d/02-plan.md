# 02 · Plan — 原生 GET /welcome

## 实现步骤
1. 新增 `src/octop_gateway/web.py`：基于 `http.server.ThreadingHTTPServer` +
   `BaseHTTPRequestHandler` 的轻量服务；`do_GET` 中对 `self.path == "/welcome"`
   返回 200 + `Content-Type: application/json` + `{"message":"welcome"}`，其余路径 404。
2. 入口 `main()` 从环境变量读取 host/port（默认 `0.0.0.0` / `8080`），
   不硬编码内部地址；`python -m octop_gateway.web` 可启动。
3. 新增 runtime 描述文件，声明启动命令、端口/环境变量、路由清单。
4. 新增契约测试 `tests/test_experience_welcome.py`。
5. 运行契约测试与全量测试确认无回归（本阶段不执行）。

## 具体文件与命令
- 新增：`src/octop_gateway/web.py`
- 新增：`runtime.json`（启动命令 / 端口 / 路由）
- 新增：`tests/test_experience_welcome.py`
- 本地验证命令（Plan 阶段仅记录，不运行）：
  - `pytest -q tests/test_experience_welcome.py`
  - `pytest -q`
  - `ruff check src/octop_gateway/web.py tests/test_experience_welcome.py`
  - `python -m octop_gateway.web`（手动启动后 `curl -i localhost:8080/welcome`）

## 契约测试方案
- fixture：在线程中启动 `ThreadingHTTPServer(("127.0.0.1", 0), WelcomeHandler)`，
  取 `server.server_address[1]` 作为临时端口，`yield` 后 `shutdown()/server_close()`。
- 用 `urllib.request` 或 `http.client` 发起请求，断言：
  - `/welcome` → status 200、`Content-Type` 以 `application/json` 开头、
    `json.loads(body) == {"message": "welcome"}`；
  - 不发送认证头即可成功（免登录）；
  - 未知路径 → 404。
- 测试仅依赖标准库，避免引入新依赖。

## runtime.json 形状（建议）
```json
{
  "start": {
    "command": "python -m octop_gateway.web",
    "env": { "WALLY_HOST": "0.0.0.0", "WALLY_PORT": "8080" }
  },
  "port": 8080,
  "routes": [ { "method": "GET", "path": "/welcome", "auth": false } ]
}
```
说明：host/port 通过 env 注入，便于平台分配端口；`auth:false` 表达免登录契约。

## 回滚要点
- 全部变更为新增文件，未触碰现有源码/依赖 → 回滚即删除上述新增文件。
- 若 runtime.json 为已存在文件被修改，则用 `git checkout -- runtime.json` 还原。
- 回滚后确认 `pytest -q` 恢复基线通过。
