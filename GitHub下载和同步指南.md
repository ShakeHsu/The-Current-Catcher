# GitHub代码下载和同步脚本

## 方式一：使用PowerShell脚本（推荐）

### 步骤1：创建下载脚本

创建文件 `download_from_github.ps1`，内容如下：

```powershell
# GitHub仓库地址
$REPO_URL = "https://github.com/ShakeHsu/The-Current-Catcher.git"
$LOCAL_DIR = "C:\Users\XU\Documents\trae_projects\The Current Catcher"

# 检查目录是否存在，不存在则创建
if (-not (Test-Path $LOCAL_DIR)) {
    New-Item -ItemType Directory -Path $LOCAL_DIR
    Write-Host "已创建目录: $LOCAL_DIR"
}

# 进入目录
Set-Location $LOCAL_DIR

# 检查是否已经是Git仓库
if (Test-Path ".git") {
    Write-Host "仓库已存在，正在拉取最新代码..."
    git pull origin main
} else {
    Write-Host "正在克隆仓库..."
    git clone $REPO_URL
    Set-Location "The-Current-Catcher"
}

Write-Host "完成！"
Write-Host "当前目录: $(Get-Location)"
Write-Host "文件列表:"
Get-ChildItem
```

### 步骤2：运行脚本

右键点击 `download_from_github.ps1`，选择"使用PowerShell运行"

---

## 方式二：手动命令行操作

### 首次获取代码

```powershell
# 1. 进入项目目录
cd "C:\Users\XU\Documents\trae_projects\The Current Catcher"

# 2. 克隆仓库
git clone https://github.com/ShakeHsu/The-Current-Catcher.git

# 3. 进入项目目录
cd The-Current-Catcher

# 4. 查看文件
dir
```

### 后续同步（修改后上传）

```powershell
# 1. 进入项目目录
cd "C:\Users\XU\Documents\trae_projects\The Current Catcher\The-Current-Catcher"

# 2. 查看修改状态
git status

# 3. 添加修改的文件
git add .

# 4. 提交修改
git commit -m "更新了策略代码"

# 5. 推送到GitHub
git push origin main
```

### 获取最新代码（在其他电脑上）

```powershell
# 1. 进入项目目录
cd "C:\Users\XU\Documents\trae_projects\The Current Catcher\The-Current-Catcher"

# 2. 拉取最新代码
git pull origin main
```

---

## 方式三：使用GitHub网页下载

1. 访问：https://github.com/ShakeHsu/The-Current-Catcher
2. 点击绿色"Code"按钮
3. 选择"Download ZIP"
4. 解压到目标目录

---

## 常用Git命令

| 命令 | 说明 |
|------|------|
| `git status` | 查看修改状态 |
| `git add .` | 添加所有修改 |
| `git commit -m "说明"` | 提交修改 |
| `git push` | 推送到GitHub |
| `git pull` | 拉取最新代码 |
| `git log` | 查看提交历史 |
| `git diff` | 查看修改内容 |

---

## 推荐工作流程

### 在电脑A上修改代码

```powershell
# 1. 拉取最新代码
cd "C:\Users\XU\Documents\trae_projects\The Current Catcher\The-Current-Catcher"
git pull

# 2. 在VS Code中修改代码
# ...

# 3. 提交修改
git add .
git commit -m "优化了买入条件"

# 4. 推送到GitHub
git push
```

### 在电脑B上获取代码

```powershell
# 1. 拉取最新代码
cd "C:\Users\XU\Documents\trae_projects\The Current Catcher\The-Current-Catcher"
git pull

# 2. 现在代码已同步，可以继续工作
```

---

## 注意事项

1. **首次使用**：需要先安装Git
   - 下载：https://git-scm.com/download/win
   - 安装后重启终端

2. **配置Git**（首次使用时）
   ```powershell
   git config --global user.name "Your Name"
   git config --global user.email "your.email@example.com"
   ```

3. **GitHub Token**（如果需要）
   - 访问：https://github.com/settings/tokens
   - 生成Personal Access Token
   - 选择"repo"权限

4. **冲突处理**
   - 如果出现冲突，先 `git pull`
   - 手动解决冲突后，再 `git push`

---

## 快速开始

如果您想立即开始，最简单的方法：

1. **下载代码**：访问 https://github.com/ShakeHsu/The-Current-Catcher 点击"Download ZIP"
2. **解压**：解压到目标目录
3. **开始工作**：在VS Code中打开项目

需要我帮您创建PowerShell脚本吗？