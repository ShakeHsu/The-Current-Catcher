# GitHub上传指南

## 方法一：使用GitHub网页上传（最简单）

### 步骤1：创建GitHub仓库
1. 访问 https://github.com/new
2. 仓库名称：`The-Current-Catcher`
3. 选择：Public（公开）或Private（私有）
4. 点击"Create repository"

### 步骤2：上传文件
1. 在新创建的仓库页面，点击"uploading an existing file"
2. 或直接拖拽以下文件到上传区域：
   - `顺势而为+激进+做T.py`
   - `顺势而为+激进+做T_backtrader.py`
   - `test_akshare_minute.py`
3. 填写提交信息："初始化量化交易策略"
4. 点击"Commit changes"

## 方法二：使用Git命令行（推荐）

### 步骤1：安装Git
下载并安装Git：
- Windows: https://git-scm.com/download/win
- 选择默认安装选项

### 步骤2：配置Git
打开PowerShell或CMD，执行：

```bash
# 配置用户名
git config --global user.name "Your Name"

# 配置邮箱
git config --global user.email "your.email@example.com"
```

### 步骤3：初始化并上传
```bash
# 进入项目目录
cd "C:\Users\XU\Documents\trae_projects\The Current Catcher"

# 初始化Git仓库
git init

# 添加所有文件
git add .

# 提交
git commit -m "初始化量化交易策略"

# 添加远程仓库（替换为您的仓库地址）
git remote add origin https://github.com/yourusername/The-Current-Catcher.git

# 推送到GitHub
git push -u origin main
```

## 方法三：使用GitHub Desktop（图形界面）

### 步骤1：安装GitHub Desktop
下载：https://desktop.github.com/

### 步骤2：连接仓库
1. 打开GitHub Desktop
2. 选择"File" -> "Add Local Repository"
3. 选择项目文件夹：`C:\Users\XU\Documents\trae_projects\The Current Catcher`
4. 点击"Publish repository"

## 推荐方案

**对于初学者**：使用方法一（网页上传）
- 最简单，无需安装软件
- 适合一次性上传

**对于开发者**：使用方法二（Git命令行）
- 功能最强大
- 支持版本管理
- 适合频繁修改

**对于Windows用户**：使用方法三（GitHub Desktop）
- 图形界面，操作简单
- 可视化版本历史

## 后续同步

### 在其他电脑上获取代码

```bash
# 克隆仓库
git clone https://github.com/yourusername/The-Current-Catcher.git

# 进入目录
cd The-Current-Catcher
```

### 更新代码

```bash
# 拉取最新代码
git pull

# 修改后提交
git add .
git commit -m "更新策略"
git push
```

## 注意事项

1. **不要上传敏感信息**：
   - API密钥
   - 密码
   - 个人信息

2. **创建.gitignore文件**（可选）：
   ```
   __pycache__/
   *.pyc
   .DS_Store
   *.log
   ```

3. **定期备份**：
   - GitHub是云存储，但建议定期本地备份
   - 重要代码可以同时保存到多个位置