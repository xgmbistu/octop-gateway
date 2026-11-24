# 03 Implement — 原生 GET /welcome

## 目标
在仓库内以 aiohttp.web 提供原生 `GET /welcome`，免登录返回
`200` + `application/json` + `{"message":"welcome"}`。

## 改动文件
| 文件 | 说明 |
| --- | --- |
| `src/octop_gateway/web.py` | 新增。`_welcome()` 返回 `web.json_response({"message": "welcome"})`；`create_app()` 注册 `GET /welcome`；`run_app()` 通过 `--host`/`--port` 启动（默认 `0.0.0.0:8080`），支持 `python -m octop_gateway.web`。未硬编码任何内部地址。 |
| `tests/test_experience_welcome.py` | 新增。契约测试：免鉴权 GET → 200 / JSON / 精确 body；POST → 405（原生 GET 路由）。用 `asyncio.run` 驱动 aiohttp test client，不引入异步 pytest 插件。 |
| `README.md` | 新增 “Web service” 章节，说明启动方式与 `GET /welcome` 请求/响应示例及 405 行为。 |
| `.wally/experiences/0c298310-98be-4457-812c-f48067f5dc4b/runtime.json` | 新增，按平台 schema：`test`/`serve` 命令数组，`serve` 含 `0.0.0.0` 与 `{port}` 占位符。 |
| `.wally/experiences/0c298310-98be-4457-812c-f48067f5dc4b/03-implement.md` | 本文件。 |

既有 channels / manager / 业务逻辑均未改动。无数据库、迁移或外部配置变更。

## 依赖与环境
按沙箱要求创建 `/workspace/.venv`，安装 `aiohttp`、`pytest`、`pydantic`
（以及项目 editable 安装 `--no-deps`），依赖均在沙箱内，未使用宿主机环境。

## 测试命令与结果
命令：
```
cd /workspace && python -m pytest -q tests/test_experience_welcome.py
```
结果（实际执行，使用 `.venv/bin/python`）：
```
..                                                                       [100%]
2 passed, 1 warning in 0.06s
```
仅运行契约测试文件，未执行全量 pytest。warning 为 pyproject 中
`asyncio_mode` 未被异步插件识别，属无害提示（测试以 `asyncio.run` 驱动）。

## 启动冒烟（额外验证）
```
python -m octop_gateway.web --host 127.0.0.1 --port 18080
```
- `GET /welcome` → `HTTP 200`，body `{"message": "welcome"}`
- `POST /welcome` → `HTTP 405 Method Not Allowed`

## runtime.json
```json
{
  "test": ["python3", "-m", "pytest", "-q", "tests/test_experience_welcome.py"],
  "serve": ["python3", "-m", "octop_gateway.web", "--host", "0.0.0.0", "--port", "{port}"]
}
```

## 状态
全部强制交付物完成，交付齐全后停止。
