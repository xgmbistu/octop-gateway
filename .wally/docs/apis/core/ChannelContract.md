# ChannelContract / 网关核心接口与数据契约

> Source: `src/octop_gateway/manager.py`, `src/octop_gateway/channel.py`, `src/octop_gateway/models.py`
> 稳定公共入口：`src/octop_gateway/api/__init__.py`
> Last-verified: 2026-11-24

---

## 描述

octop-gateway 是纯 Python 异步库，不提供 HTTP 或数据库接口。对外契约由
**消息处理管线**构成：宿主提供一个 `MessageProcessor`，`ChannelManager` 编排多个
`BaseChannel`，把各平台原生消息归一化为 `InboundMessage`，再把处理器产出的
`MessageEvent` 投递回对应会话。数据边界为 `InboundMessage` / `MessageEvent` /
`ContentPart` 三类 Pydantic 模型及 `ChannelSubject` 路由类型。

审查范围即公共 API 面（`octop_gateway.api`）与上述模型，对照源码实现核验。

---

## 入口 / 接口清单

| 接口 | 类型 | 源码 | 职责 |
|------|------|------|------|
| `ChannelManager` | 类 | `manager.py:66` | 编排通道、队列、会话锁、主动推送 |
| `ChannelManager.add_channel(...)` | 异步方法 | `manager.py:369` | 注册通道，返回 `channel_id` |
| `ChannelManager.push_text(channel_id, subject, text)` | 异步方法 | `manager.py:317` | 向指定会话主动推送文本 |
| `ChannelManager.push_content(channel_id, subject, parts)` | 异步方法 | `manager.py:329` | 主动推送富内容 `list[ContentPart]` |
| `ChannelManager.run_in_session(channel_id, session_key, operation)` | 异步方法 | `manager.py:341` | 在会话锁内执行带外操作 |
| `BaseChannel` | 抽象类 | `channel.py` | 各平台适配器必须实现的契约 |
| `MessageProcessor` | 类型别名 | `channel.py:53` | `Callable[[InboundMessage], AsyncIterator[MessageEvent]]` |
| `ChannelConfig.from_dict(data)` | 类方法 | `channel.py:96` | 由字典构造平台配置（别名映射、忽略未知键） |
| `InboundMessage` / `MessageEvent` / `ContentPart` | 数据模型 | `models.py` | 归一化消息与事件载荷 |

各平台便捷注册入口：`add_feishu_channel` / `add_wecom_channel` / `add_qq_channel` /
`add_dingtalk_channel` / `add_weixin_channel` / `add_yuanbao_channel` /
`add_xiaoyi_channel` / `add_mqtt_channel` / `add_telegram_channel` /
`add_discord_channel`（`manager.py:844` 起）。运行时扩展入口：
`register_channel_kind(kind, channel_cls, *, plugin_id)` /
`unregister_channel_kind(kind, *, plugin_id)` / `registered_channel_kinds()`
（`channels/__init__.py:132` 起）。

---

## 请求

无 HTTP 方法 / 路径；以函数调用作为请求边界。

### `ChannelManager(processor=...)` 入参

| 字段 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `channels` | `dict[str, BaseChannel] \| None` | 否 | `None` | 旧式：直接传入通道实例 |
| `workers_per_channel` | `int` | 否 | `4` | 每通道 worker 数 |
| `queue_maxsize` | `int` | 否 | `1000` | 每通道队列上限 |
| `media_backend` | `MediaBackend \| None` | 否 | `None` | 媒体后端，默认 `FileSystemMediaBackend` |
| `constraints` | `dict[str, Any] \| None` | 否 | `None` | 限流 / 超时 / typing 约束 |
| `processor` | `MessageProcessor \| None` | 否 | `None` | 默认消息处理器 |
| `on_pre_lock` | `PreLockHandler \| None` | 否 | `None` | 取会话锁前钩子（用于 `/stop` 抢占） |
| `control_message_predicate` / `interrupt_message_predicate` | `MessagePredicate \| None` | 否 | `None` | 控制 / 抢占消息判定 |

### `add_channel` 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `channel_type_or_instance` | `str \| BaseChannel \| None` | 否 | 通道种类名或实例 |
| `config` | `dict[str, Any] \| Any \| None` | 否 | 平台配置字典或 Config 对象 |
| `channel_type` | `str \| None` | 否 | 关键字参数形式的通道种类 |
| `tenant_id` | `str \| None` | 否 | 多租户标识 |
| `processor` | `MessageProcessor \| None` | 否 | 覆盖默认处理器 |
| `channel_id` | `str \| None` | 否 | 稳定注册 ID；缺省生成 `uuid4().hex` |

### 示例

```python
manager = ChannelManager(processor=my_processor)
await manager.start()
channel_id = await manager.add_channel(
    channel_type="feishu",
    config={"app_id": "...", "app_secret": "..."},
    tenant_id="acme",
)
await manager.push_text(channel_id, subject, "hello")
```

