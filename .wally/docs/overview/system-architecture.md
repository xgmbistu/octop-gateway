---
kind: panorama
scope: system-architecture
status: verified
origin: human
source_paths:
  - src/octop_gateway/__init__.py
  - src/octop_gateway/channel.py
  - src/octop_gateway/manager.py
  - src/octop_gateway/models.py
  - src/octop_gateway/constraints.py
  - src/octop_gateway/group_context.py
  - src/octop_gateway/media.py
  - src/octop_gateway/push_routing.py
  - src/octop_gateway/utils.py
  - src/octop_gateway/format_tables.py
  - src/octop_gateway/channels/__init__.py
symbols:
  - BaseChannel
  - ChannelConfig
  - ChannelCredentialsError
  - MessageProcessor
  - ChannelManager
  - ChannelSubject
  - InboundMessage
  - MessageEvent
  - ContentPart
  - ChannelConstraints
  - RateLimiter
  - ReplyTimeoutGuard
  - TypingKeepalive
  - GroupContextManager
  - GroupContextConfig
  - MediaBackend
  - FileSystemMediaBackend
  - strip_ephemeral_push_meta
  - close_event_stream
  - BUILTIN_CHANNELS
  - register_channel_kind
upstream: [../../README.md]
downstream: [integrations/index.md]
last_verified: 2026-11-24
---

# 系统技术架构（octop-gateway）

> Source: `src/octop_gateway/**`（见 frontmatter `source_paths`），`pyproject.toml`、`README.md`
> Last-verified: 2026-11-24（对照提交 `1cf169b` 的源码逐项核验）
> 本页为人工维护页（`origin: human` / `status: verified`），不自动覆盖；改动下方任一模块后按「变更影响定位」复核本页。

## 1. 组件定位与边界

- **是什么**：`octop-gateway`（`pyproject.toml`：包名 `octop-gateway`，版本 `1.0.4`，`requires-python >=3.12`，hatchling 构建为 wheel/sdist 发布到 PyPI）是一个**多平台 IM 通道桥接库**，向上把 10 个 IM 平台的事件归一成统一的 `InboundMessage`，向下把宿主 Agent 输出的 `MessageEvent` 转换成各平台的发送调用。
- **不是什么**：它是**同进程内嵌库**，不是常驻服务。没有自带 HTTP 服务、进程编排或部署入口（`.wally/config.json` 的 `deploy` 仍为 `readiness: pending`，其 gaps 明确记录「仓库为 Python 库，仅有构建与发布动作 `make build` / `make publish*` 与 `.github/workflows/release.yml`，属发布而非部署」）。平台连接由各适配器在宿主进程内主动建立。
- **外部依赖方向**：宿主（如 `octop-harness`）注入 `MessageProcessor` 并持有 `ChannelManager`；本库反向依赖各平台 SDK（`lark-oapi`、`dingtalk-stream`、`discord-py`、`wecom-aibot-sdk`、`paho-mqtt`、`python-telegram-bot`、`python-socketio`、`websockets`、`httpx`、`aiohttp`、`pydantic`、`cryptography` 等，见 `pyproject.toml`）。

## 2. 模块职责（逐项对照实现）

