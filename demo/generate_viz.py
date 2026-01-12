import json
import os
import argparse

# HTML Template
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Novlang Conversation Visualizer</title>
    <style>
        :root {
            --char-width: 100px;
            --bubble-max-width: 300px;
            --text-size: 1.1em;
            /* Injected overrides */
            {{CSS_OVERRIDES}}
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f0f2f5;
            display: flex;
            flex-direction: column;
            align-items: center;
            height: 100vh;
        }

        #app {
            width: 100%;
            max-width: 1000px;
            height: 90vh;
            margin-top: 20px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        header {
            background: #2c3e50;
            color: white;
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        #scene-info {
            background: #ecf0f1;
            padding: 10px 20px;
            border-bottom: 1px solid #bdc3c7;
            font-size: 0.9em;
            color: #555;
            white-space: pre-line;
            max-height: 100px;
            overflow-y: auto;
        }

        #stage {
            flex: 1;
            display: flex;
            justify-content: center;
            align-items: center;
            overflow: hidden;
            background-color: white;
        }

        #scene-wrapper {
            position: relative;
            max-width: 100%;
            max-height: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        #scene-wrapper.no-bg {
            width: 100%;
            height: 100%;
            background-image: radial-gradient(#d1d5db 1px, transparent 1px);
            background-size: 20px 20px;
            background-color: #e8eaed;
        }

        #scene-bg {
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
            display: none;
        }

        #scene-bg.visible {
            display: block;
        }

        #char-layer {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
        }

        .character {
            position: absolute;
            display: flex;
            flex-direction: column;
            align-items: center;
            transition: all 0.5s ease;
            width: var(--char-width);
        }

        .character img {
            width: 100%;
            height: auto;
            /* Removed circle styling */
            /* border-radius: 50%; */
            /* border: 3px solid #fff; */
            /* background-color: #ddd; */
            
            /* Blending style */
            image-rendering: pixelated; /* Sharp pixel art */
            filter: drop-shadow(0 0 10px rgba(255,255,255,0.3)); /* Outer glow to stand out from bg */
            object-fit: contain;
        }

        .character .name {
            margin-top: -10px; /* Pull up closer */
            font-weight: bold;
            background: rgba(0,0,0,0.6); /* Dark semi-transparent */
            color: white;
            padding: 2px 10px;
            border-radius: 12px;
            font-size: 0.8em;
            z-index: 2;
        }

        .chat-bubble {
            position: absolute;
            background: white;
            padding: 15px;
            border-radius: 15px;
            box-shadow: 0 3px 10px rgba(0,0,0,0.1);
            max-width: var(--bubble-max-width);
            width: max-content; /* Fit content up to max-width */
            
            /* Position relative to the character (parent) */
            bottom: 100%; 
            left: 50%;
            margin-bottom: 20px; /* Offset from char head */
            
            opacity: 0;
            transform: translateX(-50%) scale(0.8);
            transform-origin: bottom center;
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            pointer-events: none;
            z-index: 10;
        }

        .chat-bubble.visible {
            opacity: 1;
            transform: translateX(-50%) scale(1);
            pointer-events: auto;
        }

        .chat-bubble::after {
            content: '';
            position: absolute;
            bottom: -10px;
            left: 50%;
            transform: translateX(-50%); 
            border-width: 10px 10px 0;
            border-style: solid;
            border-color: white transparent transparent transparent;
        }

        .novlang-text {
            font-family: 'Courier New', Courier, monospace;
            font-size: var(--text-size);
            color: #2c3e50;
            font-weight: bold;
            margin-bottom: 8px;
            word-break: break-all;
        }

        .chinese-text {
            border-top: 1px solid #eee;
            padding-top: 8px;
            color: #7f8c8d;
            font-size: calc(var(--text-size) * 0.75);
        }

        #controls {
            padding: 15px 20px;
            background: #fff;
            border-top: 1px solid #eee;
            display: flex;
            justify-content: center;
            gap: 15px;
        }

        button {
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            background: #3498db;
            color: white;
            cursor: pointer;
            font-size: 1em;
            transition: background 0.2s;
        }

        button:hover {
            background: #2980b9;
        }
        
        button:disabled {
            background: #95a5a6;
            cursor: not-allowed;
        }

        .thinking-box {
            position: absolute;
            bottom: 20px;
            right: 20px;
            width: 250px;
            background: #fff3cd;
            border: 1px solid #ffeeba;
            padding: 10px;
            border-radius: 8px;
            font-size: 0.8em;
            color: #856404;
            display: none;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            z-index: 5;
        }

        /* Positions */
        .pos-left { left: 20%; top: 40%; }
        .pos-right { right: 20%; top: 40%; }
        .pos-1 { top: 20%; left: 50%; transform: translateX(-50%); }
        .pos-2 { top: 50%; right: 10%; }
        .pos-3 { bottom: 20%; left: 50%; transform: translateX(-50%); }
        .pos-4 { top: 50%; left: 10%; }

    </style>
