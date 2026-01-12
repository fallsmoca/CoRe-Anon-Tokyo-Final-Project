# 四人语言涌现实验 - 快速启动脚本

param(
    [string]$Action = "start",
    [string]$Name = "",
    [int]$Rounds = 100
)

$ErrorActionPreference = "Stop"

Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 69) -ForegroundColor Cyan

Write-Host "  四人语言涌现实验 - Language Emergence Experiment" -ForegroundColor Green

Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 69) -ForegroundColor Cyan

# 检查是否在正确的目录
if (-not (Test-Path "party_chat.py")) {
    Write-Host "`n错误: 请在 generative_agents 目录下运行此脚本" -ForegroundColor Red
    exit 1
}

# 检查conda环境
$condaEnv = "generative_agents_cn"
Write-Host "`n检查Python环境..." -ForegroundColor Yellow

switch ($Action) {
    "start" {
        if ($Name -eq "") {
            $Name = Read-Host "请输入实验名称 (例如: lang-emerge-1)"
        }
        
        Write-Host "`n启动新实验: $Name" -ForegroundColor Green
        Write-Host "参与者: 伊莎贝拉, 玛丽亚, 卡门, 塔玛拉" -ForegroundColor Cyan
        Write-Host "对话轮次: $Rounds" -ForegroundColor Cyan
        Write-Host "`n实验开始..." -ForegroundColor Yellow
        
        python party_chat.py --name $Name --rounds $Rounds --novlang-file "data\prompts\novlang_rules.txt" --verbose info
    }
    
    "resume" {
        if ($Name -eq "") {
            $Name = Read-Host "请输入要继续的实验名称"
        }
        
        Write-Host "`n继续实验: $Name" -ForegroundColor Green
        Write-Host "额外轮次: $Rounds" -ForegroundColor Cyan
        
        python party_chat.py --name $Name --rounds $Rounds --resume --novlang-file "data\prompts\novlang_rules.txt" --verbose info
    }
    
    "analyze" {
        if ($Name -eq "") {
            Write-Host "`n可用的实验:" -ForegroundColor Yellow
            Get-ChildItem "results\party_chat" -Directory | ForEach-Object { Write-Host "  - $($_.Name)" }
            $Name = Read-Host "`n请输入要分析的实验名称"
        }
        
        $roundsFile = "results\party_chat\$Name\rounds.json"
        
        if (-not (Test-Path $roundsFile)) {
            Write-Host "`n错误: 找不到实验数据文件: $roundsFile" -ForegroundColor Red
            exit 1
        }
        
        Write-Host "`n分析实验: $Name" -ForegroundColor Green
        python analyze_emergence.py $roundsFile --export-timeline "results\party_chat\$Name\timeline.json"
    }
    
    "list" {
        Write-Host "`n现有实验:" -ForegroundColor Yellow
        if (Test-Path "results\party_chat") {
            Get-ChildItem "results\party_chat" -Directory | ForEach-Object {
                $exp = $_.Name
                $roundsFile = "results\party_chat\$exp\rounds.json"
                
                if (Test-Path $roundsFile) {
                    $rounds = (Get-Content $roundsFile | ConvertFrom-Json).Count
                    $size = [math]::Round((Get-Item $roundsFile).Length / 1KB, 2)
                    Write-Host "  📊 $exp" -ForegroundColor Cyan
                    Write-Host "      轮次: $rounds | 大小: ${size}KB" -ForegroundColor Gray
                } else {
                    Write-Host "  📁 $exp (无数据)" -ForegroundColor Gray
                }
            }
        } else {
            Write-Host "  (暂无实验)" -ForegroundColor Gray
        }
    }
    
    "view" {
        if ($Name -eq "") {
            $Name = Read-Host "请输入要查看的实验名称"
        }
        
        $roundsFile = "results\party_chat\$Name\rounds.json"
        
        if (-not (Test-Path $roundsFile)) {
            Write-Host "`n错误: 找不到实验数据: $roundsFile" -ForegroundColor Red
            exit 1
        }
        
        Write-Host "`n查看最新对话 (最后10轮):" -ForegroundColor Green
        $data = Get-Content $roundsFile | ConvertFrom-Json
        $lastRounds = $data | Select-Object -Last 10
        
        foreach ($round in $lastRounds) {
            Write-Host "`n  === 第 $($round.round) 轮 ===" -ForegroundColor Yellow
            foreach ($conv in $round.conversations) {
                Write-Host "    $($conv.speaker): " -ForegroundColor Cyan -NoNewline
                Write-Host $conv.content -ForegroundColor White
            }
        }
    }
    
    "help" {
        Write-Host @"

使用方法:
  .\run_experiment.ps1 -Action <action> [-Name <name>] [-Rounds <number>]

可用操作:
  start     - 开始新实验
  resume    - 继续现有实验
  analyze   - 分析实验数据
  list      - 列出所有实验
  view      - 查看实验对话记录
  help      - 显示帮助信息

示例:
  # 开始新实验
  .\run_experiment.ps1 -Action start -Name "test-1" -Rounds 100

  # 继续实验
  .\run_experiment.ps1 -Action resume -Name "test-1" -Rounds 50

  # 分析结果
  .\run_experiment.ps1 -Action analyze -Name "test-1"

  # 列出所有实验
  .\run_experiment.ps1 -Action list

  # 查看对话记录
  .\run_experiment.ps1 -Action view -Name "test-1"

"@ -ForegroundColor Cyan
    }
    
    default {
        Write-Host "`n错误: 未知操作 '$Action'" -ForegroundColor Red
        Write-Host "使用 -Action help 查看帮助" -ForegroundColor Yellow
    }
}

Write-Host ""
