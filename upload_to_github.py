#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
上传代码到GitHub
"""

import os
import requests
import base64
import json

# GitHub配置
GITHUB_TOKEN = "YOUR_GITHUB_TOKEN"  # 需要替换为您的GitHub token
GITHUB_REPO = "yourusername/your-repo"  # 需要替换为您的仓库
GITHUB_API_BASE = "https://api.github.com"

def upload_to_github(file_path, repo, token, commit_message="更新文件"):
    """上传文件到GitHub"""
    
    # 获取文件相对路径
    file_name = os.path.basename(file_path)
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Base64编码
    content_base64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    
    # 构造API请求
    url = f"{GITHUB_API_BASE}/repos/{repo}/contents/{file_name}"
    headers = {
        'Authorization': f'token {token}',
        'Content-Type': 'application/json',
    }
    
    # 检查文件是否已存在
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        # 文件已存在，需要sha
        sha = response.json()['sha']
        data = {
            'message': commit_message,
            'content': content_base64,
            'sha': sha
        }
    else:
        # 新文件
        data = {
            'message': commit_message,
            'content': content_base64
        }
    
    # 上传文件
    response = requests.put(url, headers=headers, data=json.dumps(data))
    
    if response.status_code in [200, 201]:
        print(f"✓ {file_name} 上传成功")
        return True
    else:
        print(f"✗ {file_name} 上传失败: {response.text}")
        return False

def main():
    """主函数"""
    print("开始上传代码到GitHub...")
    print(f"仓库: {GITHUB_REPO}")
    
    # 检查token
    if GITHUB_TOKEN == "YOUR_GITHUB_TOKEN":
        print("错误：请先设置GitHub Token")
        print("1. 访问 https://github.com/settings/tokens")
        print("2. 生成新的Personal Access Token")
        print("3. 修改此脚本中的GITHUB_TOKEN变量")
        return
    
    # 上传策略文件
    files_to_upload = [
        "顺势而为+激进+做T.py",
        "顺势而为+激进+做T_backtrader.py",
        "test_akshare_minute.py",
    ]
    
    success_count = 0
    for file_name in files_to_upload:
        file_path = os.path.join(os.path.dirname(__file__), file_name)
        if os.path.exists(file_path):
            if upload_to_github(file_path, GITHUB_REPO, GITHUB_TOKEN):
                success_count += 1
        else:
            print(f"⚠ 文件不存在: {file_name}")
    
    print(f"\n上传完成！成功: {success_count}/{len(files_to_upload)}")

if __name__ == '__main__':
    main()