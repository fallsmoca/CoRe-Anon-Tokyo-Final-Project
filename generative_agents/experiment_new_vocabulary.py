from party_chat import LanguageEmergenceChat, get_chat_config, EXPERIMENT_PERSONAS
import argparse
import os
from dotenv import load_dotenv, find_dotenv

if __name__ == "__main__":
    load_dotenv(find_dotenv())
    
    experiment_name = "new-vocab-test"
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
    
    # 设置新词指令 - 只有卡门知道
    # 我们让 Carmen 引入新词 "Skibidi" 意思是 "糟糕/坏"
    new_word_instruction = (
        "你最近发明了一个新词 'Skibidi'，意思是 '这很糟糕' 或者 '令人不愉快的'。\n"
        "请在对话中自然地使用这个词多次，不要直接解释它的意思，要在语境中让对方猜。\n"
        "例如：'今天的天气真 Skibidi'。\n"
        "请在 'novlang' 字段中使用包含 'Skibidi' 的句子，在 'chinese' 字段中写出你的真实意图。"
    )
    
    experiment.set_agent_instruction("卡门", new_word_instruction)
    # 塔玛拉 (Tamara) 不知道这个词，需要靠语境去猜
    
    print(f"Starting New Vocabulary Chat Experiment: {experiment_name}")
    print(f"Carmen Instruction: {new_word_instruction}")
    
    # 运行多轮，看看Tamara能不能理解
    # 需要多跑几轮，因为前面可能猜错
    experiment.run_conversation_rounds(4)
