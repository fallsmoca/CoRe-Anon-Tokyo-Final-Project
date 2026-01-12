"""
语言涌现分析工具
用于分析四人对话实验中的Novlang符号使用模式
"""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
import argparse
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

# Novlang基础符号
NOVLANG_SYMBOLS = {
    '●': '存在/实体',
    '—': '线性/过程',
    '｜': '垂直/界限',
    '△': '集合/群体',
    '□': '容器/范围',
    '∟': '变化/转折',
    '⌒': '关联/连接',
    '✧': '特性/属性',
    '↔': '互动/交换',
    '⊃': '包含/归属',
    '≠': '差异/否定',
    '≈': '相似/近似',
    '○': '自然/有机',
    '╬': '人工/制造',
    '♡': '感官/情绪',
    '∝': '数量/度量',
    '⊕': '能量/活力',
    '∅': '空无/缺失',
    '∞': '永恒/持续',
    '∇': '层级/秩序',
}

NOVLANG_OPERATORS = {
    '⊂': '嵌套/限定',
    '⊗': '融合/构词',
    '‖': '谓词-论元连接',
    '·': '槽分隔符',
    '：': '解释/锚点',
    '→': '因果/承接',
}

PRAGMATIC_SYMBOLS = {
    '？': '提问',
    '！': '请求/命令',
    '✓': '接受/确认',
    '✗': '拒绝/否决',
}

# 新增符号（根据之前的prompt定义）
NEW_SYMBOLS = {
    '◀': '过去/回溯',
    '▶': '未来/预期',
    '◆': '核心/本质',
    '～': '模糊/可能',
}

NEW_OPERATORS = {
    '⇔': '相互关联/等价'
}

