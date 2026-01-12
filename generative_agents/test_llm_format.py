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
            "name": "JSON格式输出 (对话生成模拟)",
            "prompt": """
你是一个正在进行对话的Agent。请根据以下要求输出 JSON 格式的回复。

【要求】
1. 返回必须是合法的 JSON 格式。
2. 包含 "thought" (思考过程), "novlang" (符号语言), "chinese" (中文翻译) 三个字段。
3. "thought" 简述你的意图。
4. "novlang" 使用符号 "●" 和 "—" 表示 "你好"。
5. "chinese" 是 "你好" 的中文。

示例：
{
    "thought": "我想向对方打招呼",
    "novlang": "● —",
    "chinese": "你好"
}

请输出：
""",
            "expected": ["JSON: {thought, novlang, chinese}"]
        },
        {
            "name": "复杂符号处理",
            "prompt": """
请将这句话翻译成 JSON 格式：
"我看到三个苹果。"

要求输出字段：
- novlang: 使用 "●" (实体) 和 "3" (数字)。
- chinese: "我看到三个苹果"

请只输出 JSON。
""",
            "expected": ["JSON with mixed symbols"]
        }
    ]
    
    print("=" * 60)
    print("🔍 开始测试 LLM 模型输出格式")
    
    # 尝试从 config.json 读取配置
    try:
        with open("data/config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
            llm_config = config.get("agent", {}).get("think", {}).get("llm", {})
            model = llm_config.get("model", model)
            base_url = llm_config.get("base_url", base_url)
            api_key = llm_config.get("api_key", "EMPTY")
    except Exception as e:
        print(f"⚠ 读取 config.json 失败，使用默认配置: {e}")
        api_key = "EMPTY"

    print(f"模型: {model}")
    print(f"地址: {base_url}")
    print("=" * 60)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n【测试 {i}】{test['name']}")
        print(f"提示词: {test['prompt'][:50]}...")
        
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": test['prompt']}],
                "temperature": 0.5,
                "stream": False,
            }
            
            # 适配 OpenAI 格式的 API (Ollama 兼容 /v1/chat/completions)
            if not base_url.endswith("/v1"):
                # 简单处理，如果是 ollama 原生 api 可能不同，但这里假设兼容
                if "v1" not in base_url and "chat" not in base_url:
                     base_url = f"{base_url}/v1"
            
            response = requests.post(
                url=f"{base_url}/chat/completions",
                headers=headers,
                json=payload,
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
    print("此工具测试 LLM 模型是否能按要求格式输出")
    print("支持从 data/config.json 读取配置 (OpenAI/Ollama/DeepSeek)")
    print("如果输出包含额外解释或格式不对，会导致'Failed to match llm output'错误\n")
    
    # 运行测试
    test_ollama()
    
    print("\n🔧 解决方案：")
    print("1. 如果 JSON 解析失败，尝试在 prompt 中强调 '只输出JSON，不要markdown'")
    print("2. 检查 config.json 中的 model 和 api_url 是否正确")
    print("3. 对于 DeepSeek/Qwen 等模型，确保 temperature 较低 (0.1-0.5) 以获得稳定格式")
