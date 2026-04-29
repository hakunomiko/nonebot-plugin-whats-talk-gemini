from typing import List, Optional

from pydantic import BaseModel, Extra


class Config(BaseModel, extra=Extra.ignore):
    wt_ai_keys: List[str] = []  # AI 接口密钥列表
    wt_base_url: str = "https://generativelanguage.googleapis.com/v1beta" #OpenAI 兼容格式base_url
    wt_model: str = "gemini-flash-latest"  # AI 模型名称，指向特定型号变体的最新版本
    wt_proxy: str = ""  # 代理设置
    wt_history_lens: int = 1000  # 获取历史消息的数量
    wt_max_tokens: int = 2000
    wt_push_cron: str = "0 14,22 * * *"  # 定时任务的 cron 表达式
    wt_group_list: List[int] = []  # 定时推送的群组列表
    wt_thinking: Optional[bool] = None  # None=不传递，True=开启，False=显式关闭

    
