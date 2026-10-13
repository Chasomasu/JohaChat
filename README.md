# Joha（约哈）— 智能群聊机器人

> 🤖 基于 LLM 的智能群聊机器人框架，支持多模型切换、智能回复决策、风格学习。

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Version](https://img.shields.io/badge/Version-3.7.0-green.svg)

[功能特性](#-功能特性) • [快速开始](#-快速开始) • [文档导航](#-文档导航) • [更新日志](CHANGELOG.md)

</div>

***

## ✨ 功能特性

### 🎯 核心能力

| 特性         | 说明                                          |
| ---------- | ------------------------------------------- |
| **智能决策**   | 基于概率计算（Logit 累加 + Sigmoid 归一化）判断是否回复，避免废话刷屏 |
| **多模型切换**  | 运行时动态切换 AI 模型（DeepSeek / 通义千问 / Gemini 等）   |
| **消息队列合并** | 短时间内的多条消息自动合并，减少不必要的回复                      |
| **多模态支持**  | 支持图片理解（Qwen-VL、GPT-4o 等视觉模型）需自行配置           |
| **群组动态调节** | 根据群活跃度、消息频率、认可率自动调整回复阈值                     |

### 🚀 进阶能力

| 特性          | 说明                                      |
| ----------- | --------------------------------------- |
| **风格学习**    | 自动学习群成员说话风格，使回复更自然融入群聊                  |
| **人设管理**    | 基于多维度参数的精细化人设系统，支持动态调整性格特质、表达风格、社交行为等参数 |
| **工具调用**    | MCP 风格工具系统，支持搜索、网页抓取等工具                 |
| **主动/被动模式** | 支持全局和逐群设置主动/被动回复模式                      |
| **冷却系统**    | 防刷屏机制，避免频繁回复                            |
| **用户画像**    | 记录用户偏好和聊天习惯                             |
| **管理员系统**   | 多级权限管理，管理员专属命令                          |

***

## 🚀 快速开始

**环境要求**：Python >= 3.10，运行中的 [NapCatQQ](https://github.com/NapNeko/NapCatQQ)（OneBot 协议消息平台，默认 WebSocket 端口 3002）。

```bash
# 1. 克隆项目并安装依赖
git clone <your-repo-url>
cd JohaChat
pip install -r requirements.txt

# 2. 复制主配置并填入 LLM API Key
cp joha/config/config.example.json joha/config/config.json

# 3. 编辑 joha/adapter/connection.yaml，填写 NapCat 连接参数
#    napcat:
#      ws_url: ws://127.0.0.1:3002
#      bot_uin: "你的机器人QQ号"

# 4. 启动机器人
python run.py
```

> 如果 `run.py` 中的 `bot_uin` 与当前 NapCat 登录账号不一致，程序会直接停止连接，避免接错机器人账号。
>
> 详细部署步骤（虚拟环境、后台运行、systemd 守护、备份升级）见 [docs/deployment.md](docs/deployment.md)。

### � 命令速查

| 命令 | 说明 |
| --- | --- |
| `/好评` `/差评` | 反馈机器人回复质量（全员可用） |
| `/群状态` | 查看当前群运行状态（全员可用） |
| `/帮助` | 显示全部命令列表 |
| `/全局启动` `/全局关闭` `/本群启动` `/本群关闭` | 切换主动/被动模式 |
| `/模型` `/切换模型 <名称>` | 查看与切换 LLM |
| `/人设列表` `/切换人设` `/绑定人设` | 人设管理 |
| `/统计` `/模式` `/管理员列表` | 运行信息与管理 |

> 完整命令与参数说明见 [docs/modules.md](docs/modules.md)，多数命令支持自然语言别名（如发送"帮助"触发 `/帮助`）。

***

## 📚 文档导航

| 文档 | 说明 |
| --- | --- |
| [部署运维](docs/deployment.md) | 环境准备、部署步骤、后台运行与守护、数据备份、升级 |
| [配置详解](docs/configuration.md) | `connection.yaml` / `config.json` / `reply_decision.json` 全参数说明与调参指南 |
| [架构设计](docs/architecture.md) | 分层架构总览、数据流向、存储结构 |
| [模块说明](docs/modules.md) | 各模块与文件职责速查、命令清单 |
| [API 参考](docs/api_reference.md) | MessageClient、BotAPI、DecisionEngine 等核心 API |
| [二次开发指南](docs/development.md) | 添加新命令/新工具、配置系统、测试、热重载 |
| [故障排查](docs/troubleshooting.md) | 常见问题排查步骤、日志分析、数据恢复 |
| [常见问题 FAQ](docs/faq.md) | 使用、配置、维护、技术问题速答 |
| [更新日志](CHANGELOG.md) | 版本变更记录 |

***

## 🏗️ 架构一览

```
NapCatQQ → adapter 适配层 → engine 编排层 → decision 决策层 → ai 驱动层 → 回复
                              managers 数据管理层 / tools 工具层 / config 基础设施
```

决策引擎采用总分架构：反馈权重 + 场景阈值 + 群动态调节 + 内容质量 + 意图融合 + 冷却管理，最终经 Sigmoid 归一化决定是否回复。详见 [docs/architecture.md](docs/architecture.md)。

***

## 📄 许可证

本项目基于 MIT 许可证开源。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

<div align="center">

**Made with ❤️ by Joha Team**

⭐ 如果这个项目对你有帮助，请给我们一个 Star！

</div>
