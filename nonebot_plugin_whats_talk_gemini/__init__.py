import asyncio

import httpx
from nonebot import get_bots, get_plugin_config, on_command, require
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.exception import FinishedException
from nonebot.log import logger
from nonebot.plugin import PluginMetadata
from nonebot.rule import is_type

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler

from .config import Config

# 插件元数据
__plugin_meta__ = PluginMetadata(
    name="他们在聊什么",
    description="分析群聊记录，生成近期讨论话题的总结。",
    usage=(
        '发送指令"他们在聊什么"或"群友在聊什么"以获取当前群聊的讨论总结。'
        '插件会定期自动推送群聊讨论总结，推送时间可配置。'
    ),
    type="application",
    homepage="https://github.com/hakunomiko/nonebot-plugin-whats-talk-gemini",
    config=Config,
    supported_adapters={"~onebot.v11"},
)


# 加载插件配置
plugin_config = get_plugin_config(Config)
wt_api_keys = plugin_config.wt_ai_keys
wt_base_url = plugin_config.wt_base_url
if not wt_api_keys:
    raise ValueError("配置文件中未提供 API Key 列表。")
wt_model_name = plugin_config.wt_model
wt_proxy = plugin_config.wt_proxy
wt_history_lens = plugin_config.wt_history_lens
wt_max_tokens = plugin_config.wt_max_tokens
wt_push_cron = plugin_config.wt_push_cron
wt_group_list = plugin_config.wt_group_list
wt_thinking = plugin_config.wt_thinking


# 注册事件响应器
whats_talk = on_command(
    "他们在聊什么",
    aliases={"群友在聊什么"},
    priority=5,
    rule=is_type(GroupMessageEvent),
    block=True,
)


# 处理命令
@whats_talk.handle()
async def handle_whats_talk(bot: Bot, event: GroupMessageEvent):
    group_id = event.group_id
    try:
        messages, first_time, last_time = await get_history_chat(bot, group_id)
        member_count = await get_group_member(bot, group_id)
        if not messages:
            await whats_talk.finish("未能获取到聊天记录。")
        summary = await chat_with_gemini(messages, member_count, first_time, last_time)
        if not summary:
            await whats_talk.finish("生成聊天总结失败，请稍后再试。")
        await bot.send_group_forward_msg(
            group_id=group_id,
            messages=[
                {
                    "type": "node",
                    "data": {
                        "name": "群聊总结",
                        "uin": bot.self_id,
                        "content": summary,
                    },
                }
            ],
        )
    except FinishedException:
        raise
    except Exception as e:
        logger.error(f"命令执行过程中发生错误: {e!s}")
        await whats_talk.finish(f"命令执行过程中发生错误，错误信息: {e!s}")


# 获取群成员数量
async def get_group_member(bot: Bot, group_id: int) -> int:
    try:
        members = await bot.get_group_member_list(group_id=group_id)
        return len(members)
    except Exception as e:
        logger.error(f"获取群成员列表失败: {e!s}")
        return 0


# 获取群聊记录
async def get_history_chat(bot: Bot, group_id: int):
    messages = []
    first_time = None
    last_time = None
    try:
        history = await bot.get_group_msg_history(
            group_id=group_id,
            count=wt_history_lens,
        )
        logger.debug(history)
        for message in history["messages"]:
            sender = message["sender"]["card"] or message["sender"]["nickname"]
            text_messages = []
            if isinstance(message["message"], list):
                text_messages = [
                    msg["data"]["text"]
                    for msg in message["message"]
                    if msg["type"] == "text"
                ]
            elif isinstance(message["message"], str) and "CQ:" not in message["message"]:
                text_messages = [message["message"]]
            if text_messages:
                messages.append(f"{sender}: {''.join(text_messages)}")
                ts = message.get("time")
                if ts:
                    if first_time is None:
                        first_time = ts
                    last_time = ts
    except Exception as e:
        logger.error(f"获取聊天记录失败: {e!s}")
        raise Exception(f"获取聊天记录失败,错误信息: {e!s}")
    logger.debug(messages)
    return messages, first_time, last_time


