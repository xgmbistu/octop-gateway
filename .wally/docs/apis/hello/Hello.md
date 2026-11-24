# Hello

> Source: `src/octop_gateway/hello.py`
> Last-verified: 2026-11-24

---

## 描述

独立可运行服务提供的固定响应接口，用于本地验证 HTTP 服务接入与健康检查。默认仅监听回环地址，无鉴权、无持久化、无外部依赖。

## 请求

**方法 / 路径**：`GET /hello`

### 入参

无。

### 示例

```http
GET /hello HTTP/1.1
Host: 127.0.0.1:8080
```

## 响应

### 出参

| 字段 | 类型 | 说明 |
|------|------|------|
| message | string | 固定值 `hello world` |

### 示例

```json
{"message": "hello world"}
```

## 错误码

| HTTP 状态 | 含义 | 处理建议 |
|-----------|------|----------|
| 404 | 路径未注册 | 确认请求路径为 `/hello` |
| 405 | 方法不是 GET（aiohttp 默认同时允许 HEAD） | 改用 GET |

## 启动方式

`python -m octop_gateway.hello`，默认绑定 `127.0.0.1:8080`。该服务为可选入口，不影响库作为同进程内嵌组件的使用方式。

## 变更记录

| 日期 | 版本 | 变更内容 | 任务 |
|------|------|---------|------|
| 2026-11-24 | 1.0.4 | 新增 `GET /hello` | `2026-11-24_hello-world-http-api` |
