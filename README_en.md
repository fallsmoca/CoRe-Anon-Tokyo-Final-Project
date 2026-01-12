[简体中文](./README.md) | English

# Language Emergence Experiment of Anon Tokyo

---
## Overview

Stanford AI Town, open-sourced by Stanford University and Google in August 2023, is a virtual world composed of 25 intelligent agents that simulates real human life. These 25 agents are entirely powered by ChatGPT, capable of independently organizing parties, attending meetings, and arranging various activities for Valentine's Day. They can exhibit life patterns and behavioral habits similar to human beings.

Based on the original project, we conducted a language emergence experiment with our own refactored version.

## 1. Preparation

### 1.1 Obtain the Code

```
git clone https://github.com/fallsmoca/CoRe-Anon-Tokyo-Final-Project.git
cd CoRe-Anon-Tokyo-Final-Project
```

### 1.2 Configure the Large Language Model (LLM)

Modify the configuration file generative_agents/data/config.json:

1. By default,Ollama is used to load local quantized models and provide an OpenAI-compatible API. You need to pull the quantized model first (refer to ollama.md) and ensure that base_url and model are consistent with the configurations in Ollama.

2. If you want to call other OpenAI-compatible APIs, you need to change provider to openai, and modify model, api_key, and base_url according to the API documentation.

### 1.3 Install Python Dependencies

It is recommended to first create and activate a virtual environment using anaconda3:

```
conda create -n anontokyo python=3.12
conda activate anontokyo
```

Install dependencies:

```
pip install -r requirements.txt
```

Check the environment and the LLM:

```
cd generative_agents
python test_setup.py
python test_llm_format.py
```


## 2. Run the Language Emergence Experiment

```
 python party_chat.py --name experiment --rounds 10 --turns 20 --group-interval 3 --inject-round 4
```

Parameter Description

- `name` - Each time you start the virtual town, you need to set a unique name for recording experimental results.

- `rounds` - Total rounds. How many dialogue rounds the experiment will run.

- `turns` - Number of turns per round. How many sentences two characters exchange (one speaking and the other responding) in one dialogue round.

- `group-interval` - Group chat frequency. How many rounds to trigger a "village square multi-person shared dialogue" (all characters gather to chat).

- `inject-round` - The round to inject foreign words, i.e., in which round to introduce foreign words (optional).

P.S. Our demo is stored in the file demo_new.html under the demo folder, and the generate_viz.py file in this folder can convert rounds.json into the format required by the demo.

![demo](docs/resources/demo.png)