| 模块（源码路径） | 职责 | 关键符号 |
|---|---|---|
| `src/octop_gateway/__init__.py` | 公共 API 出口，`__all__` 汇总对外类型 | `__all__` |
| `src/octop_gateway/models.py` | 统一消息模型：`ContentPart` 判别联合、入站消息、出站事件、群上下文、路由主体 | `ContentType`、`TextContent`/`ImageContent`/`VideoContent`/`AudioContent`/`FileContent`、`ContentPart`、`MessageEventType`、`InboundMessage`、`MessageEvent`、`GroupContext`/`GroupContextMessage`、`ChannelSubject` |
| `src/octop_gateway/channel.py` | 抽象基类 + 配置基类 + 共享入站模板：解析、媒体持久化、群策略、事件缓冲投递、限流/超时/打字、出站三层 API、主体注册表 | `BaseChannel`、`ChannelConfig`、`ChannelCredentialsError`、`MessageProcessor`、`handle_inbound`/`_prepare_inbound`/`_process_inbound`/`_finalize_inbound`、`_send_text`/`_send_content`/`_send_media`、`reply_*`/`push_*`、`load_media_bytes`/`_persist_media`、`resolve_push_subject` |
| `src/octop_gateway/manager.py` | 编排：每通道队列与 worker 池、会话锁串行、同会话批量合并、动态增删通道、凭证探测、主动推送、宿主回调钩子 | `ChannelManager`、`start`/`stop`、`add_channel`/`_build_config`/`_instantiate_channel`/`_register_channel`/`probe_channel`、`enqueue`/`_put_to_queue`/`_worker_loop`/`_session_lock`/`_drain_same_session`、`push_text`/`push_content`/`push_to_all`/`run_in_session` |
| `src/octop_gateway/channels/__init__.py` | 内置通道注册表（懒加载，避免一次性导入全部 SDK）+ 插件注册 API | `_CHANNEL_MAP`/`_CLASS_NAMES`、`ChannelKind`、`SUPPORTED_CHANNEL_KINDS`、`BUILTIN_CHANNELS`(`_LazyBuiltinDict`)、`register_channel_kind`/`unregister_channel_kind`/`registered_channel_kinds` |
| `src/octop_gateway/channels/<kind>/` | 10 个平台适配器，各自实现 `start`/`stop`/`parse_inbound`/`_send_*` 及平台私有上传/下载 | Feishu、DingTalk、QQ、WeCom、Weixin、Yuanbao、Xiaoyi、MQTT、Telegram、Discord |
| `src/octop_gateway/constraints.py` | 平台约束配置与运行期工具：滑动窗口限流、回复超时占位、打字保活、工具/思考展示模板 | `ChannelConstraints`、`RateLimiter`、`ReplyTimeoutGuard`、`TypingKeepalive`、`tool_hint_message` |
| `src/octop_gateway/group_context.py` | 群聊可见性/激活/历史策略、被动消息缓冲、owner 命令与工具鉴权、能力降级 | `GroupVisibility`/`GroupActivation`/`GroupHistoryMode`、`GroupContextConfig`/`GroupContextPolicy`、`GroupContextManager`（`accepts`/`prepare`/`mark_replied`/`should_persist_media`/`handles`/`protects_command`/`protects_tools`） |
| `src/octop_gateway/media.py` | 媒体字节存储抽象（key → bytes），入站落盘、出站读字节统一走此层 | `MediaBackend`、`FileSystemMediaBackend` |
| `src/octop_gateway/push_routing.py` | 主动推送路由：剔除仅属于被动回复的临时字段、iLink 持久 context_token 键 | `EPHEMERAL_PUSH_META`、`strip_ephemeral_push_meta`、`alias_subject_fields`、`WEIXIN_CONTEXT_TOKEN_KEY` |
| `src/octop_gateway/utils.py` | 内容检查/合并、防抖、事件流关闭（5s 超时） | `extract_text`/`extract_media`/`has_text`/`has_media`、`merge_messages`、`Debouncer`、`close_event_stream`、`STREAM_CLOSE_TIMEOUT` |
| `src/octop_gateway/format_tables.py` | 为不支持 GFM 表格的平台渲染 Markdown 表格 | `_display_width`/`_pad`/`_split_row` 等 |

## 3. 关键调用链

### 3.1 入站（平台事件 → 宿主 processor）
1. 适配器收到平台原生事件，调用 `BaseChannel.enqueue(payload)`，该回调由 `ChannelManager` 在 `_register_channel`/`start` 中通过 `set_enqueue_callback` 注入。
2. `ChannelManager.enqueue` → `loop.call_soon_threadsafe(_put_to_queue, ...)`（线程安全，供 SDK 的 WebSocket/回调线程使用）→ `asyncio.Queue(maxsize=queue_maxsize)`；队列满则 `logger.error` 丢弃该载荷。
3. `_worker_loop`（每通道 `workers_per_channel` 个，默认 4）取出载荷 → `channel.parse_inbound(payload) -> InboundMessage` → `group_context_manager.accepts` 鉴权 → `get_debounce_key(message)` 得会话键（默认 `channel_subject.subject_id`）→ `_drain_same_session` 同会话合并（上限 20 条）→ `merge_inbound` → `on_pre_lock` 宿主钩子 → `async with _session_lock(channel_id, session_key)` 串行化 → `channel.handle_inbound(merged)`。
4. `BaseChannel.handle_inbound`（共享模板，适配器不应整体替换）：`_prepare_inbound`（`parse_inbound` → `_preprocess_inbound` 适配器解密/归一化 → `accepts` → `_track_subject` 主体登记 → 需要时 `_persist_media` → `_group_context.prepare` 注入 `GroupContext` → 绑定 `ChannelSubject`）→ `_process_inbound` → `_finalize_inbound`（成功后 `mark_replied` 清空一次性群上下文）。
5. `_process_inbound` 调 `self._processor(message)` 得到 `AsyncIterator[MessageEvent]`：`DELTA`/`THINKING_DELTA` 累积、`FLUSH`/`COMPLETED` 冲刷、`MESSAGE` 立即投递、`ERROR` 终止；异常被捕获后冲刷缓冲并发送兜底文案，`finally` 中取消 `timeout_guard`/`typing_keepalive` 并 `close_event_stream(events)`（5s 超时保护生产者 finalizer）。
6. 投递：`_deliver_event` / `_rate_limited_send` → `_clean_output` 清洗 `<think>` → `reply_text` → `_acquire_rate_slot()` → 平台原语 `_send_text(subject, text)`。

