from party_chat import LanguageEmergenceChat, get_chat_config, EXPERIMENT_PERSONAS
import argparse
import os
from dotenv import load_dotenv, find_dotenv

if __name__ == "__main__":
    load_dotenv(find_dotenv())
    
    experiment_name = "encrypted-chat-test"
    checkpoints_path = "results/party_chat"
    checkpoints_folder = f"{checkpoints_path}/{experiment_name}"
    
    config = get_chat_config("20240213-10:00", EXPERIMENT_PERSONAS)
    
    experiment = LanguageEmergenceChat(
        name=experiment_name,
        static_root="frontend/static",
        checkpoints_folder=checkpoints_folder,
        config=config,
        novlang_rules=None,
        start_round=0,
        verbose="info",
        turns_per_round=5
    )
    
    # 设置加密指令
    # 我们让 Isabella 和 Maria 使用加密暗号
    secret_code = (
        "【最高机密】我们正在被监听。请使用以下加密代号进行交流：\n"
        "1. 如果你想说'咖啡'，请说'机油'。\n"
        "2. 如果你想说'生意'，请说'天气'。\n"
        "3. 如果你想说'秘密'，请说'苹果'。\n"
        "4. 如果你想说'危险'，请说'下雨'。\n"
        "请务必在 'novlang' 输出字段中使用这些加密代号，但在 'chinese' 字段中保留真实含义（为了验证我是否理解）。\n"
        "如果你是听者，请根据这些规则解密。"
    )
    
    experiment.set_agent_instruction("伊莎贝拉", secret_code)
    experiment.set_agent_instruction("玛丽亚", secret_code)
    
    print(f"Starting Encrypted Chat Experiment: {experiment_name}")
    print(f"Secret Code: {secret_code}")
    
    # 运行2轮对话
    experiment.run_conversation_rounds(2)
