# Codex Auto Model Router

[![Validate](https://github.com/orange-the-weak/codex-auto-model-router/actions/workflows/validate.yml/badge.svg)](https://github.com/orange-the-weak/codex-auto-model-router/actions/workflows/validate.yml)

**面向 OpenAI Codex 的轻量 GPT-6 Astra、GPT-6.1 Sol 和 GPT-6 Luna 推理路由器。** 将任务语义与具体模型标识分开，并提供三个可切换的路由配置。GPT-6 Sol、GPT-5.6 和 GPT-5.5 不再用于路由，但仍可读取历史记录。

[English](README.md) · [路由反馈](https://github.com/orange-the-weak/codex-auto-model-router/issues/new?template=routing-feedback.yml) · [问题反馈](https://github.com/orange-the-weak/codex-auto-model-router/issues/new?template=bug-report.yml)

GPT-5.6 为 Codex 带来了有用的模型和推理组合。GPT-6 加入后，直接把任务规则绑定到某一代模型会让后续扩展更困难，因此路由先判断任务通道，再由模型目录解析具体模型。

所以 v2 默认采用 fail-open 收益门槛路径：快速给出建议，台账不进入关键路径，并在模型切换收益超过启动与汇总成本时自动创建有界子智能体。这也是我的第一个开源项目，欢迎把真实使用中的好坏都告诉我。

**自动选择模型**

```text
当前请求
└─ 只根据这次任务重新评估
   ├─ 机械、普通、扫描或确定性深度任务 → GPT-6 Luna
   ├─ latency_priority 兼容通道 → GPT-6 Luna/max（成本与能力取舍）
   ├─ 有界复杂任务 → GPT-6.1 Sol/low
   ├─ 高歧义或高耦合 → GPT-6.1 Sol/medium
   ├─ 高后果任务 → 当前配置指定的模型与推理强度
   └─ 已分类的复杂推理失败 → 当前配置指定的模型与推理强度
      ↓
   建议一致或切换不划算 → 主线程直接完成
   建议不同且路由收益超过开销 → 使用对应模型的叶子智能体
```

**低开销并发**

```text
任务
├─ 独立、安全的工具或进程调用 → 在主线程中并发
├─ 依赖推理或存在资源冲突 → 串行执行
└─ 独立推理且路由净收益明确 → 自动进入代理模式
```

## 快速安装

直接告诉 Codex：

> 从 `https://github.com/orange-the-weak/codex-auto-model-router` 安装 `codex-auto-model-router` Skill。

或手动安装：

```bash
git clone https://github.com/orange-the-weak/codex-auto-model-router.git
cd codex-auto-model-router
./install.sh
```

安装后重启 Codex。

## 退出当前项目

直接告诉 Codex“当前项目不再使用这个 Skill”，或运行：

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/codex-auto-model-router/scripts/router_lite.py" project-disable --repository .
```

该命令会保留其他设置，只在当前项目的 `.codex/config.toml` 中加入一条受管理的 `[[skills.config]]` 禁用项。Router 命令会立即停止；随后重启 Codex，可信项目就能在后续任务中阻止该 Skill 正常加载。它只影响当前项目，不修改全局 `~/.codex/config.toml`。

恢复或查看状态：

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/codex-auto-model-router/scripts/router_lite.py" project-enable --repository .
python3 "${CODEX_HOME:-$HOME/.codex}/skills/codex-auto-model-router/scripts/router_lite.py" project-status --repository .
```

`--no-subagents` 含义不同：它只针对一次 Router 命令禁用子智能体，不会退出整个 Skill。项目配置遵循 Codex 官方的 [`config.toml` 机制](https://developers.openai.com/codex/config-reference/)。

## 路由配置与覆盖

内置的 `balanced` 保留原有路由表。`economy` 在所有通道优先选择 Luna；`quality` 将机械任务保留在 Luna，其他工作使用 Sol，并在高后果任务和分类后的复杂失败中使用 Astra/high 或 Astra/xhigh。这些配置表达模型与推理强度偏好，不保证延迟表现。

可保存全局或当前项目的默认配置，也可为单条命令临时选择：

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/codex-auto-model-router/scripts/router_lite.py" profile-set economy --scope global
python3 "${CODEX_HOME:-$HOME/.codex}/skills/codex-auto-model-router/scripts/router_lite.py" profile-set quality --scope project --repository .
python3 "${CODEX_HOME:-$HOME/.codex}/skills/codex-auto-model-router/scripts/router_lite.py" profile-show --repository .
python3 "${CODEX_HOME:-$HOME/.codex}/skills/codex-auto-model-router/scripts/router_lite.py" decide --profile balanced
```

设置保存在 `${CODEX_HOME:-~/.codex}/router.toml` 和 `<repository>/.codex/router.toml`。项目配置优先于全局配置；项目通道路由覆盖优先于全局覆盖。每项覆盖都需要同时指定模型和推理强度：

```toml
schema_version = 1
profile = "quality"

[profiles.quality.routes.complex_uncertain]
model = "gpt-6.1-sol"
effort = "high"
```

可以使用 `router_lite.py decide --profile quality ...` 或 `plan --profile economy ...` 临时切换。`profile-set` 只更改已保存的配置名称，并保留通道路由覆盖。

## Fast / Standard executor 隔离

Service tier 配置在每个 executor 预设中，不通过切换共享 `/fast` 状态实现。Luna 预设不设置 `service_tier`，从而继承用户 Fast 偏好；GPT-6.1 Sol 和 Astra executor 则明确使用 `service_tier = "default"`（Standard）。每个 agent 的设置相互独立，Luna 与 Sol 并发时不会互相改变 tier。

## 工作方式

每个适用请求只走三条路径之一：

| 路径 | 行为 |
|---|---|
| Local | 推荐路由，然后由当前主智能体完成工作。 |
| Tool concurrency | 不创建子智能体，并发运行独立安全的工具或进程调用。 |
| Benefit-gated subagents | 路由收益明确超过有界开销时，自动委派、复用或进行多模型推理。 |

默认路径不使用 Restore、计划哈希、游标、环境变量门禁或阻塞式台账。路由或执行器启动失败不会阻塞普通工作。旧的严格状态机只在用户明确要求严格审计或防重放时启用。

所有可见路由提示都会跟随当前请求的语言：英文请求使用英文标签，中文请求使用中文标签；模型、推理强度和原因值保持不变。

当建议路由不同但仍由主线程执行时，提示会简洁说明主对话模型已固定、子智能体启动成本高于预期收益。实际委派时则写出切换原因，避免把推荐模型误认为已经执行的模型。Skill 内只保存英文规范模板，运行时再按用户当前语言自然翻译。

Skill 加载时，本轮主对话的模型和推理强度已经确定，因此 Router 不能主动切换它们。`recommended_route` 在实际委派前只是建议；委派后由独立叶子任务运行建议模型，并不改变已经开始的主对话。用户在 UI 选模或修改配置通常只影响后续任务或请求。直接工具并发仍共享当前主模型和推理强度，不会产生独立推理流或子智能体卡片。

适合直接并发的工作包括独立文件读取、搜索、元数据查询，以及不共享构建状态的测试。依赖前一步语义判断、重叠写入、Git 修改、部署、审批，以及共享模拟器、设备或构建资源的动作必须串行。

当路由适配、质量、延迟或资源收益明确超过有界启动与汇总开销时，子智能体模式会自动启用，不需要额外询问用户许可；用户可用 `--no-subagents` 明确禁用。委派前的提示应标为“计划执行器”；只有成功收到创建或复用确认后，才能标为实际执行的叶子智能体。每次单独或并行创建前，都要验证 `task_name` 符合 `^[a-z0-9][a-z0-9_]{0,47}$`，仅使用小写字母、数字和下划线（例如 `pipeline_workflows`），并先把连字符名称规范化。委派仍保留有界生命周期规则：`completed` 是正常终态，子任务 `task_complete` 覆盖父侧陈旧的 `running`，单次等待超时本身不等于停滞，复用也不会跨用户请求。

主线程发送最终回复前，只要本轮使用过子智能体，就会停止新调度、禁用复用、清空当前请求的复用登记、刷新当前任务树、中断所有仍真实 `running` 但已非必需的子智能体，并再次刷新。只有当前请求拥有的全部子智能体都进入终态后才结束。这个流程能结束当前任务的子智能体，但 Codex 协作接口没有删除已完成子智能体 UI 历史的操作；历史卡片可能继续显示，Skill 不会声称已经清除。

CLI 默认启用收益门槛委派；`--no-subagents` 是明确退出开关。旧的 `--allow-subagents` 仍为调用方兼容而接受，但不再代表授权，也不是必需参数。执行器预设只在收益门槛通过后自动选择，绝不预热或预建等待队列。

## v0.2 更新重点

- 默认路径会在模型切换收益明确超过有界开销时自动使用对应模型的叶子智能体。
- 独立安全的工具和进程可以并发执行，不复制模型上下文，也不新增子智能体 UI 条目。
- `--no-subagents` 可明确禁用委派、复用和代理并发；其他情况下无需额外询问许可。
- 推荐路由与本轮实际使用的模型被明确分开，不再声称 Skill 已切换主对话模型。
- Ultra 仍需用户显式开启。路由配置可在 GPT-6 Astra、GPT-6.1 Sol 与 GPT-6 Luna 间选择；GPT-6 Sol 和 GPT-5.6 不可选择，GPT-5.5 不再作为可用性回退。

## balanced 配置的模型梯度

| 任务 | 默认路由 |
|---|---|
| 确定性机械任务 | GPT-6 Luna / medium |
| 普通有界任务 | GPT-6 Luna / high |
| 大型有界扫描或审查 | GPT-6 Luna / xhigh |
| 大型确定性深度任务 | GPT-6 Luna / max |
| `latency_priority` 兼容通道（成本与能力取舍） | GPT-6 Luna / max |
| 有界复杂任务 | GPT-6.1 Sol / low |
| 高歧义或高耦合 | GPT-6.1 Sol / medium |
| 高后果任务 | balanced 使用 GPT-6.1 Sol / high；quality 使用 GPT-6 Astra / high |
| 复杂推理或验证已有失败 | balanced 使用 GPT-6.1 Sol / xhigh；quality 使用 GPT-6 Astra / xhigh |

`latency_priority` 通道名为兼容而保留，其 `balanced` 配置的 Luna/max 路由体现成本与能力取舍，不代表最快路由。`sol` 表示 GPT-6.1 Sol，`astra` 表示 GPT-6 Astra。GPT-6 Sol、GPT-5.6 和 GPT-5.5 不可用于路由，但历史执行记录仍可读取。

Ultra 永不自动启用。用户显式使用 Ultra 时，由其原生编排接管，并关闭 Router 并发。Luna 路由不可用时可按相同 effort 回退到 Sol；Sol 路由不会降级到 Luna。Sol 不可用时，保留首选路由建议并按常规本地 fail-open 路径处理。GPT-5.5 不再作为可用性回退。

## 测评与台账

用户提供的 Artificial Analysis 图表（记录日期 2026-10-02）估算 Luna 从 low 的指数约 21、每任务约 $0.005，到 max 的指数约 37、每任务约 $0.068；Sol 6.1 从 low 的指数约 42、每任务约 $0.131，到 max 的指数约 52、每任务约 $0.724。这些值来自图表坐标估读，支持 Luna 承担低成本有界任务、Sol 承担更高能力任务。图表没有延迟数据，也没有测量 Codex 订阅费用。

effort 的完整估值和限制记录在[测评证据](references/benchmark-evidence.md)中。历史 GPT-5.6 测评快照独立保留，不用于校准这些模型路由。任务证据和受支持的模型覆盖始终优先。

完整数据见[测评证据](references/benchmark-evidence.md)和[机器可读快照](references/benchmark-evidence.json)。快照缺失、损坏或过期时，Router 直接使用确定性规则，不阻塞任务。

只有观察到的真实执行才会写入台账，推荐路由绝不记作实际模型使用。收益门槛子智能体模式会返回机器可读的启动契约：执行器类型必须搭配 `fork_turns="none"`；契约不匹配时不重试，直接由主任务接管。台账失败不会影响项目交付。

## 开发

```bash
python3 -m unittest discover -s tests
python3 tests/validate_distribution.py
```

隐私安全的反馈与贡献方式见 [CONTRIBUTING.md](CONTRIBUTING.md)。