</head>
<body>

<div id="app">
    <header>
        <div>
            <strong>Novlang Experience</strong>
            <span id="round-indicator" style="margin-left: 15px; font-weight: normal; opacity: 0.8;">Round 1</span>
        </div>
        <div style="font-size: 0.8em">Language Emergence Project</div>
    </header>
    
    <div id="scene-info"></div>

    <div id="stage">
        <div id="scene-wrapper">
            <img id="scene-bg" alt="">
            <div id="char-layer">
                <div id="thinking-display" class="thinking-box"></div>
            </div>
        </div>
    </div>

    <div id="controls">
        <button id="prevBtn" onclick="prevStep()">Previous</button>
        <button id="playBtn" onclick="togglePlay()">Play</button>
        <button id="nextBtn" onclick="nextStep()">Next</button>
        <button id="resetBtn" onclick="reset()">Reset</button>
    </div>
</div>

<script>
    // --- Data Injected ---
    const conversationData = {{JSON_DATA}};

    // State
    let currentRoundIndex = 0;
    let currentTurnIndex = -1; 
    let isSetup = false;
    let isPlaying = false;
    let playInterval = null;
    let playSpeed = 3000; // time in ms per turn
    
    // Elements
    const stageEl = document.getElementById('stage');
    const sceneWrapperEl = document.getElementById('scene-wrapper');
    const sceneBgEl = document.getElementById('scene-bg');
    const charLayerEl = document.getElementById('char-layer');
    const sceneInfoEl = document.getElementById('scene-info');
    const roundIndicatorEl = document.getElementById('round-indicator');
    const thinkingDisplayEl = document.getElementById('thinking-display');
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const playBtn = document.getElementById('playBtn');


    // Logic
    function renderCharacters(participants, isGroup) {
        // Clear charlayer except thinking box
        charLayerEl.innerHTML = '<div id="thinking-display" class="thinking-box"></div>';
        
        participants.forEach((name, index) => {
            const charEl = document.createElement('div');
            charEl.className = 'character';
            charEl.id = `char-${name}`;
            
            if (isGroup) {
               const posClass = `pos-${index + 1}`;
               charEl.classList.add(posClass);
            } else {
               if (index === 0) charEl.classList.add('pos-left');
               else charEl.classList.add('pos-right');
            }

            // Note: The script assumes images are in folders named after the character relative to the HTML file
            const imgPath = `${name}/portrait.png`;
            charEl.innerHTML = `
                <img src="${imgPath}" onerror="this.src='https://ui-avatars.com/api/?name=${name}&background=random'" alt="${name}">
                <div class="name">${name}</div>
            `;
            charLayerEl.appendChild(charEl);
        });
    }

    function showBubble(speakerName, turnData) {
        // Reset z-indexes
        document.querySelectorAll('.character').forEach(c => c.style.zIndex = '');

        const existingBubbles = document.querySelectorAll('.chat-bubble');
        existingBubbles.forEach(b => b.remove());

        const charEl = document.getElementById(`char-${speakerName}`);
        if (!charEl) return;
        
        // Bring speaker to front
        charEl.style.zIndex = 100;

        const bubble = document.createElement('div');
        bubble.className = 'chat-bubble';
        bubble.innerHTML = `
            <div class="novlang-text">${turnData.novlang}</div>
            <div class="chinese-text">${turnData.chinese}</div>
        `;
        
        // Positioning logic
        // Append bubble directly to the character element so it moves with it and positions relatively
        
        // Clear manual styles that interfere with CSS relative positioning
        // bubble.style.left/top handled by CSS bottom: 100% left: 50%
        
        charEl.appendChild(bubble); 
        
        requestAnimationFrame(() => {
            bubble.classList.add('visible');
        });

        // Update thinking box
        const thinkingBox = document.getElementById('thinking-display');
        if (turnData.thinking) {
            thinkingBox.style.display = 'block';
            thinkingBox.innerText = `Thinking: ${turnData.thinking}`;
        } else {
            thinkingBox.style.display = 'none';
        }
    }

    function updateScene() {
        const roundData = conversationData[currentRoundIndex];
        sceneInfoEl.innerText = roundData.scene;
        roundIndicatorEl.innerText = `Round ${roundData.round}`;

        // Update Background
        if (roundData.backgroundImage) {
            sceneBgEl.src = roundData.backgroundImage;
            sceneBgEl.classList.add('visible');
            sceneWrapperEl.classList.remove('no-bg');
        } else {
            sceneBgEl.classList.remove('visible');
            sceneWrapperEl.classList.add('no-bg');
        }

        const isGroup = roundData.participants.length > 2;
        if (!isSetup) {
            renderCharacters(roundData.participants, isGroup);
            isSetup = true;
        }

        if (currentTurnIndex >= 0 && currentTurnIndex < roundData.conversations.length) {
            const turnData = roundData.conversations[currentTurnIndex];
            showBubble(turnData.speaker, turnData);
        } else {
            const existingBubbles = document.querySelectorAll('.chat-bubble');
            existingBubbles.forEach(b => b.remove());
            document.getElementById('thinking-display').style.display = 'none';
            document.querySelectorAll('.character').forEach(c => c.style.zIndex = '');
        }

        updateButtons();
    }

    function togglePlay() {
        if (isPlaying) {
            stopPlay();
        } else {
            startPlay();
        }
    }

    function startPlay() {
        if (nextBtn.disabled) return; // Don't start if at end
        
        isPlaying = true;
        playBtn.innerText = "Pause";
        playBtn.style.backgroundColor = "#e74c3c"; // Red for pause
        
        nextStep(); // Run one immediately
        
        // Clear any existing just in case
        if (playInterval) clearTimeout(playInterval);
        
        scheduleNext();
    }
    
    function scheduleNext() {
        if (!isPlaying) return;
        
        // Determine wait time based on current content length
        let waitTime = 3000; // Base time
        
        if (currentRoundIndex < conversationData.length) {
             const roundData = conversationData[currentRoundIndex];
             if (currentTurnIndex >= 0 && currentTurnIndex < roundData.conversations.length) {
                 const turnData = roundData.conversations[currentTurnIndex];
                 // Simple logic: 2000ms base + 50ms per character of conversation
                 // Including both novlang and chinese for estimation
                 const length = (turnData.novlang?.length || 0) + (turnData.chinese?.length || 0);
                 waitTime = 0 + (length * 80); 
             }
        }

        playInterval = setTimeout(() => {
            if (isPlaying && !nextBtn.disabled) {
                nextStep();
                scheduleNext();
            } else {
                stopPlay(); // Stop if reached end
            }
        }, waitTime);
    }

    function stopPlay() {
        isPlaying = false;
        playBtn.innerText = "Play";
        playBtn.style.backgroundColor = ""; // Reset color
        if (playInterval) {
            clearTimeout(playInterval);
            playInterval = null;
        }
    }

    function nextStep() {
        const roundData = conversationData[currentRoundIndex];
        
        if (currentTurnIndex < roundData.conversations.length - 1) {
            currentTurnIndex++;
        } else {
            if (currentRoundIndex < conversationData.length - 1) {
                currentRoundIndex++;
                currentTurnIndex = -1;
                isSetup = false;
            }
        }
        updateScene();
    }

    function prevStep() {
         if (currentTurnIndex > -1) {
            currentTurnIndex--;
        } else {
            if (currentRoundIndex > 0) {
                currentRoundIndex--;
                const roundData = conversationData[currentRoundIndex];
                currentTurnIndex = roundData.conversations.length - 1;
                isSetup = false;
            }
        }
        updateScene();
    }

    function reset() {
        currentRoundIndex = 0;
        currentTurnIndex = -1;
        isSetup = false;
        updateScene();
    }

    function updateButtons() {
        prevBtn.disabled = (currentRoundIndex === 0 && currentTurnIndex === -1);
        
        const lastRoundIdx = conversationData.length - 1;
        const lastTurnIdx = conversationData[lastRoundIdx].conversations.length - 1;
        nextBtn.disabled = (currentRoundIndex === lastRoundIdx && currentTurnIndex === lastTurnIdx);
    }

    updateScene();
