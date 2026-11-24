# 接口文档总索引

> 每个对外接口 / 契约对应一篇 `<module>/<ActionName>.md`。
> 新增 / 修改接口时同步更新本索引并复核契约文档与源码一致。

本仓库是 Python 库（`octop-gateway`），库本身**不暴露 HTTP 服务，也没有数据库**。
另提供可选的独立运行服务入口（`src/octop_gateway/hello.py`，`python -m octop_gateway.hello`），仅用于本地验证，不接入库的公共 API 面。
库的对外契约即 Python 公共 API 与 Pydantic 数据模型；实际入口与数据边界为
`ChannelManager`、各平台 `BaseChannel` 适配器、`MessageProcessor` 以及
`InboundMessage` / `MessageEvent` / `ContentPart` 模型体系。

---

## 命名约定

- 路径：`.wally/docs/apis/<module>/<ActionName>.md`
- 文件名 = 接口名（PascalCase 或项目既有风格）
- 每篇至少包含：描述、入参 / 请求、出参 / 响应、错误语义、数据模型、示例、变更记录
- `_template.md` 仅作模板，不计为接口文档

---

## 模块清单

| 模块 | 路径 | 接口数 |
|------|------|-------|
| core | `apis/core/` | 4 |
| hello | `apis/hello/` | 1 |

---

## 接口清单

| 接口 | 模块 | 源码入口 | 文档 |
|------|------|----------|------|
| ChannelManager | core | `src/octop_gateway/manager.py` | [`core/ChannelContract.md`](core/ChannelContract.md) |
| BaseChannel | core | `src/octop_gateway/channel.py` | [`core/ChannelContract.md`](core/ChannelContract.md) |
| MessageProcessor | core | `src/octop_gateway/channel.py:53` | [`core/ChannelContract.md`](core/ChannelContract.md) |
| 数据模型 / 内容类型 | core | `src/octop_gateway/models.py` | [`core/ChannelContract.md`](core/ChannelContract.md) |
| Hello（`GET /hello`） | hello | `src/octop_gateway/hello.py` | [`hello/Hello.md`](hello/Hello.md) |

---

## 入口与验证对照

| 角色 | 入口 | 说明 |
|------|------|------|
| 实现 | `src/octop_gateway/api/__init__.py` | 稳定公共 API 面，统一转出契约符号 |
| 文档 | `.wally/docs/apis/core/ChannelContract.md` | 入参 / 出参 / 错误语义 / 数据模型 |
| 验证 | `tests/test_api_contracts.py` | 校验导出、事件类型、模型字段与工厂契约 |
| 可选服务实现 | `src/octop_gateway/hello.py` | 独立可运行 hello HTTP 服务，不改动公共 API 面 |
| 可选服务验证 | `tests/test_hello.py` | 校验 hello 路由、JSON 响应与启动绑定 |

---

## 维护约定

- 变更 `manager.py` / `channel.py` / `models.py` 的公共签名时，同步更新
  `core/ChannelContract.md`、`src/octop_gateway/api/__init__.py` 的 `__all__`
  以及 `tests/test_api_contracts.py`。
- 契约文档只描述仓库真实存在的符号；禁止把未实现能力写成已支持。
