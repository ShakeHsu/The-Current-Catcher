#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GitHub工作流程演示脚本
1. 从GitHub获取代码
2. 本地修改
3. 云端同步
"""

import os
import requests
import base64
import json
from datetime import datetime

# 从.env文件读取配置
import os
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

# GitHub配置
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "ghp_xxxxxxxxxxxxxxxxxxxx")  # 您的GitHub Token
GITHUB_REPO = os.getenv("GITHUB_REPO", "yourusername/The-Current-Catcher")  # 您的仓库
GITHUB_API_BASE = "https://api.github.com"

def get_file_from_github(file_name, repo, token):
    """从GitHub获取文件内容"""
    url = f"{GITHUB_API_BASE}/repos/{repo}/contents/{file_name}"
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        content_base64 = response.json()['content']
        content = base64.b64decode(content_base64).decode('utf-8')
        sha = response.json()['sha']
        print(f"✓ 成功获取 {file_name}")
        return content, sha
    else:
        print(f"✗ 获取失败: {response.text}")
        return None, None

def save_file_locally(file_name, content):
    """保存文件到本地"""
    file_path = os.path.join(os.path.dirname(__file__), file_name)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✓ 已保存到本地: {file_name}")

def upload_to_github(file_name, content, repo, token, sha=None, message="更新文件"):
    """上传文件到GitHub"""
    url = f"{GITHUB_API_BASE}/repos/{repo}/contents/{file_name}"
    headers = {
        'Authorization': f'token {token}',
        'Content-Type': 'application/json',
    }
    
    content_base64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    
    data = {
        'message': message,
        'content': content_base64
    }
    
    if sha:
        data['sha'] = sha
    
    response = requests.put(url, headers=headers, data=json.dumps(data))
    
    if response.status_code in [200, 201]:
        print(f"✓ 成功上传到GitHub: {file_name}")
        return True
    else:
        print(f"✗ 上传失败: {response.text}")
        return False

def step1_get_from_github():
    """步骤1：从GitHub获取代码"""
    print("\n" + "="*60)
    print("步骤1：从GitHub获取代码")
    print("="*60)
    
    file_name = "顺势而为+激进+做T.py"
    content, sha = get_file_from_github(file_name, GITHUB_REPO, GITHUB_TOKEN)
    
    if content:
        save_file_locally(file_name, content)
        # 保存sha用于后续更新
        with open('.github_sha', 'w') as f:
            f.write(sha)
        return True
    return False

def step2_modify_locally():
    """步骤2：本地修改"""
    print("\n" + "="*60)
    print("步骤2：本地修改")
    print("="*60)
    
    file_name = "顺势而为+激进+做T.py"
    file_path = os.path.join(os.path.dirname(__file__), file_name)
    
    # 读取文件
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 示例修改：在文件末尾添加注释
    modification = f"""

# ============================================
# 修改记录
# 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# 修改内容: 添加了云端同步测试注释
# ============================================
"""
    
    # 检查是否已经添加过
    if "云端同步测试注释" not in content:
        content += modification
        
        # 保存修改
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✓ 已修改文件: {file_name}")
        print(f"  修改内容: 添加了云端同步测试注释")
        return True
    else:
        print(f"⚠ 文件已经修改过，跳过")
        return False

def step3_sync_to_cloud():
    """步骤3：云端同步"""
    print("\n" + "="*60)
    print("步骤3：云端同步")
    print("="*60)
    
    file_name = "顺势而为+激进+做T.py"
    file_path = os.path.join(os.path.dirname(__file__), file_name)
    
    # 读取本地文件
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 读取之前保存的sha
    sha = None
    if os.path.exists('.github_sha'):
        with open('.github_sha', 'r') as f:
            sha = f.read().strip()
    
    # 上传到GitHub
    message = f"更新策略代码 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    success = upload_to_github(file_name, content, GITHUB_REPO, GITHUB_TOKEN, sha, message)
    
    return success

def main():
    """主函数"""
    print("\n" + "="*60)
    print("GitHub工作流程演示")
    print("="*60)
    print(f"仓库: {GITHUB_REPO}")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查配置
    if GITHUB_TOKEN == "ghp_xxxxxxxxxxxxxxxxxxxx" or GITHUB_REPO == "yourusername/The-Current-Catcher":
        print("\n⚠ 请先修改脚本中的配置：")
        print("  1. GITHUB_TOKEN: 您的GitHub Personal Access Token")
        print("  2. GITHUB_REPO: 您的GitHub仓库名")
        print("\n获取Token方法:")
        print("  1. 访问 https://github.com/settings/tokens")
        print("  2. 点击 'Generate new token (classic)'")
        print("  3. 勾选 'repo' 权限")
        print("  4. 生成并复制Token")
        return
    
    # 执行三个步骤
    success_count = 0
    
    # 步骤1：获取代码
    if step1_get_from_github():
        success_count += 1
    
    # 步骤2：本地修改
    if step2_modify_locally():
        success_count += 1
    
    # 步骤3：云端同步
    if step3_sync_to_cloud():
        success_count += 1
    
    # 总结
    print("\n" + "="*60)
    print("工作流程完成")
    print("="*60)
    print(f"成功步骤: {success_count}/3")
    
    if success_count == 3:
        print("\n✓ 所有步骤执行成功！")
        print("  - 已从GitHub获取最新代码")
        print("  - 已在本地修改代码")
        print("  - 已同步到云端")
    else:
        print("\n⚠ 部分步骤失败，请检查错误信息")

if __name__ == '__main__':
    main()
