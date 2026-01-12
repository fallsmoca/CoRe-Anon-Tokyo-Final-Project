"""
LLM输出格式诊断工具
用于测试Ollama/Qwen3模型的输出是否符合预期格式
"""

import requests
import json

def test_ollama(model="qwen3:8b-q4_K_M", base_url="http://127.0.0.1:11434/v1"):
    """测试Ollama模型的基本输出"""
    
    test_cases = [
        {
            "name": "简单是非判断",
            "prompt": "请回答：今天是星期六吗？只用'是'或'否'回答。",
            "expected": ["是", "否"]
        },
        {
            "name": "时间格式输出",
            "prompt": "通常人们早上6点左右醒来。\n\n根据上述提示，输出起床时间。只输出时间（24小时制），不要包含其他内容。\n格式要求：hh:mm\n示例：6:00",
            "expected": ["数字:数字格式"]
        },
        {
            "name": "英文是非判断",
            "prompt": "Should Alice talk to Bob? Answer only 'yes' or 'no'.",
            "expected": ["yes", "no"]
        }
    ]
    
    print("=" * 60)
    print("🔍 开始测试 Ollama 模型输出格式")
    print(f"模型: {model}")
    print(f"地址: {base_url}")
    print("=" * 60)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n【测试 {i}】{test['name']}")
        print(f"提示词: {test['prompt'][:50]}...")
        
        try:
            response = requests.post(
                url=f"{base_url}/chat/completions",
                headers={"Content-Type": "application/json"},
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": test['prompt'] + "\n/nothink"}],
                    "temperature": 0.5,
                    "stream": False,
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result and len(result["choices"]) > 0:
                    output = result["choices"][0]["message"]["content"]
                    print(f"✅ 模型输出: {repr(output)}")
                    print(f"预期格式: {test['expected']}")
                else:
                    print(f"❌ 无效响应: {result}")
            else:
                print(f"❌ HTTP错误: {response.status_code}")
                print(f"响应: {response.text}")
                
        except Exception as e:
            print(f"❌ 请求失败: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    print("\n💡 使用说明：")
    print("此工具测试Ollama模型是否能按要求格式输出")
    print("如果输出包含额外解释或格式不对，会导致'Failed to match llm output'错误\n")
    
    # 运行测试
    test_ollama()
    
    print("\n🔧 解决方案：")
    print("1. 如果输出格式不对，尝试调整prompt更明确")
    print("2. 如果输出包含额外内容，在代码中增加容错处理")
    print("3. 检查qwen3模型是否已加载：ollama list")
    print("4. 尝试其他模型：ollama run qwen2.5:7b")
