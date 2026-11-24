# 03 · Implement + UT + Docs — 原生 GET /welcome

## 结论
已完成实现：新增原生 `GET /welcome` 路由，返回 `200` + `application/json` +
`{"message":"welcome"}`（免登录）。契约测试 3 项全部通过，`python -m
octop_gateway.web` 启动后 `curl` 实测返回符合契约。

## 改动文件
| 文件 | 类型 | 说明 |
| --- | --- | --- |
| `src/octop_gateway/web.py` | 新增 | 基于标准库 `http.server.ThreadingHTTPServer` + `BaseHTTPRequestHandler` 的 Web 入口；`do_GET` 分派 `/welcome` → 200 JSON，其余路径 404；`main()` 支持 `--host/--port` 与 `WALLY_HOST/WALLY_PORT`，默认 `0.0.0.0:8080` |
| `tests/test_experience_welcome.py` | 新增 | 契约测试：200 + JSON 精确体、免登录、未知路径 404；fixture 在线程中启动临时端口服务 |
| `README.md` | 修改 | 新增 `## HTTP API` 章节，说明启动方式、`GET /welcome` 的响应与示例；文档目录加入链接 |
| `.wally/experiences/.../runtime.json` | 新增 | `test` / `serve` 命令声明，`serve` 含 `{port}` 占位符 |
| `.wally/experiences/.../03-implement.md` | 新增 | 本阶段文档 |

说明：未修改任何现有业务源码与依赖，未引入新的运行依赖（仅用 Python 标准库）。
`http.server` 为“原生”实现，契合“原生路由”要求。

## 测试命令与结果
命令（沙箱内使用 `/workspace/.venv` 虚拟环境）：
```
python -m pytest -q tests/test_experience_welcome.py
```
实际执行：`.venv/bin/python -m pytest -q tests/test_experience_welcome.py`

结果：
```
...                                                                      [100%]
3 passed, 1 warning in 1.55s
```
- 1 warning 为 `Unknown config option: asyncio_mode`（pytest-asyncio 版本与仓库
  pytest 配置兼容提示），与本契约无关，测试全部通过。

服务启动验证（使用 runtime.json 中 `serve` 等价命令）：
```
python -m octop_gateway.web --host 127.0.0.1 --port 18099
curl -i http://127.0.0.1:18099/welcome
```
返回：
```
HTTP/1.0 200 OK
Content-Type: application/json
Content-Length: 22

{"message": "welcome"}
```

## runtime.json
```json
{
  "test": ["python", "-m", "pytest", "-q", "tests/test_experience_welcome.py"],
  "serve": ["python", "-m", "octop_gateway.web", "--host", "0.0.0.0", "--port", "{port}"]
}
```
- `serve` 监听 `0.0.0.0`，端口由平台以 `{port}` 注入。
- `main()` 解析 `--host`/`--port`，因此注入端口会真实生效（已本地 smoke 验证）。

## 契约覆盖
- `GET /welcome` → 200、`Content-Type: application/json`、精确 JSON 体。
- 免登录：不携带任何认证头即可成功。
- 未知路径 → 404，无额外行为暴露。

## 环境
- 按项目配置在 `/workspace/.venv` 创建虚拟环境，安装项目（editable）与测试依赖。
- 契约测试仅依赖标准库 + `pytest`，无网络访问。