### 3.2 出站三层 API（限流只 acquire 一次）
- `reply_*`（入站上下文）与 `push_*`/`push_message`（bot 主动）是**公共层**，每条「用户可见消息」只调用一次 `_acquire_rate_slot()`。
- `_send_text` / `_send_content` / `_send_media` 是**抽象平台原语层**，由适配器实现；文档明确规定适配器内部必须调用同级 `_send_*` helper，**不得**回调 `self.reply_text`/`push_text`，否则一条消息会重复占用限流额度。
- 路由目标由 `ChannelSubject.subject_id` 决定，平台附加字段（`msg_id`、`webhook_url`、`chat_type` …）在 `ChannelSubject.metadata` 中。

### 3.3 主动推送（bot-initiated）
`ChannelManager.push_text`/`push_content`/`push_to_all` → `BaseChannel.push_text`/`push_message` → `resolve_push_subject`（合并 `_known_subjects` 中的入站路由态、平台 `_enrich_push_metadata` 回填、`strip_ephemeral_push_meta` 剔除 `msg_id`/`webhook_url`/`context_token`/`response_url` 等仅被动回复有效的字段）→ `_send_*` 走主动发送路径。`run_in_session` 让带外操作复用同一会话锁，避免与入站处理交错。

### 3.4 媒体链路
- 入站：`_persist_media` 遍历 `message.content` 及 `group_context.messages`，对有 `url` 无 `local_path` 的媒体调 `fetch_remote_media(url)`（适配器可覆写注入平台鉴权头）→ `_media_backend.save(data, key)` → 回填 `part.local_path`/`size`/`mime_type`。key 形如 `{channel_type}/{channel_id}/{filename}`。
- 出站：`load_media_bytes(part)` 按 `data`(base64 内联) > `local_path`(MediaBackend key) > `url`(远端拉取并回写缓存) 的优先级解析字节；`local_path` 无 backend 时抛 `RuntimeError`。媒体上传平台 CDN/COS 由适配器私有 helper 完成（如 Yuanbao 先传 COS 再发 TIM 媒体元素）。
- `MediaBackend` 是宿主可插拔扩展；`ChannelManager.start` 未提供时默认 `FileSystemMediaBackend("/")`。

### 3.5 生命周期与注册
`ChannelManager.start` → 传播 `MediaBackend`、应用全局 `constraints`、建队列与 enqueue 回调 → 逐个 `channel.start()`（失败仅记录日志、隔离故障域）→ 创建 worker 任务。`add_channel(channel_type, config, ...)` → `_build_config`（dict 经 `Config.from_dict` 构造，未知键忽略、别名映射）→ `missing_credentials()` 校验，缺凭证抛 `ChannelCredentialsError`（**不发起网络**）→ `_instantiate_channel` → `_register_channel`（启动失败则回滚注册与队列）→ 运行中再拉起 worker。`BUILTIN_CHANNELS` 用 `_LazyBuiltinDict` 按 `_CHANNEL_MAP` 懒加载类，避免导入期加载全部 SDK；`register_channel_kind` 供插件扩展，内置 kind 不可覆盖。

## 4. 上下游协议