</script>
</body>
</html>
"""

def generate_visualization(json_file_path, output_html_path, options=None):
    """
    Reads a JSON conversation file and creates an HTML visualization.
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return

    # --- Pre-process data to find backgrounds ---
    base_dir = os.path.dirname(os.path.abspath(json_file_path))
    bg_dir = os.path.join(base_dir, 'backgrounds')
    
    # Get available background images
    available_bgs = []
    if os.path.exists(bg_dir):
        available_bgs = [f for f in os.listdir(bg_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif'))]
        # Sort by name length desc to match most specific first
        available_bgs.sort(key=lambda x: len(os.path.splitext(x)[0]), reverse=True)

    def find_bg(scene_text):
        if not scene_text or not available_bgs:
            return None
        for bg_file in available_bgs:
            name_no_ext = os.path.splitext(bg_file)[0]
            if name_no_ext in scene_text:
                return f"backgrounds/{bg_file}"
        return None

    # Inject background paths into data
    if isinstance(data, list):
        for round_item in data:
            if 'scene' in round_item:
                bg = find_bg(round_item['scene'])
                if bg:
                    round_item['backgroundImage'] = bg

    # Convert data to JSON string for injection
    json_string = json.dumps(data, ensure_ascii=False, indent=2)

    # Inject data into HTML
    output_html = HTML_TEMPLATE.replace('{{JSON_DATA}}', json_string)
    
    # Inject CSS Overrides
    css_overrides = ""
    if options:
        if options.get('char_size'):
            css_overrides += f"--char-width: {options['char_size']}px;\n"
        if options.get('bubble_width'):
            css_overrides += f"--bubble-max-width: {options['bubble_width']}px;\n"
        if options.get('text_size'):
             val = options['text_size']
             # Add em if no unit provided
             if str(val).replace('.','',1).isdigit():
                 val = f"{val}em"
             css_overrides += f"--text-size: {val};\n"
            
    output_html = output_html.replace('{{CSS_OVERRIDES}}', css_overrides)

    try:
        with open(output_html_path, 'w', encoding='utf-8') as f:
            f.write(output_html)
        print(f"Successfully created visualization at: {output_html_path}")
    except Exception as e:
        print(f"Error writing HTML file: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert Novlang conversation JSON to HTML visualization.")
    parser.add_argument("json_file", help="Path to the input JSON conversation file")
    parser.add_argument("--output", "-o", help="Path to the output HTML file. Defaults to [json_filename].html", default=None)
    
    # Tuning parameters
    parser.add_argument("--char-size", type=int, help="Character width in pixels (default: 100)")
    parser.add_argument("--bubble-width", type=int, help="Max bubble width in pixels (default: 300)")
    parser.add_argument("--text-size", help="Text font size (e.g. '1.1em' or '0.9')")

    args = parser.parse_args()

    input_path = args.json_file
    if args.output:
        output_path = args.output
    else:
        # Default output name based on input
        base_name = os.path.splitext(input_path)[0]
        output_path = f"{base_name}.html"

    # Pass options
    options = {
        'char_size': args.char_size,
        'bubble_width': args.bubble_width,
        'text_size': args.text_size
    }

    generate_visualization(input_path, output_path, options)
