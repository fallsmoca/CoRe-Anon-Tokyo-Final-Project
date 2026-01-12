"""
语言涌现分析工具
用于分析四人对话实验中的Novlang符号使用模式
"""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
import argparse

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


class LanguageEmergenceAnalyzer:
    def __init__(self, rounds_file):
        self.rounds_file = Path(rounds_file)
        self.data = self._load_data()
        self.symbol_usage = Counter()
        self.operator_usage = Counter()
        self.symbol_combinations = Counter()
        self.speaker_stats = defaultdict(lambda: {
            'total_messages': 0,
            'symbol_usage': Counter(),
            'avg_symbols_per_message': 0
        })
        
    def _load_data(self):
        """加载对话数据"""
        with open(self.rounds_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def extract_symbols(self, text):
        """从文本中提取Novlang符号"""
        symbols = []
        for symbol in NOVLANG_SYMBOLS.keys():
            count = text.count(symbol)
            if count > 0:
                symbols.extend([symbol] * count)
                self.symbol_usage[symbol] += count
        
        for operator in NOVLANG_OPERATORS.keys():
            count = text.count(operator)
            if count > 0:
                self.operator_usage[operator] += count
        
        return symbols
    
    def extract_combinations(self, text):
        """提取符号组合模式（2-3个连续符号）"""
        # 提取所有符号序列
        all_symbols = ''.join(NOVLANG_SYMBOLS.keys()) + ''.join(NOVLANG_OPERATORS.keys())
        pattern = f'[{re.escape(all_symbols)}]{{2,3}}'
        combinations = re.findall(pattern, text)
        return combinations
    
    def analyze(self):
        """执行完整分析"""
        print("=" * 70)
        print("语言涌现分析报告")
        print("=" * 70)
        
        total_rounds = len(self.data)
        total_conversations = sum(len(r.get('conversations', [])) for r in self.data)
        
        print(f"\n📊 基础统计")
        print(f"  总轮次: {total_rounds}")
        print(f"  总对话数: {total_conversations}")
        
        # 分析每轮对话
        for round_data in self.data:
            for conv in round_data.get('conversations', []):
                speaker = conv.get('speaker', '')
                content = conv.get('content', '')
                
                # 提取符号
                symbols = self.extract_symbols(content)
                
                # 提取组合
                combinations = self.extract_combinations(content)
                for combo in combinations:
                    self.symbol_combinations[combo] += 1
                
                # 更新说话者统计
                self.speaker_stats[speaker]['total_messages'] += 1
                for symbol in symbols:
                    self.speaker_stats[speaker]['symbol_usage'][symbol] += 1
        
        # 计算平均值
        for speaker, stats in self.speaker_stats.items():
            if stats['total_messages'] > 0:
                total_symbols = sum(stats['symbol_usage'].values())
                stats['avg_symbols_per_message'] = total_symbols / stats['total_messages']
        
        self._print_symbol_usage()
        self._print_operator_usage()
        self._print_combinations()
        self._print_speaker_stats()
        self._print_emergence_indicators()
    
    def _print_symbol_usage(self):
        """打印符号使用频率"""
        print(f"\n🔤 基础符号使用频率 (Top 10)")
        print("-" * 70)
        for symbol, count in self.symbol_usage.most_common(10):
            meaning = NOVLANG_SYMBOLS.get(symbol, '未知')
            percentage = (count / sum(self.symbol_usage.values())) * 100
            print(f"  {symbol}  {meaning:15s}  使用次数: {count:4d}  占比: {percentage:5.2f}%")
    
    def _print_operator_usage(self):
        """打印操作符使用频率"""
        print(f"\n🔧 组合标记使用频率")
        print("-" * 70)
        for operator, count in self.operator_usage.most_common():
            meaning = NOVLANG_OPERATORS.get(operator, '未知')
            percentage = (count / sum(self.operator_usage.values())) * 100 if self.operator_usage else 0
            print(f"  {operator}  {meaning:20s}  使用次数: {count:4d}  占比: {percentage:5.2f}%")
    
    def _print_combinations(self):
        """打印常见符号组合"""
        print(f"\n🔗 高频符号组合 (Top 15)")
        print("-" * 70)
        for combo, count in self.symbol_combinations.most_common(15):
            if count >= 2:  # 只显示出现2次以上的组合
                print(f"  {combo:10s}  出现次数: {count:3d}")
    
    def _print_speaker_stats(self):
        """打印各说话者的统计"""
        print(f"\n👥 各角色统计")
        print("-" * 70)
        for speaker, stats in sorted(self.speaker_stats.items()):
            print(f"\n  {speaker}")
            print(f"    总发言数: {stats['total_messages']}")
            print(f"    平均符号数/消息: {stats['avg_symbols_per_message']:.2f}")
            print(f"    最常用符号:")
            for symbol, count in stats['symbol_usage'].most_common(5):
                meaning = NOVLANG_SYMBOLS.get(symbol, '未知')
                print(f"      {symbol} ({meaning}): {count}次")
    
    def _print_emergence_indicators(self):
        """打印语言涌现指标"""
        print(f"\n✨ 语言涌现指标")
        print("-" * 70)
        
        # 1. 符号多样性
        total_unique_symbols = len(self.symbol_usage)
        total_possible_symbols = len(NOVLANG_SYMBOLS)
        symbol_diversity = total_unique_symbols / total_possible_symbols
        print(f"  符号多样性: {symbol_diversity:.2%} ({total_unique_symbols}/{total_possible_symbols})")
        
        # 2. 组合创新度
        unique_combinations = len(self.symbol_combinations)
        print(f"  独特组合数: {unique_combinations}")
        
        # 3. 稳定组合（出现5次以上）
        stable_combos = [combo for combo, count in self.symbol_combinations.items() if count >= 5]
        print(f"  稳定组合数: {len(stable_combos)} (出现≥5次)")
        if stable_combos:
            print(f"    {', '.join(stable_combos[:10])}")
        
        # 4. 使用集中度（基尼系数的简化版）
        if self.symbol_usage:
            total_usage = sum(self.symbol_usage.values())
            top_5_usage = sum(count for _, count in self.symbol_usage.most_common(5))
            concentration = top_5_usage / total_usage
            print(f"  符号集中度: {concentration:.2%} (Top5符号占比)")
        
        # 5. 演化趋势
        if len(self.data) >= 10:
            early_rounds = self.data[:len(self.data)//2]
            late_rounds = self.data[len(self.data)//2:]
            
            early_symbols = set()
            late_symbols = set()
            
            for round_data in early_rounds:
                for conv in round_data.get('conversations', []):
                    early_symbols.update(self.extract_symbols(conv.get('content', '')))
            
            for round_data in late_rounds:
                for conv in round_data.get('conversations', []):
                    late_symbols.update(self.extract_symbols(conv.get('content', '')))
            
            new_symbols = late_symbols - early_symbols
            print(f"  新出现符号数: {len(new_symbols)} (后半期)")
            if new_symbols:
                print(f"    {', '.join(sorted(new_symbols)[:10])}")
    
    def export_timeline(self, output_file):
        """导出时间线数据（可用于可视化）"""
        timeline = []
        for round_data in self.data:
            round_num = round_data.get('round', 0)
            round_symbols = Counter()
            
            for conv in round_data.get('conversations', []):
                symbols = self.extract_symbols(conv.get('content', ''))
                round_symbols.update(symbols)
            
            timeline.append({
                'round': round_num,
                'total_symbols': sum(round_symbols.values()),
                'unique_symbols': len(round_symbols),
                'top_symbols': dict(round_symbols.most_common(5))
            })
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(timeline, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ 时间线数据已导出到: {output_file}")


def main():
    parser = argparse.ArgumentParser(description='分析语言涌现实验数据')
    parser.add_argument('rounds_file', help='rounds.json文件路径')
    parser.add_argument('--export-timeline', help='导出时间线数据到指定文件')
    args = parser.parse_args()
    
    analyzer = LanguageEmergenceAnalyzer(args.rounds_file)
    analyzer.analyze()
    
    if args.export_timeline:
        analyzer.export_timeline(args.export_timeline)


if __name__ == '__main__':
    main()