### 4.1 上游（各 IM 平台 → `parse_inbound`）
| 通道 kind | 传输 / SDK | 入站契约要点 |
|---|---|---|
| `feishu` | lark-oapi WebSocket + REST | `app_id`/`app_secret`；HTTP 回调可用 `verification_token`/`encrypt_key` 校验解密 |
| `dingtalk` | dingtalk-stream Stream | `app_key`/`app_secret`/`robot_code` |
| `qq` | WebSocket | `app_id`/`token`/`secret`/`intents`，支持沙箱；含 QR 绑定登录 |
| `wecom` | wecom-aibot-sdk 回调 + API | `bot_id`/`secret`，首 token 超时自带占位/流式处理 |
| `weixin` | iLink | 多账号 `WeixinAccountConfig`，`context_token` 用于回复，持久键见 `push_routing.py` |
| `yuanbao` | WebSocket(`wss://.../wss/connection`) + COS | `app_key`/`app_secret`，媒体先传 COS |
| `xiaoyi` / `mqtt` / `telegram` / `discord` | 华为 OpenClaw / paho-mqtt MQTT / python-telegram-bot 长轮询 / discord.py Gateway WebSocket | Discord 需 Message Content Intent 与 `allowed_*` 白名单 |

统一产出 `InboundMessage`：`content: list[ContentPart]`、`channel_subject`（DM 为用户、群聊为会话）、`metadata`（`sender_id`/`sender_name`/`chat_type`/`conversation_id`/`bot_mentioned`/`msg_id` …）、`group_context`。群聊保留个体作者于 `metadata`，使全群共享一个会话线程而不丢归属。

### 4.2 与宿主的契约（本组件最重要的对外协议）
- 注入：`MessageProcessor = Callable[[InboundMessage], AsyncIterator[MessageEvent]]`。唯一 processor，10 个平台共用。
- 出站事件类型（`MessageEventType`）：`MESSAGE`、`DELTA`、`THINKING`、`THINKING_DELTA`、`FLUSH`、`TYPING`、`TOOL_START`、`TOOL_END`、`ERROR`、`COMPLETED`；构造工厂在 `MessageEvent`（`text`/`delta`/`thinking`/`flush`/`tool_start`/`tool_end`/`completed`/`error_event`）。`ERROR` 为终止事件，生产者须在 `finally` 自行清理，且须在 yield 前持久化失败历史。
- 宿主注入（`ChannelManager.__init__` / `set_pre_lock_handler`）：`on_pre_lock`（`/stop`、`/cancel` 预锁信号）、`control_message_predicate`、`interrupt_message_predicate`（紧急控制消息绕过会话锁）、`MediaBackend` 实现、`constraints` 运行期覆盖、`processor` 默认处理器；通道级回调 `BaseChannel.set_on_new_subject`（新主体首次出现）。

### 4.3 下游（本库 → 各平台发送 API / 存储）
- 平台原语 `_send_*` 由适配器把统一内容转成平台调用（REST/WebSocket 发送、CDN/COS 上传）；`ChannelSubject.metadata` 携带路由附加字段。
- `ChannelManager.push_*`、`BaseChannel.push_*` 为带外主动发送；`strip_ephemeral_push_meta` 保证主动消息不误用被动回复字段。
- `MediaBackend`（默认 `FileSystemMediaBackend`）承载二进制媒体；`format_tables.py` 为不支持 GFM 的平台（QQ、WeChat iLink 拍平为键值行；Telegram 先试原生富文本，API 拒绝后回退对齐代码块）渲染表格。

## 5. 失败影响与隔离边界

| 失败点 | 处理位置 | 影响范围 / 行为 |
|---|---|---|
| processor 抛异常 / yield `ERROR` | `channel.py:_process_inbound` / `_deliver_event` | 捕获后冲刷已累积 delta、发送兜底文案、取消 guard、`close_event_stream`；**单条消息失败不终止 worker**；`processing_succeeded=False` 时不 `mark_replied`，被动群上下文保留 |
| worker 循环异常 | `manager.py:_worker_loop` | `logger.exception` 后继续取队列，坏载荷/适配器失败被隔离 |
| 队列满 | `manager.py:_put_to_queue` | 丢弃该载荷并记日志（该条消息丢失，不阻塞其它会话） |
| MediaBackend 读写/缓存失败 | `channel.py:load_media_bytes` / `_persist_media` | 出站缓存失败 `logger.debug` 非致命；入站持久化失败 `logger.warning` 非致命；`local_path` 无 backend 抛 `RuntimeError` |
| 通道 `start()` 失败 | `manager.py:start` / `_register_channel` | 启动期仅记录、其它通道继续；运行期注册则回滚注册与队列后抛错，避免留下无 worker 的僵尸通道 |
| 凭证缺失 | `manager.py:add_channel` / `probe_channel` | `ChannelCredentialsError`，**在建连前**失败 |
| 限流 | `constraints.py:RateLimiter.acquire` | 阻塞等待额度，仅拖慢该次发送 |
| 回复超时 | `constraints.py:ReplyTimeoutGuard`（0.8×timeout 触发） | `timeout_strategy="placeholder"` 时先发占位文案保活；成功回复时 `cancel()` |
| 群聊非 owner 命令 / 工具 | `group_context.py:accepts`/`prepare` | `accepts=False` 在批处理、宿主回调、媒体 I/O **之前**丢弃；`owner_tools_only` 时置 `allowed_tools=[]` |
| 激活能力降级 | `group_context.py:_effective_activation` | `ALWAYS` 但可见性非 `ALL` 时降级为 `MENTION` 并置 `GroupContext.capability_degraded=True` |
| 紧急控制消息 | `manager.py:_run_interrupt` | 不经会话锁直接 `handle_inbound`，异常同样被隔离 |