---

## 响应

### 出参

| 接口 | 返回 | 说明 |
|------|------|------|
| `add_channel(...)` | `str` | `channel_id`，用于推送与移除 |
| `get_channel(channel_id)` | `BaseChannel \| None` | 按 ID 取通道 |
| `channel_ids()` | `list[str]` | 已注册通道 ID |
| `list_subjects(channel_id)` | `list[Any]` | 通道已知会话主体 |
| `list_all_users()` | `dict[str, list[Any]]` | 各通道用户汇总 |
| `processor` | `AsyncIterator[MessageEvent]` | 流式事件序列 |

### `MessageEvent`（处理器产出）

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `type` | `MessageEventType` | `MESSAGE` | 事件类型 |
| `content` | `list[ContentPart]` | `[]` | 内容片段 |
| `metadata` | `dict[str, Any]` | `{}` | 扩展元数据 |
| `error` | `str \| None` | `None` | 错误信息（`ERROR` 事件使用） |

`MessageEventType` 取值：`message`、`delta`、`thinking`、`thinking_delta`、
`flush`、`typing`、`tool_start`、`tool_end`、`error`、`completed`。
语义：`MESSAGE` 立即发送；`DELTA` 累积至 `COMPLETED` 一并发送；`FLUSH` 冲刷当前内容并开启新消息；
`ERROR` 为失败终止事件，消费者应立即停止读取并关闭生产者，清理逻辑放在生产者 `finally`
（5 秒超时）；`COMPLETED` 结束响应流。

### 示例

```python
async def my_processor(msg: InboundMessage) -> AsyncIterator[MessageEvent]:
    yield MessageEvent.text(f"Echo: {msg.text}")
    yield MessageEvent.completed()
```

---

## 错误语义

| 错误 | 触发 | 处理建议 |
|------|------|----------|
| `ValueError("Channel not found: ...")` | `push_text` / `push_content` / `run_in_session` 传入未注册 `channel_id`，或 `session_key` 为空 | 先 `add_channel` 获取有效 ID；会话键须非空 |
| `ValueError` | 通道种类 / 插件 owner 冲突（`register_channel_kind` 覆盖 builtin 或被其他 owner 占用） | 使用唯一 `plugin_id`；reload 前停止受影响实例 |
| `ChannelCredentialsError`（继承 `ValueError`，`channel.py:159`） | 平台凭证缺失 / 无效 | 检查平台配置与 `.env`（模板 `.env.example`），不要硬编码密钥 |
| `MessageEvent.type == ERROR` | 处理器异常终止 | 消费者立即停止读取并关闭生产者；持久失败历史须在产出 `ERROR` 前写入 |

约束：`owner_tools_only` 开启时非 owner 的 `InboundMessage.allowed_tools=[]`；`None` 继承既有权限；
`owner_commands_only` 默认 `true`，空 `owner_ids` 会拒绝所有内置群命令。

---

## 数据模型

| 模型 | 字段 / 取值 | 说明 |
|------|-------------|------|
| `ContentType` | `text` / `image` / `video` / `audio` / `file` | 内容片段 discriminator |
| `TextContent` | `type`, `text` | 纯文本 |
| `ImageContent` / `VideoContent` / `AudioContent` / `FileContent` | `type`, `url`, `local_path`, `data`, `mime_type`, `size`, ... | 媒体片段；字节读取统一走 `BaseChannel.load_media_bytes(part)`，禁止直接解码 `data` 或打开 `local_path` |
| `ContentPart` | `Annotated[Text \| Image \| Video \| Audio \| File, Field(discriminator="type")]` | 判别联合类型 |
| `InboundMessage` | `channel_id`（必填）, `channel_type`, `tenant_id`, `channel_subject`, `channel_session_id`, `content`（必填）, `group_context`, `allowed_tools`, `metadata`, `timestamp` | 归一化入站消息；`text`、`has_media` 为派生属性 |
| `ChannelSubject` | `subject_id`（必填）, `first_seen`, `last_seen`, `display_name`, `chat_type`, `metadata` | 回复 / 会话目标，平台路由信息在 `metadata` |
| `GroupContext` / `GroupContextMessage` | `messages`, `capability_degraded` / `sender_id`, `text`, `content` | 短时群上下文 |
| `GroupContextConfig` | `visibility`, `activation`, `history`, `history_limit`, `history_ttl_seconds`, `clear_after_reply`, `owner_*` | 群可见性 / 激活策略，见 `README.md` |
| `ChannelConfig` | `channel_id`, `tenant_id`, `show_thinking`, `show_tool_hints`, `group_context` | 所有平台 Config 基类 |

---

## 变更记录

| 日期 | 版本 | 变更内容 | 任务 |
|------|------|---------|------|
| 2026-11-24 | 1.0 | 按 `manager.py` / `channel.py` / `models.py` 实际签名建立接口与数据契约文档 | 体检修复 `ee3adfd4` |