class LanguageEmergenceAnalyzer:
    def __init__(self, rounds_file):
        self.rounds_file = Path(rounds_file)
        self.data = self._load_data()
        self.symbol_usage = Counter()
        self.new_symbol_usage = Counter()  # 新增：专门统计新符号
        self.operator_usage = Counter()
        self.new_operator_usage = Counter()  # 新增：专门统计新操作符
        self.symbol_combinations = Counter()
        self.speaker_stats = defaultdict(lambda: {
            'total_messages': 0,
            'symbol_usage': Counter(),
            'new_symbol_usage': Counter(),  # 新增：统计每位说话者的新符号使用
            'avg_symbols_per_message': 0,
            'new_symbol_adoption_rate': 0  # 新增：新符号采用率
        })
        
    def _load_data(self):
        """加载对话数据"""
        with open(self.rounds_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def extract_symbols(self, text):
        """从文本中提取Novlang符号"""
        if not text:
            return []
        
        symbols = []
        # 提取基础符号
        for symbol in NOVLANG_SYMBOLS.keys():
            count = text.count(symbol)
            if count > 0:
                symbols.extend([symbol] * count)
                self.symbol_usage[symbol] += count
        
        # 提取新增符号
        for symbol in NEW_SYMBOLS.keys():
            count = text.count(symbol)
            if count > 0:
                symbols.extend([symbol] * count)
                self.new_symbol_usage[symbol] += count
        
        # 提取基础操作符
        for operator in NOVLANG_OPERATORS.keys():
            count = text.count(operator)
            if count > 0:
                self.operator_usage[operator] += count
        
        # 提取新增操作符
        for operator in NEW_OPERATORS.keys():
            count = text.count(operator)
            if count > 0:
                self.new_operator_usage[operator] += count
        
        return symbols
    
    def extract_combinations(self, text):
        """提取符号组合模式（2-3个连续符号）"""
        if not text:
            return []
            
        # 提取所有符号序列（包括新旧符号和操作符）
        all_symbols = (''.join(NOVLANG_SYMBOLS.keys()) + 
                      ''.join(NOVLANG_OPERATORS.keys()) +
                      ''.join(NEW_SYMBOLS.keys()) +
                      ''.join(NEW_OPERATORS.keys()))
        
        # 这个pattern匹配连续2-3个符号
        pattern = f'[{re.escape(all_symbols)}]{{2,3}}'
        combinations = re.findall(pattern, text)
        return combinations
    
    def trace_emergence(self, target, output_file=None):
        """追踪特定词汇的涌现过程 (按时间顺序)"""
        lines = []
        def log(s=""):
            print(s)
            lines.append(s)

        log("=" * 70)
        log(f"涌现追踪报告: '{target}'")
        log("=" * 70)
        
        found_count = 0
        
        for round_data in self.data:
            round_num = round_data.get('round', '?')
            conversations = round_data.get('conversations', [])
            
            for conv in conversations:
                novlang = conv.get('novlang', '')
                chinese = conv.get('chinese', '')
                speaker = conv.get('speaker', '')
                turn = conv.get('turn', '?')
                
                # Check if target is in novlang
                if target in novlang:
                    found_count += 1
                    log(f"\n[Round {round_num} | Turn {turn}] {speaker}:")
                    log(f"  Novlang: {novlang}")
                    log(f"  Chinese: {chinese}")  # Keep chinese for context
                    
                    # Highlight which part of novlang matched (optional but helpful if multiple matches)
                    # For now just confirming it is in novlang
                    # log(f"  > 匹配: Novlang")
        
        if found_count == 0:
            log(f"\n⚠ 未找到 '{target}' 的任何记录。")
        else:
            log(f"\n✓ 共找到 {found_count} 次出现。")

        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines))
                print(f"\n📁 报告已保存至: {output_file}")
            except Exception as e:
                print(f"\n❌ 保存报告失败: {e}")
    
    def visualize_frequency_trends(self, output_dir=None):
        """可视化词频、词汇组和新词随时间的变化趋势"""
        if output_dir is None:
            output_dir = self.rounds_file.parent
        
        # 准备数据：每轮的词频、词汇组和新词使用情况
        rounds = []
        symbol_freq_by_round = defaultdict(lambda: defaultdict(int))
        combination_freq_by_round = defaultdict(lambda: defaultdict(int))
        new_symbol_freq_by_round = defaultdict(lambda: defaultdict(int))
        
        for round_idx, round_data in enumerate(self.data):
            round_num = round_data.get('round', round_idx + 1)
            rounds.append(round_num)
            
            conversations = round_data.get('conversations', [])
            for conv in conversations:
                novlang_content = conv.get('novlang', '')
                
                # 统计符号使用
                for symbol in self.extract_symbols(novlang_content):
                    symbol_freq_by_round[round_num][symbol] += 1
                    
                    # 如果是新符号，单独统计
                    if symbol in NEW_SYMBOLS or symbol in NEW_OPERATORS:
                        new_symbol_freq_by_round[round_num][symbol] += 1
                
                # 统计组合使用
                for combo in self.extract_combinations(novlang_content):
                    combination_freq_by_round[round_num][combo] += 1
        
        # 获取全局前五的符号、组合和新词
        all_symbols_combined = Counter()
        for round_freq in symbol_freq_by_round.values():
            for symbol, count in round_freq.items():
                all_symbols_combined[symbol] += count
        
        all_combinations_combined = Counter()
        for round_freq in combination_freq_by_round.values():
            for combo, count in round_freq.items():
                all_combinations_combined[combo] += count
        
        all_new_symbols_combined = Counter()
        for round_freq in new_symbol_freq_by_round.values():
            for symbol, count in round_freq.items():
                all_new_symbols_combined[symbol] += count
        
        # 取前五
        top_symbols = [item[0] for item in all_symbols_combined.most_common(5)]
        top_combinations = [item[0] for item in all_combinations_combined.most_common(5)]
        top_new_symbols = [item[0] for item in all_new_symbols_combined.most_common(5)]
        
        # 如果没有足够的新词，使用所有新词
        if len(top_new_symbols) < 5 and (NEW_SYMBOLS or NEW_OPERATORS):
            all_new_symbols = list(NEW_SYMBOLS.keys()) + list(NEW_OPERATORS.keys())
            top_new_symbols = all_new_symbols[:5]
        
        # 创建可视化
        fig, axes = plt.subplots(3, 1, figsize=(12, 15))
        
        # 1. 符号频率趋势
        ax1 = axes[0]
        for symbol in top_symbols:
            freqs = [symbol_freq_by_round[round_num].get(symbol, 0) for round_num in rounds]
            ax1.plot(rounds, freqs, marker='o', label=f'{symbol}')
        
        ax1.set_title('Top 5 Symbols Frequency Over Time', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Round Number')
        ax1.set_ylabel('Frequency')
        ax1.legend(title='Symbols')
        ax1.grid(True, alpha=0.3)
        
        # 2. 组合频率趋势
        ax2 = axes[1]
        for combo in top_combinations:
            freqs = [combination_freq_by_round[round_num].get(combo, 0) for round_num in rounds]
            ax2.plot(rounds, freqs, marker='s', label=f'{combo}')
        
        ax2.set_title('Top 5 Symbol Combinations Over Time', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Round Number')
        ax2.set_ylabel('Frequency')
        ax2.legend(title='Combinations')
        ax2.grid(True, alpha=0.3)
        
        # 3. 新词频率趋势
        ax3 = axes[2]
        for symbol in top_new_symbols:
            freqs = [new_symbol_freq_by_round[round_num].get(symbol, 0) for round_num in rounds]
            ax3.plot(rounds, freqs, marker='^', label=f'{symbol}')
        
        ax3.set_title('New Symbols Frequency Over Time', fontsize=14, fontweight='bold')
        ax3.set_xlabel('Round Number')
        ax3.set_ylabel('Frequency')
        ax3.legend(title='New Symbols')
        ax3.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 保存图像
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f"frequency_trends_{timestamp}.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"\n📊 可视化图表已保存至: {output_path}")
        
        # 保存数据用于后续分析
        data_output = {
            'rounds': rounds,
            'top_symbols': top_symbols,
            'top_combinations': top_combinations,
            'top_new_symbols': top_new_symbols,
            'symbol_freq_by_round': {str(k): dict(v) for k, v in symbol_freq_by_round.items()},
            'combination_freq_by_round': {str(k): dict(v) for k, v in combination_freq_by_round.items()},
            'new_symbol_freq_by_round': {str(k): dict(v) for k, v in new_symbol_freq_by_round.items()}
        }
        
        data_file = output_dir / f"frequency_data_{timestamp}.json"
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data_output, f, indent=2, ensure_ascii=False)
        
        print(f"📁 数据文件已保存至: {data_file}")
        
        return data_output
    
    def analyze(self):
        """执行完整分析"""
        output_lines = []
        def log_func(s=""):
            print(s)
            output_lines.append(str(s))
            
        log_func("=" * 70)
        log_func("语言涌现分析报告")
        log_func("=" * 70)
        
        total_rounds = len(self.data)
        total_conversations = sum(len(r.get('conversations', [])) for r in self.data)
        
        log_func(f"\n📊 基础统计")
        log_func(f"  总轮次: {total_rounds}")
        log_func(f"  总对话数 (messages): {total_conversations}")
        
        # 分析每轮对话
        for round_idx, round_data in enumerate(self.data):
            conversations = round_data.get('conversations', [])
            for conv in conversations:
                speaker = conv.get('speaker', '')
                novlang_content = conv.get('novlang', '')
                
                # 提取符号
                symbols = self.extract_symbols(novlang_content)
                
                # 提取组合
                combinations = self.extract_combinations(novlang_content)
                for combo in combinations:
                    self.symbol_combinations[combo] += 1
                
                # 更新说话者统计
                self.speaker_stats[speaker]['total_messages'] += 1
                for symbol in symbols:
                    # 判断是否为新增符号
                    if symbol in NEW_SYMBOLS or symbol in NEW_OPERATORS:
                        self.speaker_stats[speaker]['new_symbol_usage'][symbol] += 1
                    else:
                        self.speaker_stats[speaker]['symbol_usage'][symbol] += 1
        
        # 计算平均值
        for speaker, stats in self.speaker_stats.items():
            if stats['total_messages'] > 0:
                total_symbols = sum(stats['symbol_usage'].values()) + sum(stats['new_symbol_usage'].values())
                stats['avg_symbols_per_message'] = total_symbols / stats['total_messages']
                
                # 计算新符号采用率
                total_symbol_usage = sum(stats['symbol_usage'].values()) + sum(stats['new_symbol_usage'].values())
                if total_symbol_usage > 0:
                    stats['new_symbol_adoption_rate'] = sum(stats['new_symbol_usage'].values()) / total_symbol_usage
        
        self._print_symbol_usage(log_func)
        self._print_new_symbol_usage(log_func)  # 新增：单独打印新符号统计
        self._print_operator_usage(log_func)
        self._print_combinations(log_func)
        
        # Add N-gram analysis
        self.analyze_ngrams(n=2, top_k=10, log_func=log_func)
        self.analyze_ngrams(n=3, top_k=10, log_func=log_func)
        
        self._print_speaker_stats(log_func)
        self._print_emergence_indicators(log_func)
        self._print_new_symbol_analysis(log_func)  # 新增：新符号专题分析

        # Save report
        report_file = self.rounds_file.parent / "analysis_report.txt"
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(output_lines))
            print(f"\n✅ 完整报告已保存至: {report_file}")
        except Exception as e:
            print(f"\n❌ 保存失败: {e}")
        
        # 生成可视化图表
        try:
            self.visualize_frequency_trends()
        except Exception as e:
            print(f"\n⚠ 可视化生成失败: {e}")
    
    def _print_symbol_usage(self, log_func=print):
        """打印基础符号使用频率"""
        if self.symbol_usage:
            log_func(f"\n🔤 基础符号使用频率 (Top 10)")
            log_func("-" * 70)
            for symbol, count in self.symbol_usage.most_common(10):
                meaning = NOVLANG_SYMBOLS.get(symbol, '未知')
                total_usage = sum(self.symbol_usage.values()) + sum(self.new_symbol_usage.values())
                percentage = (count / total_usage) * 100 if total_usage > 0 else 0
                log_func(f"  {symbol}  {meaning:15s}  使用次数: {count:4d}  占比: {percentage:5.2f}%")
    
    def _print_new_symbol_usage(self, log_func=print):
        """打印新增符号使用频率"""
        if self.new_symbol_usage or self.new_operator_usage:
            log_func(f"\n🆕 新增符号使用统计")
            log_func("-" * 70)
            
            # 统计新增符号
            if self.new_symbol_usage:
                log_func("  新增基础符号:")
                total_new_symbols = sum(self.new_symbol_usage.values())
                total_all_symbols = sum(self.symbol_usage.values()) + total_new_symbols
                
                for symbol, count in self.new_symbol_usage.most_common():
                    meaning = NEW_SYMBOLS.get(symbol, '未知')
                    percentage_all = (count / total_all_symbols) * 100 if total_all_symbols > 0 else 0
                    percentage_new = (count / total_new_symbols) * 100 if total_new_symbols > 0 else 0
                    log_func(f"    {symbol}  {meaning:15s}  使用次数: {count:4d}  总符号占比: {percentage_all:5.2f}%  新符号占比: {percentage_new:5.2f}%")
            
            # 统计新增操作符
            if self.new_operator_usage:
                log_func("\n  新增操作符:")
                total_new_operators = sum(self.new_operator_usage.values())
                total_all_operators = sum(self.operator_usage.values()) + total_new_operators
                
                for operator, count in self.new_operator_usage.most_common():
                    meaning = NEW_OPERATORS.get(operator, '未知')
                    percentage_all = (count / total_all_operators) * 100 if total_all_operators > 0 else 0
                    log_func(f"    {operator}  {meaning:20s}  使用次数: {count:4d}  总操作符占比: {percentage_all:5.2f}%")
    
    def _print_operator_usage(self, log_func=print):
        """打印操作符使用频率"""
        if self.operator_usage:
            log_func(f"\n🔧 基础组合标记使用频率")
            log_func("-" * 70)
            total_operators = sum(self.operator_usage.values()) + sum(self.new_operator_usage.values())
            for operator, count in self.operator_usage.most_common():
                meaning = NOVLANG_OPERATORS.get(operator, '未知')
                percentage = (count / total_operators) * 100 if total_operators > 0 else 0
                log_func(f"  {operator}  {meaning:20s}  使用次数: {count:4d}  占比: {percentage:5.2f}%")
    
    def _print_combinations(self, log_func=print):
        """打印常见符号组合"""
        if self.symbol_combinations.most_common(15):
            for combo, count in self.symbol_combinations.most_common(15):
                if count >= 2:  # 只显示出现2次以上的组合
                    # 标记包含新符号的组合
                    has_new_symbol = any(symbol in combo for symbol in NEW_SYMBOLS.keys()) or any(operator in combo for operator in NEW_OPERATORS.keys())
                    new_marker = "[新]" if has_new_symbol else "    "
                    log_func(f"  {combo:10s} {new_marker} 出现次数: {count:3d}")
        else:
            log_func("  暂无足够数据发现高频组合")

    def analyze_ngrams(self, n=2, top_k=10, log_func=print):
        """分析N-gram (N元语法) 涌现情况"""
        from collections import Counter, defaultdict
        
        # Valid symbols set for filtering
        valid_chars = set()
        valid_chars.update(NOVLANG_SYMBOLS.keys())
        valid_chars.update(NOVLANG_OPERATORS.keys())
        valid_chars.update(NEW_SYMBOLS.keys())
        valid_chars.update(NEW_OPERATORS.keys())
        valid_chars.update(PRAGMATIC_SYMBOLS.keys())

        # 1. 收集所有轮次的 Novlang Token
        # tokens_per_round = { round_num: [tokens...] }
        tokens_per_round = defaultdict(list)
        all_ngrams = Counter()
        ngrams_per_round = defaultdict(Counter)

        for round_data in self.data:
            round_num = round_data.get('round', 0)
            
            # 提取本轮所有 token
            round_tokens = []
            for conv in round_data.get('conversations', []):
                novlang = conv.get('novlang', '')
                if not novlang: continue
                
                # 简单分词: 暂时按字符或者特定分隔符分词
                # 假设 Novlang 以 · 或空格分隔，或者直接分析字符流
                # 这里我们采用一种混合策略：保留完整符号，忽略纯标点（除了Novlang操作符）
                
                # 方法 A: 字符级 N-gram (适合紧凑的 Novlang)
                # 过滤掉非符号字符 (这里假设所有感兴趣的都在定义的字典里，或者是汉字/单词)
                # 但混合了中文词汇的 Novlang 比较复杂，我们先试着按 '·' 分割
                
                # 尝试分割:
                # 1. 替换掉一些干扰字符
                clean_text = novlang.replace('\n', ' ').strip()
                # 2. 按 '·' 分割成 "词" (Token)
                raw_tokens = [t.strip() for t in clean_text.split('·') if t.strip()]

                # 3. 过滤汉字和无关字符，只保留有效符号
                filtered_tokens = []
                for t in raw_tokens:
                    # Keep only chars in valid_chars
                    cleaned = "".join([c for c in t if c in valid_chars])
                    if cleaned:
                        filtered_tokens.append(cleaned)
                
                round_tokens.extend(filtered_tokens)

            tokens_per_round[round_num] = round_tokens

            # 生成 N-grams
            if len(round_tokens) >= n:
                grams = [tuple(round_tokens[i:i+n]) for i in range(len(round_tokens)-n+1)]
                ngrams_per_round[round_num].update(grams)
                all_ngrams.update(grams)
        
        log_func("\n" + "="*70)
        log_func(f"🧮 {n}-gram (N元组) 涌现分析")
        log_func("="*70)

        if not all_ngrams:
            log_func("  暂无足够数据进行 N-gram 分析")
            return

        # 2. 找出高频 N-gram
        top_grams = all_ngrams.most_common(top_k)
        
        log_func(f"\n🏆 全局 Top {top_k} {n}-grams:")
        for gram, count in top_grams:
            log_func(f"  {' · '.join(gram)} (Count: {count})")

        # 3. 计算涌现指标 (简单版: 突增检测)
        # 定义: 在前 X 轮很少出现，但在后 Y 轮频繁出现
        log_func(f"\n🚀 潜在的涌现搭配 (Emerging Collocations):")
        log_func(f"  (筛选标准: 前半程出现率 < 20% 且 后半程出现次数 >= 3)")
        
        sorted_rounds = sorted(tokens_per_round.keys())
        if len(sorted_rounds) < 2:
            log_func("  轮次过少，无法计算涌现趋势")
            return

        mid_point = len(sorted_rounds) // 2
        early_rounds = sorted_rounds[:mid_point]
        late_rounds = sorted_rounds[mid_point:]
        
        # 遍历所有出现过至少 3 次的 ngram
        potential_emergence = []
        for gram, total_count in all_ngrams.items():
            if total_count < 3: continue
            
            count_early = sum(ngrams_per_round[r][gram] for r in early_rounds)
            count_late = sum(ngrams_per_round[r][gram] for r in late_rounds)
            
            # 简单指标: 后期占比
            late_ratio = count_late / total_count
            
            if late_ratio > 0.8 and count_early <= 1: # 80% 以上出现在后半程，且前半程几乎没有
                potential_emergence.append({
                    'gram': gram,
                    'count': total_count,
                    'early': count_early,
                    'late': count_late
                })
        
        # 按总次数排序
        potential_emergence.sort(key=lambda x: x['count'], reverse=True)
        
        if potential_emergence:
            for item in potential_emergence:
                gram_str = ' · '.join(item['gram'])
                log_func(f"  🔥 {gram_str}")
                log_func(f"     Total: {item['count']} | Early Rounds: {item['early']} | Late Rounds: {item['late']}")
        else:
            log_func("  未检测到明显的涌现模式 (根据当前阈值)")

    def _print_speaker_stats(self, log_func=print):
        """打印各说话者的统计"""
        log_func(f"\n👥 各角色统计")
        log_func("-" * 70)
        for speaker, stats in sorted(self.speaker_stats.items()):
            log_func(f"\n  {speaker}")
            log_func(f"    总发言数: {stats['total_messages']}")
            log_func(f"    平均符号数/消息: {stats['avg_symbols_per_message']:.2f}")
            log_func(f"    新符号采用率: {stats['new_symbol_adoption_rate']:.2%}")
            
            # 最常用基础符号
            if stats['symbol_usage']:
                log_func(f"    最常用基础符号:")
                for symbol, count in stats['symbol_usage'].most_common(3):
                    meaning = NOVLANG_SYMBOLS.get(symbol, '未知')
                    log_func(f"      {symbol} ({meaning}): {count}次")
            
            # 最常用新增符号
            if stats['new_symbol_usage']:
                log_func(f"    最常用新增符号:")
                for symbol, count in stats['new_symbol_usage'].most_common(3):
                    meaning = NEW_SYMBOLS.get(symbol, NEW_OPERATORS.get(symbol, '未知'))
                    log_func(f"      {symbol} ({meaning}): {count}次")
    
    def _print_new_symbol_analysis(self, log_func=print):
        """新增：专题分析新符号使用情况"""
        log_func(f"\n📈 新增符号专题分析")
        log_func("-" * 70)
        
        # 1. 新符号总体采用情况
        total_old_symbols = sum(self.symbol_usage.values())
        total_new_symbols = sum(self.new_symbol_usage.values())
        total_all_symbols = total_old_symbols + total_new_symbols
        
        if total_all_symbols > 0:
            new_symbol_percentage = (total_new_symbols / total_all_symbols) * 100
            log_func(f"  新符号总体采用率: {new_symbol_percentage:.2f}% ({total_new_symbols}/{total_all_symbols})")
        
        # 2. 新符号在各轮次中的使用趋势
        log_func(f"\n  新符号使用时间线:")
        new_symbols_by_round = []
        for round_idx, round_data in enumerate(self.data):
            round_new_symbols = 0
            round_all_symbols = 0
            
            for conv in round_data.get('conversations', []):
                novlang_content = conv.get('novlang', '')
                # 统计本轮所有符号
                for symbol in NOVLANG_SYMBOLS.keys():
                    round_all_symbols += novlang_content.count(symbol)
                for symbol in NEW_SYMBOLS.keys():
                    count = novlang_content.count(symbol)
                    round_all_symbols += count
                    round_new_symbols += count
            
            if round_all_symbols > 0:
                percentage = (round_new_symbols / round_all_symbols) * 100
                new_symbols_by_round.append(percentage)
                log_func(f"    第{round_idx+1}轮: {percentage:.1f}% ({round_new_symbols}/{round_all_symbols})")
        
        # 3. 新符号的组合能力
        log_func(f"\n  新符号组合能力:")
        new_symbol_combinations = []
        for combo, count in self.symbol_combinations.items():
            # 检查组合是否包含新符号
            has_new_symbol = any(symbol in combo for symbol in NEW_SYMBOLS.keys()) or any(operator in combo for operator in NEW_OPERATORS.keys())
            if has_new_symbol and count >= 2:
                new_symbol_combinations.append((combo, count))
        
        if new_symbol_combinations:
            new_symbol_combinations.sort(key=lambda x: x[1], reverse=True)
            log_func(f"    包含新符号的稳定组合 ({len(new_symbol_combinations)}个):")
            for combo, count in new_symbol_combinations[:5]:
                log_func(f"      {combo}: {count}次")
        else:
            log_func(f"    暂无包含新符号的稳定组合")
    
    def _print_emergence_indicators(self, log_func=print):
        """打印语言涌现指标"""
        log_func(f"\n✨ 语言涌现指标")
        log_func("-" * 70)
        
        # 1. 符号多样性（包括新旧符号）
        all_symbols_dict = {**NOVLANG_SYMBOLS, **NEW_SYMBOLS}
        total_unique_symbols = len(self.symbol_usage) + len(self.new_symbol_usage)
        total_possible_symbols = len(all_symbols_dict)
        symbol_diversity = total_unique_symbols / total_possible_symbols
        log_func(f"  符号多样性: {symbol_diversity:.2%} ({total_unique_symbols}/{total_possible_symbols})")
        
        # 2. 新符号多样性
        total_unique_new_symbols = len(self.new_symbol_usage)
        total_possible_new_symbols = len(NEW_SYMBOLS)
        new_symbol_diversity = total_unique_new_symbols / total_possible_new_symbols if total_possible_new_symbols > 0 else 0
        log_func(f"  新符号多样性: {new_symbol_diversity:.2%} ({total_unique_new_symbols}/{total_possible_new_symbols})")
        
        # 3. 组合创新度
        unique_combinations = len(self.symbol_combinations)
        log_func(f"  独特组合数: {unique_combinations}")
        
        # 4. 稳定组合（出现5次以上）
        stable_combos = [combo for combo, count in self.symbol_combinations.items() if count >= 5]
        log_func(f"  稳定组合数: {len(stable_combos)} (出现≥5次)")
        if stable_combos:
            # 标记包含新符号的稳定组合
            stable_with_new = [combo for combo in stable_combos if 
                               any(symbol in combo for symbol in NEW_SYMBOLS.keys()) or 
                               any(operator in combo for operator in NEW_OPERATORS.keys())]
            log_func(f"    其中包含新符号: {len(stable_with_new)}个")
            if stable_combos:
                log_func(f"    {', '.join(stable_combos[:10])}")
        
        # 5. 使用集中度（基尼系数的简化版）
        all_usage = dict(self.symbol_usage)
        all_usage.update(self.new_symbol_usage)
        if all_usage:
            total_usage = sum(all_usage.values())
            top_5_usage = sum(count for _, count in Counter(all_usage).most_common(5))
            concentration = top_5_usage / total_usage
            log_func(f"  符号集中度: {concentration:.2%} (Top5符号占比)")
        
        # 6. 演化趋势（新符号的出现情况）
        if len(self.data) >= 4:  # 至少有4轮数据
            early_rounds = self.data[:len(self.data)//2]
            late_rounds = self.data[len(self.data)//2:]
            
            early_symbols = set()
            late_symbols = set()
            
            for round_data in early_rounds:
                for conv in round_data.get('conversations', []):
                    novlang = conv.get('novlang', '')
                    # 提取所有符号（包括新符号）
                    for symbol in all_symbols_dict.keys():
                        if symbol in novlang:
                            early_symbols.add(symbol)
            
            for round_data in late_rounds:
                for conv in round_data.get('conversations', []):
                    novlang = conv.get('novlang', '')
                    for symbol in all_symbols_dict.keys():
                        if symbol in novlang:
                            late_symbols.add(symbol)
            
            new_symbols = late_symbols - early_symbols
            lost_symbols = early_symbols - late_symbols
            
            # 只关注新增符号中的新出现
            new_symbols_in_new_set = [s for s in new_symbols if s in NEW_SYMBOLS or s in NEW_OPERATORS]
            
            log_func(f"  新出现符号数: {len(new_symbols)} (后半期)")
            log_func(f"  其中新增符号: {len(new_symbols_in_new_set)}个")
            if new_symbols_in_new_set:
                log_func(f"    {', '.join(sorted(new_symbols_in_new_set))}")
            
            if lost_symbols:
                log_func(f"  消失符号数: {len(lost_symbols)} (前半期有，后半期无)")
                if len(lost_symbols) <= 10:
                    log_func(f"    {', '.join(sorted(lost_symbols))}")
    
    def export_timeline(self, output_file):
        """导出时间线数据（可用于可视化）"""
        timeline = []
        for round_data in self.data:
            round_num = round_data.get('round', 0)
            round_symbols = Counter()
            round_new_symbols = Counter()
            
            for conv in round_data.get('conversations', []):
                novlang_content = conv.get('novlang', '')
                
                # 统计基础符号
                for symbol in NOVLANG_SYMBOLS.keys():
                    count = novlang_content.count(symbol)
                    if count > 0:
                        round_symbols[symbol] += count
                
                # 统计新增符号
                for symbol in NEW_SYMBOLS.keys():
                    count = novlang_content.count(symbol)
                    if count > 0:
                        round_new_symbols[symbol] += count
            
            timeline.append({
                'round': round_num,
                'total_symbols': sum(round_symbols.values()) + sum(round_new_symbols.values()),
                'total_new_symbols': sum(round_new_symbols.values()),
                'unique_symbols': len(round_symbols) + len(round_new_symbols),
                'unique_new_symbols': len(round_new_symbols),
                'new_symbol_ratio': sum(round_new_symbols.values()) / (sum(round_symbols.values()) + sum(round_new_symbols.values())) if (sum(round_symbols.values()) + sum(round_new_symbols.values())) > 0 else 0,
                'top_symbols': dict(round_symbols.most_common(3)),
                'top_new_symbols': dict(round_new_symbols.most_common(3))
            })
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(timeline, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ 时间线数据已导出到: {output_file}")


def main():
    parser = argparse.ArgumentParser(description='分析语言涌现实验数据')
    parser.add_argument('rounds_file', help='rounds.json文件路径')
    parser.add_argument('--export-timeline', help='导出时间线数据到指定文件')
    parser.add_argument('--trace', help='追踪特定词汇的涌现过程（按时间顺序输出）')
    parser.add_argument('--visualize', action='store_true', help='生成可视化图表')
    args = parser.parse_args()
    
    analyzer = LanguageEmergenceAnalyzer(args.rounds_file)
    
    if args.trace:
        # 自动生成追踪报告文件名
        trace_file = Path(args.rounds_file).parent / f"trace_{args.trace}.txt"
        analyzer.trace_emergence(args.trace, trace_file)
    elif args.visualize:
        # 只生成可视化图表
        analyzer.visualize_frequency_trends()
    else:
        analyzer.analyze()
    
    if args.export_timeline:
        analyzer.export_timeline(args.export_timeline)


if __name__ == '__main__':
    main()