# 调用 AI 接口生成聊天总结
async def chat_with_gemini(messages, member_count, first_time=None, last_time=None):
    from datetime import datetime

    # 构造时间信息
    time_info = ""
    if first_time and last_time:
        first_str = datetime.fromtimestamp(first_time).strftime("%m-%d %H:%M")
        last_str = datetime.fromtimestamp(last_time).strftime("%m-%d %H:%M")
        time_info = f"{first_str} ~ {last_str}"
    else:
        time_info = "未知"

    # 昵称压缩 3位十六进制,rongliang 4096
    name_to_code = {}
    code_to_name = {}
    code_idx = 0
    compressed_messages = []

    for msg in messages:
        if ": " in msg:
            name, content = msg.split(": ", 1)
            if name not in name_to_code:
                code = f"{code_idx:03X}"
                name_to_code[name] = code
                code_to_name[code] = name
                code_idx += 1
            compressed_messages.append(f"{name_to_code[name]}: {content}")
        else:
            compressed_messages.append(msg)

    logger.debug(f"昵称映射: {code_to_name}")
    logger.debug(
        f"原始 {sum(len(m) for m in messages)} 字符, "
        f"压缩后 {sum(len(m) for m in compressed_messages)} 字符, "
        f"用户 {len(code_to_name)} 人"
    )

    prompt = (
        f"""你是群聊总结专家。请严格按以下要求输出：

        采集时间段：{time_info}
        群总人数：{member_count}人
        聊天记录中的000、001等是用户代号，输出时请将代号还原为真实昵称，还原映射如下：
        {chr(10).join(f"{code} = {name}" for code, name in code_to_name.items())}

        要求：
        1. 纯文本输出，禁止使用任何markdown符号（#、*、-、|、>、`等）。
        2. 总字数控制在{wt_max_tokens}字以内。
        3. 开头先写整体总结（3-4句话概括本次群聊主题、氛围、突出特点）。
        4. 尽可能多地归纳话题，不要遗漏，哪怕某个话题只有两三个人聊了几句也要单独列出。
        5. 每个话题要详细展开，列出讨论的来龙去脉、不同观点、关键转折点。
        6. 结尾输出互动评价（活跃人数比例、话题数量、整体氛围，简短说明即可）。
        7. 每个【】标题前面空一行。

        输出格式：

        【采集时间】{time_info}

        【整体总结】
        （3-4句话概括本次群聊的主题、整体氛围和突出特点）

        【话题1】标题
        主要内容：详细描述讨论的起因、经过、不同观点和结论，至少3-4句话。
        关键用户：...

        【话题2】标题
        主要内容：详细描述讨论的起因、经过、不同观点和结论，至少3-4句话。
        关键用户：...

        【话题3】标题
        主要内容：...
        关键用户：...

        （话题数量不限，有多少内容就总结多少个）

        【互动评价】
        活跃X人（占群总人数X%），话题X个，整体氛围..."""
    )



    data = {
        "model": wt_model_name,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": "\n".join(compressed_messages)},
        ],
    }

    for wt_api_key in wt_api_keys:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {wt_api_key}",
        }

        if "googleapis.com" in wt_base_url:
            url = f"{wt_base_url}/models/{wt_model_name}:generateContent?key={wt_api_key}"
            headers.pop("Authorization", None)
            data = {
                "contents": [
                    {"parts": [{"text": prompt}], "role": "user"},
                    {"parts": [{"text": "\n".join(compressed_messages)}], "role": "user"},
                ]
            }

        else:
            url = f"{wt_base_url}/chat/completions"
            data = {
                "model": wt_model_name,
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": "\n".join(compressed_messages)},
                ],
            }
            
            if wt_thinking is not None:
                data["reasoning_effort"] = "high"
                data["extra_body"] = {"thinking": {"type": "enabled" if wt_thinking else "disabled"}}

        try:
            async with httpx.AsyncClient(
                proxy=wt_proxy if wt_proxy else None,
                timeout=300,
            ) as client:
                response = await client.post(url, headers=headers, json=data)
                response.raise_for_status()
                result = response.json()

                if "choices" in result:
                    content = result["choices"][0]["message"]["content"]
                elif "candidates" in result:
                    content = "".join(
                        item.get("text", "")
                        for item in result["candidates"][0]
                        .get("content", {})
                        .get("parts", [])
                    )
                else:
                    logger.error(f"未知的响应格式: {result}")
                    return None

                logger.debug(f"原始输出: {content}")

                # 还原昵称（按长度降序，避免短码误替换）
                for code in sorted(code_to_name, key=len, reverse=True):
                    content = content.replace(code, code_to_name[code])

                logger.debug(f"还原后输出: {content}")
                return content

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning(f"API Key {wt_api_key} 已超出限制，切换到下一个。")
                continue
            else:
                logger.error(f"调用 AI 接口失败: {e!s}")
                raise Exception(f"调用 AI 接口失败，错误信息: {e!s}")
        except Exception as e:
            logger.error(f"发生预料之外的错误: {e!s}")
            raise Exception(f"发生预料之外的错误，错误信息: {e!s}")

    raise Exception("所有 API Key 均超出限制或调用失败。")



# 解析 cron 表达式
def parse_cron_expression(cron: str):
    fields = cron.split()
    if len(fields) != 5:
        raise ValueError(f"无效的 cron 表达式: {cron}")
    minute, hour, day, month, day_of_week = fields
    return {
        "minute": minute,
        "hour": hour,
        "day": day,
        "month": month,
        "day_of_week": day_of_week,
    }


# 定时任务
@scheduler.scheduled_job("cron", id="push_whats_talk", **parse_cron_expression(wt_push_cron))
async def push_whats_talk():
    bots = get_bots()
    for bot in bots:
        if isinstance(bot, Bot):
            for group_id in wt_group_list:
                try:
                    messages, first_time, last_time = await get_history_chat(bot, group_id)
                    member_count = await get_group_member(bot, group_id)
                    if not messages:
                        await bot.send_group_msg(group_id=group_id, message="未能获取到聊天记录。")
                        continue
                    summary = await chat_with_gemini(messages, member_count, first_time, last_time)
                    if not summary:
                        await bot.send_group_msg(group_id=group_id, message="生成聊天总结失败，请稍后再试。")
                        continue
                    await bot.send_group_forward_msg(
                        group_id=group_id,
                        messages=[
                            {
                                "type": "node",
                                "data": {
                                    "name": "群聊总结",
                                    "uin": bot.self_id,
                                    "content": summary,
                                },
                            }
                        ],
                    )
                except Exception as e:
                    logger.error(f"定时任务处理群 {group_id} 时发生错误: {e!s}")
                    await bot.send_group_msg(
                        group_id=group_id,
                        message=f"命令执行过程中发生错误，错误信息: {e!s}",
                    )
                await asyncio.sleep(2)
