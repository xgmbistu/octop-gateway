# 集成测试规范

## 环境

引用：.wally/docs/devops/test-env-deploy.md、.env.example、AGENTS.md §6、pyproject.toml。runner 为 pytest（[tool.pytest.ini_options]：asyncio_mode=auto、testpaths=tests、注册 integration marker）。测试环境为本机 + 网络，命中真实 IM 平台 API（Feishu `open.feishu.cn`、QQ Bot API、DingTalk OAuth）；用例位于 tests/channels/test_qq.py、test_feishu.py、test_dingtalk.py；tests/test_media_integration.py 为本地文件后端端到端管线测试（不标记 integration）。凭证来自 .env（git 忽略，模板 .env.example）：QQ_APP_ID/QQ_TOKEN/QQ_SECRET、FEISHU_APP_ID/FEISHU_APP_SECRET、DINGTALK_APP_KEY/DINGTALK_APP_SECRET；test_dingtalk.py 缺凭证时由 skipif 跳过，Feishu/QQ 用例需真实凭证，否则对真实 API 调用失败。禁止提交明文凭证。

## 用例

覆盖 TestQQChannelIntegration（token / gateway URL / WS HELLO / IDENTIFY / READY）、TestFeishuChannelIntegration + TestFeishuExtendedFeatures（tenant token / bot info / chats / 收发消息与卡片）、TestDingTalkChannelIntegration（token）；tests/test_media_integration.py 覆盖媒体下载→持久化→backend 读取（mock fetch + tmp filesystem）。断言覆盖业务结果与副作用（token 非空、握手 op、bot open_id、落盘字节、mock 调用一次），非仅响应码；稳定回归用例置于 tests/。

## 执行与判定

命令：make test-integration（Makefile → `pytest -m integration`，有 uv 时为 `uv run pytest -m integration`）；单用例迭代见 AGENTS.md §6（`uv run pytest tests/channels/test_feishu.py -k media -xvs`）。成功判据：退出码 0 且 @pytest.mark.integration 用例全部通过，缺 DINGTALK 凭证时 skip 视为可接受；须区分断言失败 / 环境凭证缺失 / 执行错误，退出码不替代业务结果。CI 门禁（.github/workflows/ci.yml）仅跑 make test（`-m "not integration"`），集成测试为本地/手动阶段，不自动进 CI 门禁。

执行前读取本任务 execution.json 的 it 配置；command/guide 均为空则自动 SKIPPED，保留未验证边界。配置后的失败或环境/权限/工具缺失应阻塞，不得冒充未配置。


初始化时从项目实际文件补齐执行指引，记录来源、工作目录、命令、前置依赖、结果判据及清理/回滚。必要信息缺失时在 `.wally/config.json` 设可选 `readiness: pending` 并列出具体 `gaps`，向用户询问并等待补齐；阶段标为 BLOCKED，不能自动跳过或因指南路径非空而启用。静态核验完整后才设 ready，不代表执行通过。未带 readiness 的旧配置仍兼容 command/guide 判断。
