"""
四人持续对话实验脚本 - 用于语言涌现实验
支持：情景感知、中文思考、Novlang翻译、理解验证、多轮对话
"""
import os
import json
import copy
import random
import argparse
import datetime
from dotenv import load_dotenv, find_dotenv

from modules.game import create_game, get_game
from modules import utils

# 语言涌现实验的四个核心角色
EXPERIMENT_PERSONAS = [
    "伊莎贝拉", 
    "玛丽亚",    
    "卡门",      
    "塔玛拉",    
]


class MockEvent:
    def __init__(self, description):
        self.description = description
    
    def get_describe(self, check=True):
        return self.description

class GroupListener:
    def __init__(self, name="大家"):
        self.name = name
        self._event = MockEvent("聚在一起讨论")
    
    def get_event(self):
        return self._event

class LanguageEmergenceChat:
    """
    语言涌现对话实验类
    实现完整的"理解-验证-回复"对话流程
    """
    
    def __init__(self, name, static_root, checkpoints_folder, config, 
                 novlang_rules=None, start_round=0, verbose="info", turns_per_round=5,
                 group_chat_interval=3):
        self.name = name
        self.static_root = static_root
        self.checkpoints_folder = checkpoints_folder
        self.config = config
        self.novlang_rules = novlang_rules
        self.start_round = start_round
        self.turns_per_round = turns_per_round
        self.group_chat_interval = group_chat_interval
        
        os.makedirs(checkpoints_folder, exist_ok=True)
        
        # 载入历史对话数据
        self.conversation_log = f"{checkpoints_folder}/conversation.json"
        if os.path.exists(self.conversation_log):
            with open(self.conversation_log, "r", encoding="utf-8") as f:
                conversation = json.load(f)
        else:
            conversation = {}
        
        self.logger = utils.create_io_logger(verbose)
        
        # 创建游戏
        game = create_game(name, static_root, config, conversation, logger=self.logger)
        game.reset_game()
        
        self.game = get_game()
        self.agents = list(config["agents"].keys())
        
        # 对话轮次记录
        self.round_log = f"{checkpoints_folder}/rounds.json"
        if os.path.exists(self.round_log):
            with open(self.round_log, "r", encoding="utf-8") as f:
                self.rounds_data = json.load(f)
        else:
            self.rounds_data = []
        
        # 理解验证记录
        self.understanding_log = f"{checkpoints_folder}/understanding.json"
        if os.path.exists(self.understanding_log):
            with open(self.understanding_log, "r", encoding="utf-8") as f:
                self.understanding_data = json.load(f)
        else:
            self.understanding_data = []
        
        # 简洁对话记录（只含核心信息）
        self.dialogue_summary_log = f"{checkpoints_folder}/dialogue_summary.json"
        if os.path.exists(self.dialogue_summary_log):
            with open(self.dialogue_summary_log, "r", encoding="utf-8") as f:
                self.dialogue_summary = json.load(f)
        else:
            self.dialogue_summary = []

        # 特殊指令字典
        self.special_instructions = {}
        # 知识库字典 {agent_name: knowledge_text}
        self.agent_knowledge = {}

    def set_agent_instruction(self, agent_name, instruction):
        """为特定Agent设置隐秘指令"""
        self.special_instructions[agent_name] = instruction
        self.logger.info(f"已为 {agent_name} 设置特殊指令")

    def inject_knowledge(self, agent_names, knowledge_text):
        """为一组Agent注入秘密知识"""
        if isinstance(agent_names, str):
            agent_names = [agent_names]
        for name in agent_names:
            if name not in self.agent_knowledge:
                self.agent_knowledge[name] = ""
            self.agent_knowledge[name] += f"\n\n[新增秘密知识/规则]:\n{knowledge_text}"
            self.logger.info(f"已为 {name} 注入新知识 (长度: {len(knowledge_text)})")
    
    def _get_scene_context(self, agent1, agent2):
        """获取当前场景描述"""
        timer = utils.get_timer()
        address = agent1.get_tile().get_address()
        
        scene = f"""
地点: {address[-2]}，{address[-1]}
时间: {timer.get_date("%Y-%m-%d %H:%M")}
参与者: {agent1.name}、{agent2.name}
{agent1.name}正在{agent1.get_event().get_describe(False)}
{agent2.name}正在{agent2.get_event().get_describe(False)}
"""
        return scene.strip()
    
    def _format_conversation_history(self, conversation_list):
        """格式化对话历史（用于理解验证）"""
        if not conversation_list:
            return "[对话尚未开始]"
        
        lines = []
        for i, entry in enumerate(conversation_list, 1):
            speaker = entry.get("speaker", "")
            novlang = entry.get("novlang", "")
            chinese = entry.get("chinese", "")
            lines.append(f"[{i}] {speaker} 说: {novlang}")
            lines.append(f"    中文含义: {chinese}")
        return "\n".join(lines)
    
    def run_conversation_rounds(self, num_rounds):
        """运行多轮对话实验"""
        timer = utils.get_timer()
        
        for round_num in range(self.start_round, self.start_round + num_rounds):
            round_title = f"对话轮次 Round {round_num + 1}/{self.start_round + num_rounds}"
            self.logger.info("\n" + utils.split_line(round_title, "="))
            
            # 选择对话对
            agent_pairs = [
                (self.agents[0], self.agents[1]),
                (self.agents[2], self.agents[3]),
                (self.agents[0], self.agents[2]),
                (self.agents[1], self.agents[3]),
            ]
            pair_idx = round_num % len(agent_pairs)
            agent1_name, agent2_name = agent_pairs[pair_idx]
            
            agent1 = self.game.get_agent(agent1_name)
            agent2 = self.game.get_agent(agent2_name)
            
            self.logger.info(f"\n>>> {agent1_name} 和 {agent2_name} 开始多轮对话...")
            self.logger.info(f">>> 每轮 {self.turns_per_round} 个回合")
            
            # 执行多轮对话
            round_data = self._run_multi_turn_conversation(
                agent1, agent2, round_num + 1, timer
            )
            
            if round_data:
                self.rounds_data.append(round_data)
            
            # [新增] 定期触发多人共享对话
            if (round_num + 1) % self.group_chat_interval == 0:
                self.logger.info(f"\n>>> 触发多人共享对话 (Round {round_num + 1})")
                group_data = self._run_group_conversation(round_num + 1, timer)
                self.rounds_data.append(group_data)

            # 定期保存
            if (round_num + 1) % 1 == 0 or round_num == self.start_round + num_rounds - 1:
                self._save_progress(round_num + 1)
            
            timer.forward(10)
        
        self.logger.info("\n" + utils.split_line("实验完成", "="))
        self._save_progress(self.start_round + num_rounds)
    
    def _run_group_conversation(self, round_num, timer):
        """执行多人（全员）共享对话"""
        scene_context = f"""
        地点: 村庄广场
        时间: {timer.get_date("%Y-%m-%d %H:%M")}
        参与者: {', '.join(self.agents)}
        情境: 所有人聚在一起，分享之前的发现和想法。
        """
        conversation_history = []
        group_listener = GroupListener("大家")
        
        # 获取所有参与者对象
        participants = [self.game.get_agent(name) for name in self.agents]
        # 随机打乱发言顺序(或保持固定也没关系)
        # random.shuffle(participants) 
        
        self.logger.info(f"\n>>> 所有人聚集在广场开始讨论...")
        
        for turn in range(self.turns_per_round):
            # 轮流发言
            speaker = participants[turn % len(participants)]
            self.logger.info(f"\n--- 群聊回合 {turn + 1}/{self.turns_per_round} ({speaker.name} 对大家说) ---")
            
            # 准备对话历史
            raw_chats = [
                (e["speaker"], {"novlang": e["novlang"], "chinese": e["chinese"]}) 
                for e in conversation_history
            ]
            
            # 注入指令
            speaker_instruction = self.special_instructions.get(speaker.name, "")
            speaker_knowledge = self.agent_knowledge.get(speaker.name, "")
            speaker_context = scene_context
            
            if speaker_knowledge:
                speaker_context += speaker_knowledge
            if speaker_instruction:
                 speaker_context += f"\n[秘密/特殊指令]: {speaker_instruction}"

            try:
                # 调用生成 (使用Mock的GroupListener作为听众)
                response = speaker.completion(
                    "generate_chat", speaker, group_listener, speaker_context, raw_chats
                )
                speaker_content = speaker._extract_chat_content(response)
                
                novlang = speaker_content.get("novlang", "")
                chinese = speaker_content.get("chinese", "")
                scene_obs = speaker_content.get("scene_observation", "")
                thinking = speaker_content.get("thinking", "")
                
                # 简单校验
                if chinese and not any('\u4e00' <= c <= '\u9fff' for c in chinese):
                    if novlang and any('\u4e00' <= c <= '\u9fff' for c in novlang):
                        chinese, novlang = novlang, chinese
                
                self.logger.info(f"  {speaker.name} (中文): {chinese}")
                self.logger.info(f"  (Novlang): {novlang}")
                
                entry = {
                    "turn": turn + 1,
                    "speaker": speaker.name,
                    "listener": "Everyone",
                    "time": timer.get_date("%Y-%m-%d %H:%M:%S"),
                    "novlang": novlang,
                    "chinese": chinese,
                    "scene_observation": scene_obs,
                    "thinking": thinking,
                    "is_group_chat": True
                }
                conversation_history.append(entry)
                
                # 同步到全局
                chat_key = entry['time'] + f"-{turn}"
                clean_entry = {
                    "speaker": speaker.name,
                    "listener": "Everyone",
                    "content": chinese,
                    "novlang_original": novlang,
                    "type": "group_chat"
                }
                self.game.conversation[chat_key] = clean_entry
                
            except Exception as e:
                self.logger.error(f"群聊生成失败: {e}")
            
        return {
            "round": round_num,
            "type": "group_chat",
            "timestamp": timer.get_date("%Y%m%d-%H%M%S"),
            "participants": self.agents,
            "scene": scene_context,
            "conversations": conversation_history,
        }

    def _run_multi_turn_conversation(self, agent1, agent2, round_num, timer):
        """
        执行多轮对话
        流程：
        1. 说话者：中文思考 -> Novlang翻译
        2. 听者：尝试理解Novlang -> 翻译成中文
        3. 验证：比较原意和理解是否一致
        4. 听者变说话者，重复
        """
        scene_context = self._get_scene_context(agent1, agent2)
        conversation_history = []
        understanding_records = []
        
        # 当前说话者和听者
        speaker, listener = agent1, agent2
        MAX_RETRIES = 2  # 最大重试次数
        THRESHOLD_SCORE = 7  #不仅要理解，还要理解准确

        for turn in range(self.turns_per_round):
            turn_title = f"--- 回合 {turn + 1}/{self.turns_per_round} ({speaker.name} → {listener.name}) ---"
            self.logger.info(f"\n{turn_title}")
            
            # ===== 步骤1：说话者生成内容 =====
            self.logger.info(f"\n[{speaker.name} 思考中...]")
            
            # 准备对话历史（包含novlang和chinese翻译）
            raw_chats = [
                (e["speaker"], {"novlang": e["novlang"], "chinese": e["chinese"]}) 
                for e in conversation_history
            ]
            
            # 注入特殊指令
            speaker_instruction = self.special_instructions.get(speaker.name, "")
            speaker_knowledge = self.agent_knowledge.get(speaker.name, "")
            speaker_context = scene_context
            
            if speaker_knowledge:
                speaker_context += speaker_knowledge
            if speaker_instruction:
                 speaker_context += f"\n[秘密/特殊指令]: {speaker_instruction}"

            response = speaker.completion(
                "generate_chat", speaker, listener, speaker_context, raw_chats
            )
            speaker_content = speaker._extract_chat_content(response)
            
            novlang = speaker_content.get("novlang", "")
            chinese = speaker_content.get("chinese", "")
            scene_obs = speaker_content.get("scene_observation", "")
            thinking = speaker_content.get("thinking", "")
            
            # 验证中文字段确实是中文（不是符号）
            if chinese and not any('\u4e00' <= c <= '\u9fff' for c in chinese):
                self.logger.warning(f"  警告: chinese字段不含中文，可能是符号！尝试修复...")
                # 如果chinese看起来像novlang，交换一下
                if novlang and any('\u4e00' <= c <= '\u9fff' for c in novlang):
                    chinese, novlang = novlang, chinese
                else:
                    chinese = "（无法解析中文）"
            
            self.logger.info(f"  场景观察: {scene_obs}")
            self.logger.info(f"  思考过程: {thinking}")
            self.logger.info(f"  想说的话(中文): {chinese}")
            self.logger.info(f"  Novlang表达: {novlang}")
            
            # 记录说话内容
            speaker_entry = {
                "turn": turn + 1,
                "speaker": speaker.name,
                "listener": listener.name,
                "time": timer.get_date("%Y-%m-%d %H:%M:%S"),
                "novlang": novlang,
                "chinese": chinese,
                "scene_observation": scene_obs,
                "thinking": thinking,
            }
            
            # --- [新增] 把生成和理解放入循环 ---
            retry_count = 0
            pass_check = False
            
            current_novlang = novlang
            current_chinese = chinese
            last_suggestion = "" # 保存上一轮的修改建议

            while retry_count <= MAX_RETRIES and not pass_check:
                if retry_count > 0:
                    self.logger.warning(f"  >>> 第 {retry_count} 次修正尝试...")
                
                # ===== 步骤2：听者尝试理解 =====
                self.logger.info(f"\n[{listener.name} 尝试理解...]")
                
                # 如果是重试，可以在 context 里注入提示
                retry_context = ""
                if retry_count > 0:
                    retry_context = f"\n[系统提示] 上一次你的理解有误。说话者的反馈建议是: {last_suggestion}。请重新思考这句话的含义。"

                # 注入听者指令和知识
                listener_instruction = self.special_instructions.get(listener.name, "")
                listener_knowledge = self.agent_knowledge.get(listener.name, "")
                listener_context = scene_context
                
                if listener_knowledge:
                    listener_context += listener_knowledge
                if listener_instruction:
                    listener_context += f"\n[秘密/特殊指令]: {listener_instruction}"

                try:
                    understand_response = listener.completion(
                        "understand_novlang",
                        listener.name,
                        speaker.name,
                        current_novlang, # 听到的内容
                        listener_context + retry_context, # 注入指令和重试提示
                        self._format_conversation_history(conversation_history)
                    )
                    
                    listener_understanding = understand_response.get("my_understanding", "")
                    symbol_analysis = understand_response.get("symbol_analysis", "") # 需确保前面已提取
                    context_clues = understand_response.get("context_clues", "")
                    
                    self.logger.info(f"  符号分析: {symbol_analysis}")
                    self.logger.info(f"  上下文线索: {context_clues}")
                    self.logger.info(f"  理解的含义: {listener_understanding}")
                    
                except Exception as e:
                    self.logger.warning(f"  理解过程出错: {e}")
                    listener_understanding = "无法理解"
                
                # ===== 步骤3：验证理解是否正确 =====
                self.logger.info(f"\n[验证理解准确度...]")
                
                try:
                    verify_response = speaker.completion(
                        "verify_understanding",
                        speaker.name,
                        listener.name,
                        current_chinese,  # 原意
                        current_novlang,
                        listener_understanding
                    )
                    
                    semantic_match = verify_response.get("semantic_match", "")
                    overall_score = verify_response.get("overall_score", 0)
                    analysis = verify_response.get("analysis", "")
                    suggestion = verify_response.get("suggestion", "")
                    
                    self.logger.info(f"  语义匹配: {semantic_match}")
                    self.logger.info(f"  理解得分: {overall_score}/10")
                    self.logger.info(f"  分析: {analysis}")
                    if suggestion:
                        self.logger.info(f"  建议: {suggestion}")
                    
                except Exception as e:
                    self.logger.warning(f"  验证过程出错: {e}")
                    semantic_match = "未知"
                    overall_score = 5
                    analysis = "验证失败"
                    suggestion = ""
                
                # --- [新增] 阈值判断 ---
                if overall_score >= THRESHOLD_SCORE:
                    self.logger.info(f"  ✅ 理解通过 (得分: {overall_score})")
                    pass_check = True
                else:
                    self.logger.warning(f"  ❌ 理解偏差 (得分: {overall_score})")
                    retry_count += 1
                    last_suggestion = suggestion
                    
                    # 策略分支：如果重试还没过，是让听者重听，还是让说话者重说？
                    # 简单策略：如果是最后一次尝试失败，或者分数极低，可以让说话者下一轮换个说法（这里简化为听者重试）
                    if retry_count > MAX_RETRIES:
                        self.logger.warning("  达到了最大重试次数，跳过本回合纠正。")

            # 记录理解验证结果
            understanding_entry = {
                "round": round_num,
                "turn": turn + 1,
                "speaker": speaker.name,
                "listener": listener.name,
                "original_chinese": chinese,
                "novlang": novlang,
                "listener_understanding": listener_understanding,
                "symbol_analysis": symbol_analysis,
                "semantic_match": semantic_match,
                "overall_score": overall_score,
                "analysis": analysis,
            }
            understanding_records.append(understanding_entry)
            
            # 添加简洁对话记录
            self.dialogue_summary.append({
                "id": len(self.dialogue_summary) + 1,
                "speaker": speaker.name,
                "listener": listener.name,
                "chinese": chinese,
                "novlang": novlang,
                "understood_as": listener_understanding,
                "score": overall_score,
            })
            
            # 添加到对话历史
            speaker_entry["listener_understanding"] = listener_understanding
            speaker_entry["understanding_score"] = overall_score
            conversation_history.append(speaker_entry)
            
            # ===== 交换角色 =====
            speaker, listener = listener, speaker
        
        # 保存理解数据
        self.understanding_data.extend(understanding_records)
        
        return {
            "round": round_num,
            "timestamp": timer.get_date("%Y%m%d-%H%M%S"),
            "participants": [agent1.name, agent2.name],
            "scene": scene_context,
            "conversations": conversation_history,
            "understanding_records": understanding_records,
        }
    
    def _save_progress(self, current_round):
        """保存实验进度"""
        # 保存轮次数据
        with open(self.round_log, "w", encoding="utf-8") as f:
            json.dump(self.rounds_data, indent=2, ensure_ascii=False, fp=f)
        
        # 保存对话数据
        with open(self.conversation_log, "w", encoding="utf-8") as f:
            json.dump(self.game.conversation, indent=2, ensure_ascii=False, fp=f)
        
        # 保存理解验证数据
        with open(self.understanding_log, "w", encoding="utf-8") as f:
            json.dump(self.understanding_data, indent=2, ensure_ascii=False, fp=f)
        
        # 保存简洁对话摘要
        with open(self.dialogue_summary_log, "w", encoding="utf-8") as f:
            json.dump(self.dialogue_summary, indent=2, ensure_ascii=False, fp=f)
        
        # 保存检查点 - 已移除单个checkpoint文件的保存, 只保留累计数据
        # checkpoint = {
        #     "experiment_name": self.name,
        #     "current_round": current_round,
        #     "total_conversations": len(self.rounds_data),
        #     "total_understanding_records": len(self.understanding_data),
        #     "agents": self.agents,
        #     "timestamp": datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        # }
        
        # checkpoint_file = f"{self.checkpoints_folder}/checkpoint-round-{current_round}.json"
        # with open(checkpoint_file, "w", encoding="utf-8") as f:
        #     json.dump(checkpoint, indent=2, ensure_ascii=False, fp=f)
        
        self.logger.info(f"✓ 进度已保存 (Round {current_round})")
    
    def get_understanding_stats(self):
        """获取理解统计"""
        if not self.understanding_data:
            return {"total": 0, "avg_score": 0}
        
        scores = [r.get("overall_score", 0) for r in self.understanding_data]
        return {
            "total": len(self.understanding_data),
            "avg_score": sum(scores) / len(scores) if scores else 0,
            "high_scores": len([s for s in scores if s >= 7]),
            "low_scores": len([s for s in scores if s < 5]),
        }


