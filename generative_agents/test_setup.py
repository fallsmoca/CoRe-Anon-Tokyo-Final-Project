"""
测试四人对话系统配置
快速验证环境和配置是否正确
"""
import os
import sys
import json

def test_environment():
    """测试环境配置"""
    print("=" * 70)
    print("四人对话系统 - 环境测试")
    print("=" * 70)
    
    checks = []
    
    # 1. 检查必要文件
    print("\n📁 检查必要文件...")
    required_files = [
        "party_chat.py",
        "analyze_emergence.py",
        "start.py",
        "data/config.json",
        "data/prompts/novlang_rules.txt",
        "data/prompts/generate_chat.txt",
    ]
    
    for file in required_files:
        exists = os.path.exists(file)
        status = "✓" if exists else "✗"
        print(f"  {status} {file}")
        checks.append(exists)
    
    # 2. 检查config.json配置
    print("\n⚙️  检查配置文件...")
    try:
        with open("data/config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        
        agent_config = config.get("agent", {})
        
        # 检查关键参数
        interval = agent_config.get("think", {}).get("interval", 0)
        chat_iter = agent_config.get("chat_iter", 0)
        retention = agent_config.get("associate", {}).get("retention", 0)
        vision_r = agent_config.get("percept", {}).get("vision_r", 0)
        
        print(f"  interval: {interval} ms {'✓ 已优化' if interval <= 500 else '⚠ 建议≤500'}")
        print(f"  chat_iter: {chat_iter} {'✓ 已优化' if chat_iter >= 8 else '⚠ 建议≥8'}")
        print(f"  retention: {retention} {'✓ 已优化' if retention >= 12 else '⚠ 建议≥12'}")
        print(f"  vision_r: {vision_r} {'✓ 已优化' if vision_r >= 10 else '⚠ 建议≥10'}")
        
        checks.append(True)
    except Exception as e:
        print(f"  ✗ 配置文件错误: {e}")
        checks.append(False)
    
    # 3. 检查start.py人物列表
    print("\n👥 检查人物配置...")
    try:
        with open("start.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        expected_personas = ["伊莎贝拉", "玛丽亚", "卡门", "塔玛拉"]
        found = all(name in content for name in expected_personas)
        
        if found:
            print(f"  ✓ 四个核心角色已配置: {', '.join(expected_personas)}")
            checks.append(True)
        else:
            print(f"  ✗ 人物列表配置错误")
            checks.append(False)
    except Exception as e:
        print(f"  ✗ 无法读取start.py: {e}")
        checks.append(False)
    
    # 4. 检查Ollama连接
    print("\n🤖 检查LLM服务...")
    try:
        import requests
        response = requests.get("http://127.0.0.1:11434/api/tags", timeout=3)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m.get("name", "") for m in models]
            
            required_model = "qwen3:8b-q4_K_M"
            if any(required_model in name for name in model_names):
                print(f"  ✓ Ollama运行正常，模型已加载")
                checks.append(True)
            else:
                print(f"  ⚠ Ollama运行，但未找到 {required_model}")
                print(f"    可用模型: {', '.join(model_names[:3])}")
                checks.append(False)
        else:
            print(f"  ✗ Ollama响应异常: {response.status_code}")
            checks.append(False)
    except requests.exceptions.RequestException:
        print(f"  ✗ 无法连接Ollama服务 (http://127.0.0.1:11434)")
        print(f"    请运行: ollama serve")
        checks.append(False)
    except ImportError:
        print(f"  ⚠ 未安装requests库，跳过Ollama检查")
        print(f"    安装: pip install requests")
    
    # 5. 检查embedding模型
    print("\n🧠 检查Embedding模型...")
    try:
        from sentence_transformers import SentenceTransformer
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        print(f"  ✓ sentence-transformers已安装")
        checks.append(True)
    except ImportError:
        print(f"  ✗ 未安装sentence-transformers")
        print(f"    安装: pip install sentence-transformers")
        checks.append(False)
    
    # 6. 检查结果目录
    print("\n📂 检查输出目录...")
    results_dir = "results/party_chat"
    if not os.path.exists(results_dir):
        os.makedirs(results_dir, exist_ok=True)
        print(f"  ✓ 已创建输出目录: {results_dir}")
    else:
        print(f"  ✓ 输出目录已存在: {results_dir}")
    checks.append(True)
    
    # 总结
    print("\n" + "=" * 70)
    passed = sum(checks)
    total = len(checks)
    percentage = (passed / total) * 100 if total > 0 else 0
    
    if percentage == 100:
        print(f"✅ 所有检查通过！({passed}/{total})")
        print("\n🚀 你可以开始实验了:")
        print("   .\\run_experiment.ps1 -Action start -Name 'test-1' -Rounds 50")
        print("   或")
        print("   python party_chat.py --name test-1 --rounds 50 --novlang-file data\\prompts\\novlang_rules.txt")
        return True
    elif percentage >= 80:
        print(f"⚠️  大部分检查通过 ({passed}/{total} = {percentage:.0f}%)")
        print("\n建议修复上述问题后再开始实验")
        return False
    else:
        print(f"❌ 检查失败 ({passed}/{total} = {percentage:.0f}%)")
        print("\n请修复上述所有问题")
        return False


if __name__ == "__main__":
    success = test_environment()
    sys.exit(0 if success else 1)
