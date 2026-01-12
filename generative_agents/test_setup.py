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
        "data/config.json",
        "data/prompts/generate_chat.txt",
    ]
    
    for file in required_files:
        exists = os.path.exists(file)
        status = "✓" if exists else "✗"
        print(f"  {status} {file}")
        checks.append(exists)
    
    # 2. 检查config.json配置
    print("\n⚙️  检查配置文件 (data/config.json)...")
    try:
        with open("data/config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        
        agent_config = config.get("agent", {})
        llm_config = agent_config.get("think", {}).get("llm", {})
        
        # 检查关键参数
        provider = llm_config.get("provider", "unknown")
        model = llm_config.get("model", "unknown")
        base_url = llm_config.get("base_url", "unknown")
        
        print(f"  LLM Provider: {provider}")
        print(f"  Model: {model}")
        print(f"  Base URL: {base_url}")
        
        if provider and model:
            print(f"  ✓ LLM 配置看似有效")
            checks.append(True)
        else:
            print(f"  ✗ LLM 配置缺失")
            checks.append(False)
            
    except Exception as e:
        print(f"  ✗ 配置文件错误: {e}")
        checks.append(False)
    
    # 3. 检查人物配置 (hardcoded in party_chat.py)
    print("\n👥 检查实验脚本...")
    try:
        with open("party_chat.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # 检查 party_chat.py 中的核心角色定义
        expected_personas = ["伊莎贝拉", "玛丽亚", "卡门", "塔玛拉"]
        found = all(name in content for name in expected_personas)
        
        if found:
            print(f"  ✓ 四个核心角色在代码中定义: {', '.join(expected_personas)}")
            checks.append(True)
        else:
            print(f"  ✗ party_chat.py 中未找到部分核心角色定义")
            checks.append(False)
    except Exception as e:
        print(f"  ✗ 无法读取 party_chat.py: {e}")
        checks.append(False)
    
    # 4. 检查 LLM 服务连通性 (基于 config.json)
    print("\n🤖 检查 LLM 服务连通性...")
    try:
        import requests
        # 简单的连通性测试 (尝试访问 base_url 或其变体)
        test_url = base_url
        if not test_url.startswith("http"):
            print("  ⚠ Base URL 需要以 http/https 开头")
        else:
            # 简单 Ping
            try:
                # 很多 OpenAI API 兼容接口在根路径会有 404 或 200，只要能连通就行
                # 或者访问 /v1/models
                if not test_url.endswith("/v1"):
                     if "v1" not in test_url: test_url += "/v1"
                
                response = requests.get(f"{test_url}/models", timeout=5, headers={"Authorization": f"Bearer {llm_config.get('api_key', '')}"})
                
                if response.status_code in [200, 401, 403]: # 401/403 说明服务在，只是key可能问题，但也算连通
                    print(f"  ✓ 服务可访问 ({test_url}) [{response.status_code}]")
                    checks.append(True)
                else:
                    print(f"  ⚠ 服务响应状态码异常: {response.status_code}")
                    checks.append(False)
            except Exception as e:
                 print(f"  ✗ 无法连接到 LLM 服务: {e}")
                 checks.append(False)

    except ImportError:
        print(f"  ⚠ 未安装 requests 库")

    
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
        print("   python party_chat.py --name test-1 --rounds 50")
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