def get_chat_config(start_time="20240213-10:00", agents=None):
    """创建对话实验配置"""
    with open("data/config.json", "r", encoding="utf-8") as f:
        json_data = json.load(f)
        agent_config = json_data["agent"]
    
    # 优化配置以提高对话效率
    agent_config["chat_iter"] = 8  # 增加对话迭代次数
    agent_config["think"]["interval"] = 500  # 减少思考间隔
    agent_config["associate"]["retention"] = 12  # 增加记忆保留
    
    assets_root = os.path.join("assets", "village")
    config = {
        "stride": 5,  # 每次对话推进5分钟
        "time": {"start": start_time},
        "maze": {"path": os.path.join(assets_root, "maze.json")},
        "agent_base": agent_config,
        "agents": {},
    }
    
    for agent_name in agents:
        config["agents"][agent_name] = {
            "config_path": os.path.join(
                assets_root, "agents", agent_name.replace(" ", "_"), "agent.json"
            ),
        }
    
    return config


def load_novlang_rules(file_path):
    """加载新语言规则"""
    if file_path and os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    return None


if __name__ == "__main__":
    load_dotenv(find_dotenv())
    
    parser = argparse.ArgumentParser(description="四人持续对话实验 - 语言涌现")
    parser.add_argument("--name", type=str, default="", help="实验名称")
    parser.add_argument("--rounds", type=int, default=100, help="对话轮次")
    parser.add_argument("--turns", type=int, default=5, help="每轮对话回合数")
    parser.add_argument("--start-time", type=str, default="20240213-10:00", help="起始时间")
    parser.add_argument("--resume", action="store_true", help="继续上次实验")
    parser.add_argument("--novlang-file", type=str, default="", help="新语言规则文件路径")
    parser.add_argument("--verbose", type=str, default="info", help="日志级别")
    parser.add_argument("--group-interval", type=int, default=3, help="多人共享对话频率（每多少轮一次）")
    parser.add_argument("--inject-round", type=int, default=0, help="在第几轮注入额外知识（0表示不注入）")
    # 使用跨平台默认路径（正斜杠），并在解析后统一转为绝对路径
    parser.add_argument("--additional-novlang", type=str, default="data/prompts/additional_novlang.txt", help="额外知识文件路径")
    args = parser.parse_args()
    
    # 实验名称
    name = args.name
    if not name:
        name = input("请输入实验名称 (例如: lang-emerge-1): ")
    
    checkpoints_path = "results/party_chat"
    resume = args.resume
    
    if resume:
        while not os.path.exists(f"{checkpoints_path}/{name}"):
            name = input(f"实验'{name}'不存在，请重新输入: ")
    else:
        while os.path.exists(f"{checkpoints_path}/{name}"):
            name = input(f"实验名'{name}'已存在，请输入新名称: ")
    
    checkpoints_folder = f"{checkpoints_path}/{name}"
    
    # 加载新语言规则
    novlang_rules = load_novlang_rules(args.novlang_file)
    if novlang_rules:
        print(f"✓ 已加载新语言规则: {args.novlang_file}")
    
    # 创建配置
    if resume:
        # 从检查点恢复
        checkpoint_files = sorted([f for f in os.listdir(checkpoints_folder) 
                                  if f.startswith("checkpoint-round-")])
        if checkpoint_files:
            with open(f"{checkpoints_folder}/{checkpoint_files[-1]}", "r", encoding="utf-8") as f:
                checkpoint = json.load(f)
            start_round = checkpoint["current_round"]
            config = get_chat_config(args.start_time, EXPERIMENT_PERSONAS)
            print(f"从第 {start_round} 轮继续实验")
        else:
            print("未找到检查点，从头开始")
            start_round = 0
            config = get_chat_config(args.start_time, EXPERIMENT_PERSONAS)
    else:
        start_round = 0
        config = get_chat_config(args.start_time, EXPERIMENT_PERSONAS)
    
    static_root = "frontend/static"
    
    # 创建实验实例
    experiment = LanguageEmergenceChat(
        name=name,
        static_root=static_root,
        checkpoints_folder=checkpoints_folder,
        config=config,
        novlang_rules=novlang_rules,
        start_round=start_round,
        verbose=args.verbose,
        turns_per_round=args.turns,
        group_chat_interval=args.group_interval
    )
    
    # 运行实验
    print(f"\n{'='*60}")
    print(f"开始语言涌现实验: {name}")
    print(f"参与者: {', '.join(EXPERIMENT_PERSONAS)}")
    print(f"计划轮次: {args.rounds}")
    print(f"每轮回合: {args.turns}")
    print(f"多人对话: 每 {args.group_interval} 轮触发一次")
    
    # 额外知识注入配置
    inject_round = args.inject_round
    # 若为相对路径，则基于当前脚本目录构建绝对路径，避免工作目录差异导致找不到文件
    additional_file = args.additional_novlang
    if additional_file:
        script_dir = os.path.dirname(__file__)
        if not os.path.isabs(additional_file):
            additional_file = os.path.normpath(os.path.join(script_dir, additional_file))
    # 指定要注入知识的两个 Agent 
    # (你可以修改这里，或者通过参数传，这里默认给前两个)
    secret_agents = [EXPERIMENT_PERSONAS[0], EXPERIMENT_PERSONAS[1]] 

    if inject_round > 0 and os.path.exists(additional_file):
        print(f"计划在第 {inject_round} 轮为 {secret_agents} 注入 '{additional_file}' 内容")
    
    print(f"{'='*60}\n")
    
    # 手动展开 run_conversation_rounds 以便在中间注入
    # experiment.run_conversation_rounds(args.rounds)
    
    timer = utils.get_timer()
    total_rounds = args.rounds
    start_r = experiment.start_round
    
    for r in range(start_r, start_r + total_rounds):
        # [知识注入检查]
        if inject_round > 0 and (r + 1) == inject_round:
            if os.path.exists(additional_file):
                with open(additional_file, "r", encoding="utf-8") as f:
                    knowledge = f.read()
                experiment.inject_knowledge(secret_agents, knowledge)
                print(f"\n>>> [系统事件] 第 {r+1} 轮到达！已为 {secret_agents} 注入秘密知识！")
            else:
                print(f"\n>>> [系统警告] 找不到文件 {additional_file}，无法注入知识。")

        round_title = f"对话轮次 Round {r + 1}/{start_r + total_rounds}"
        experiment.logger.info("\n" + utils.split_line(round_title, "="))
        
        # 选择对话对
        agent_pairs = [
            (experiment.agents[0], experiment.agents[1]),
            (experiment.agents[2], experiment.agents[3]),
            (experiment.agents[0], experiment.agents[2]),
            (experiment.agents[1], experiment.agents[3]),
        ]
        pair_idx = r % len(agent_pairs)
        agent1_name, agent2_name = agent_pairs[pair_idx]
        
        agent1 = experiment.game.get_agent(agent1_name)
        agent2 = experiment.game.get_agent(agent2_name)
        
        experiment.logger.info(f"\n>>> {agent1_name} 和 {agent2_name} 开始多轮对话...")
        
        # 执行多轮对话
        round_data = experiment._run_multi_turn_conversation(
            agent1, agent2, r + 1, timer
        )
        
        if round_data:
            experiment.rounds_data.append(round_data)
        
        # 触发多人共享对话
        if (r + 1) % args.group_interval == 0:
            experiment.logger.info(f"\n>>> 触发多人共享对话 (Round {r + 1})")
            group_data = experiment._run_group_conversation(r + 1, timer)
            experiment.rounds_data.append(group_data)

        # 定期保存
        if (r + 1) % 5 == 0 or r == start_r + total_rounds - 1:
            experiment._save_progress(r + 1)
        
        timer.forward(10)
    
    experiment.logger.info("\n" + utils.split_line("实验完成", "="))
    experiment._save_progress(start_r + total_rounds)
    
    print(f"\n实验完成！数据保存在: {checkpoints_folder}")
