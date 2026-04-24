<div align="center">
  <a href="https://v2.nonebot.dev/store"><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/nbp_logo.png" width="180" height="180" alt="NoneBotPluginLogo"></a>
  <br>
  <p><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/NoneBotPlugin.svg" width="240" alt="NoneBotPluginText"></p>
</div>

<div align="center">

# nonebot-plugin-whats-talk-gemini

_✨ 分析群聊记录，生成近期讨论话题的总结。 ✨_


<a href="https://github.com/hakunomiko/nonebot-plugin-whats-talk-gemini/stargazers">
        <img alt="GitHub stars" src="https://img.shields.io/github/stars/hakunomiko/nonebot-plugin-whats-talk-gemini" alt="stars">
</a>
<a href="./LICENSE">
    <img src="https://img.shields.io/github/license/hakunomiko/nonebot-plugin-whats-talk-gemini.svg" alt="license">
</a>
<a href="https://pypi.python.org/pypi/nonebot-plugin-whats-talk-gemini">
    <img src="https://img.shields.io/pypi/v/nonebot-plugin-whats-talk-gemini.svg" alt="pypi">
</a>
<img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="python">

</div>

## 📖 介绍

通过指令获取当前群聊近期讨论内容的总结，或者将群聊加入推送列表定时进行话题总结。

## 💿 安装

<details open>
<summary>使用 nb-cli 安装</summary>
在 nonebot2 项目的根目录下打开命令行, 输入以下指令即可安装

    nb plugin install nonebot-plugin-whats-talk-gemini

</details>

<details>
<summary>使用包管理器安装</summary>
在 nonebot2 项目的插件目录下, 打开命令行, 根据你使用的包管理器, 输入相应的安装命令

<details>
<summary>pip</summary>

    pip install nonebot-plugin-whats-talk-gemini
</details>
<details>
<summary>pdm</summary>

    pdm add nonebot-plugin-whats-talk-gemini
</details>
<details>
<summary>poetry</summary>

    poetry add nonebot-plugin-whats-talk-gemini
</details>
<details>
<summary>conda</summary>

    conda install nonebot-plugin-whats-talk-gemini
</details>

打开 nonebot2 项目根目录下的 `pyproject.toml` 文件, 在 `[tool.nonebot]` 部分追加写入

    plugins = ["nonebot_plugin_whats_talk_gemini"]

</details>

## ⚙️ 配置

在 nonebot2 项目的`.env`文件中添加下表中的必填配置

| 配置项 | 必填 | 默认值 | 说明 |
|:-----:|:----:|:----:|:----:|
| wt_ai_keys | 是 | 无 | [Gemini API Key](https://aistudio.google.com/app/apikey?), 可填入多个key, 格式为`["xxx","xxx"]` |
| wt_base_url | 否 | "https://generativelanguage.googleapis.com/v1beta" | API地址，兼容OpenAI格式, 可填入多个key, 格式为`["xxx","xxx"]` |
| wt_model | 否 | "gemini-flash-latest" | 总结使用的AI模型 |
| wt_thinking | 否 | None | 是否开启思考模式，None=不传递，True=开启，False=显式关闭 |
| wt_proxy | 否 | 无 | 访问Gemini使用的代理，格式为`"http://<ip>:<port>"` |
| wt_history_lens | 否 | 1000 | 总结使用的群聊条数 |
| wt_max_tokens | 否 | 2000 | 总结输出的最大字数 |
| wt_push_cron | 否 | "0 14,22 * * *" | 定时推送的时间，只支持Cron表达式 |
| wt_group_list | 否 | 无 | 定时推送的群列表 |

## 🕹️ 使用
### 指令表
| 指令 | 权限 | 需要@ | 范围 | 说明 |
|:-----:|:----:|:----:|:----:|:----:|
| 他们在聊什么/群友在聊什么 | 群员 | 否 | 群聊 | 获取当前群聊的讨论总结 |

## 🎉 鸣谢
感谢[大橘](https://github.com/zhiyu1998)提供的prompt以及[插件灵感](https://github.com/zhiyu1998/rconsole-plugin-complementary-set/blob/master/whats-talk-gemini.js)。