## 6. 变更影响定位（一次变更可据此圈定范围）

| 欲改动 | 必查源码 | 相关测试 |
|---|---|---|
| 新增 / 修改某平台适配器 | `channels/__init__.py`（`_CHANNEL_MAP`/`_CLASS_NAMES`/`ChannelKind`）、`channels/<kind>/`、`manager.py` 的 `add_*_channel` 便捷方法与类型提示、`README.md` 平台表 | `tests/channels/test_<kind>.py`、`tests/test_channel_registration.py` |
| 统一入站模型 / 字段 | `channel.py`（`parse_inbound` 契约、`_prepare_inbound`/`handle_inbound`）、`models.py`、所有适配器 `parse_inbound`、`group_context.py` 对 metadata 的读取 | `tests/test_channel.py`、`tests/test_models.py`、`tests/test_group_context.py` |
| 出站 / 限流 / 超时 | `channel.py`（`reply_*`/`push_*`/`_send_*`/`_rate_limited_send`）、`constraints.py`、`push_routing.py`、各适配器 `_send_*` | `tests/test_channel.py`、`tests/test_constraints.py`、`tests/test_push_routing.py`、`tests/test_error_delivery.py` |
| 群聊策略 | `group_context.py`、`models.py:GroupContext`、适配器注入的 metadata | `tests/test_group_context.py` |
| 媒体收发 | `media.py`、`channel.py`（`load_media_bytes`/`_persist_media`/`_derive_storage_key`/`_resolve_media_filename`）、适配器 `fetch_remote_media` 与 COS/CDN 上传 | `tests/test_media.py`、`tests/test_media_integration.py`、`tests/test_send_local_media.py` |
| 事件协议 / 流关闭 | `models.py`（`MessageEventType` 与工厂）、`channel.py:_process_inbound`/`_deliver_event`、`utils.py:close_event_stream` | `tests/test_models.py`、`tests/test_channel.py` |
| 调度 / 会话串行 / 批量 | `manager.py`（队列、worker、`_session_lock`、`enqueue`、`_drain_same_session`）、`channel.py`（`get_debounce_key`/`should_batch_inbound`/`merge_inbound`） | `tests/test_manager.py` |
| 配置 / 凭证 | `channel.py:ChannelConfig.from_dict`/`missing_credentials`、各 `Config` dataclass、`manager.py:_build_config`/`probe_channel` | `tests/test_channel_config.py` |

对照方法：`git diff` 定位本次改动的源码路径 → 按上表找到对应文档章节与源码锚点（见 frontmatter `source_paths`/`symbols`）→ 核对正文与实现是否一致 → 同步更新本页与对应测试；`README.md` 的 Architecture 小节与平台表是面向使用者的摘要，改协议时一并核对。

## 7. 入口分组自检

- 架构文档入口：本页 `.wally/docs/overview/system-architecture.md`（`status: verified`、`origin: human`、`source_paths`/`symbols` 非空且可解析，正文含本组件模块职责、调用链、上下游协议、失败影响与影响定位）。
- 源码入口：`src/octop_gateway/**/*.py`（`{source}*.{code}` 分组），公共 API 见 `src/octop_gateway/__init__.py`。
- 详细上下游页入口：`.wally/docs/integrations/index.md`（本页 `downstream`）；接口/单测/集成测试/运维执行规范分别位于 `.wally/docs/apis/`、`unittest/`、`integration_test/`、`devops/`，执行入口见 `.wally/config.json` 与 `Makefile`。
