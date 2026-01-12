import os
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify

from compress import frames_per_step, file_movement
from start import personas

app = Flask(
    __name__,
    template_folder="frontend/templates",
    static_folder="frontend/static",
    static_url_path="/static",
)

# 全局变量存储当前模拟的对话数据
current_conversation_data = {}


@app.route("/", methods=['GET'])
def index():
    name = request.args.get("name", "")          # 记录名称
    step = int(request.args.get("step", 0))      # 回放起始步数
    speed = int(request.args.get("speed", 2))    # 回放速度（0~5）
    zoom = float(request.args.get("zoom", 0.8))  # 画面缩放比例

    if len(name) > 0:
        compressed_folder = f"results/compressed/{name}"
    else:
        return f"Invalid name of the simulation: '{name}'"

    replay_file = f"{compressed_folder}/{file_movement}"
    if not os.path.exists(replay_file):
        return f"The data file doesn‘t exist: '{replay_file}'<br />Run compress.py to generate the data first."

    with open(replay_file, "r", encoding="utf-8") as f:
        params = json.load(f)

    if step < 1:
        step = 1
    if step > 1:
        # 重新设置回放的起始时间
        t = datetime.fromisoformat(params["start_datetime"])
        dt = t + timedelta(minutes=params["stride"]*(step-1))
        params["start_datetime"] = dt.isoformat()
        step = (step-1) * frames_per_step + 1
        if step >= len(params["all_movement"]):
            step = len(params["all_movement"])-1

        # 重新设置Agent的初始位置
        for agent in params["persona_init_pos"].keys():
            persona_init_pos = params["persona_init_pos"]
            persona_step_pos = params["all_movement"][f"{step}"]
            persona_init_pos[agent] = persona_step_pos[agent]["movement"]

    if speed < 0:
        speed = 0
    elif speed > 5:
        speed = 5
    speed = 2 ** speed

    # 加载对话数据
    global current_conversation_data
    checkpoints_folder = f"results/checkpoints/{name}"
    conversation_file = f"{checkpoints_folder}/conversation.json"
    if os.path.exists(conversation_file):
        try:
            with open(conversation_file, "r", encoding="utf-8") as f:
                current_conversation_data = json.load(f)
        except:
            current_conversation_data = {}
    else:
        current_conversation_data = {}

    return render_template(
        "index.html",
        persona_names=personas,
        step=step,
        play_speed=speed,
        zoom=zoom,
        **params
    )


@app.route("/api/conversations", methods=['GET'])
def get_conversations():
    """获取对话数据的 API 端点"""
    global current_conversation_data
    
    # 将对话数据格式化为前端所需的格式
    formatted_data = {}
    
    if not current_conversation_data:
        return jsonify({"conversations": {}})
    
    # 遍历每个时间段的对话
    for time_key, conv_list in current_conversation_data.items():
        conversations = []
        
        if isinstance(conv_list, list):
            for conv_item in conv_list:
                if isinstance(conv_item, dict):
                    # 每个对话项的格式：{"说话者1 → 说话者2 @ 位置": [[说话者, 符号语言, 翻译], ...]}
                    formatted_item = {}
                    for key, messages in conv_item.items():
                        if isinstance(messages, list):
                            # 处理消息列表
                            formatted_messages = []
                            for msg in messages:
                                if isinstance(msg, (list, tuple)) and len(msg) >= 2:
                                    # msg 格式：(说话者, 符号语言, 翻译)
                                    speaker = msg[0]
                                    symbol = msg[1]
                                    translation = msg[2] if len(msg) > 2 else ""
                                    
                                    # 提取翻译部分（如果包含在符号后面）
                                    if " [翻译：" in symbol:
                                        parts = symbol.split(" [翻译：")
                                        symbol = parts[0]
                                        if len(parts) > 1 and "]" in parts[1]:
                                            translation = parts[1].rstrip("]")
                                    
                                    formatted_messages.append([speaker, symbol, translation])
                            
                            if formatted_messages:
                                formatted_item[key] = formatted_messages
                    
                    if formatted_item:
                        conversations.append(formatted_item)
        
        if conversations:
            formatted_data[time_key] = conversations
    
    return jsonify({"conversations": formatted_data})


@app.route("/conversation", methods=['GET'])
def conversation():
    """对话可视化页面"""
    return render_template("conversation.html", persona_names=personas)


if __name__ == "__main__":
    app.run(debug=True)
