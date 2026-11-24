# 测试环境部署

以项目已有部署文档为权威，在这里记录引用、实际命令与验证方式。

## 环境与执行

- 环境类型、地址、资源归属、访问和部署授权边界：**未定义**。本仓为 Python 库（pyproject.toml：hatchling 构建，发布为 PyPI 包 octop-gateway），无常驻服务，无 Dockerfile / Compose / k8s / 部署脚本；env.md 仍为未填写模板，本文据实记录环境缺失；缺测试环境地址、资源归属与授权边界。
- 创建/查询/代码同步/部署命令：**无真实部署命令**。仓库仅有构建/发布动作：make build（wheel + sdist）、make publish-test（PYPI_REPO=testpypi → TestPyPI）、make publish（PyPI，PYPI_TOKEN），以及 .github/workflows/release.yml（v* tag 触发：make test → make build → pypa/gh-action-pypi-publish）。这些是发布动作，非测试环境部署，不能作为 deploy.command。
- 依赖、配置和凭证来源（不记录明文）：依赖见 pyproject.toml / uv.lock / make install（uv sync --extra dev）；发布凭证 PYPI_TOKEN（交互输入或环境变量）/ secrets.PYPI_API_TOKEN。无部署环境凭证获取方式。
- 就绪与生效检查命令：**无**（无健康检查 / smoke / 生效验证入口）。
- 缺陷修复前保留基线的方法：**无**（未见环境快照或基线保留流程）。
- 回滚命令与触发条件：**无**（未见回滚 / 撤销发布流程）。
- 清理/释放及保留条件：**无**（未见环境释放流程）。

## 项目自定义

- 仓库性质：多平台 IM 通道桥接库（src/octop_gateway/），供下游 pip install 使用，自身不提供常驻服务，故不存在测试环境部署目标。
- 质量门禁（.github/workflows/ci.yml）：make install → make lint → make typecheck → make test（pytest -m "not integration"）；集成测试不进 CI。
- 静态核验结论：缺真实部署入口、目标环境、凭证获取、生效验证与回滚，.wally/config.json 的 deploy 记 readiness: pending 并列出 gaps，不猜测命令。


初始化时从项目实际文件补齐执行指引，记录来源、工作目录、命令、前置依赖、结果判据及清理/回滚。必要信息缺失时在 `.wally/config.json` 设可选 `readiness: pending` 并列出具体 `gaps`，向用户询问并等待补齐；阶段标为 BLOCKED，不能自动跳过或因指南路径非空而启用。静态核验完整后才设 ready，不代表执行通过。未带 readiness 的旧配置仍兼容 command/guide 判断。
