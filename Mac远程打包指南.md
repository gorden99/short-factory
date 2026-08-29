# 短稿工厂 - Mac 桌面版远程打包指南

## 为什么需要远程打包？

Electron 打包 Mac 应用（.dmg/.app）**必须在 macOS 系统上执行**（依赖 Mac 专属工具 `hdiutil`、`iconutil`、`codesign`），Windows 上无法直接生成。

本方案使用 **GitHub Actions 云端 Mac 机器**自动打包，免费、无需自己买 Mac。

---

## 一、前置准备

1. 注册 GitHub 账号：https://github.com
2. 安装 Git：https://git-scm.com/download/win（安装时一路下一步即可）

---

## 二、创建 GitHub 仓库

1. 登录 GitHub，点击右上角 **+** → **New repository**
2. 仓库名：`short-factory`（或任意名字）
3. 选择 **Public**（公开，免费额度无限制）或 **Private**（私有也有免费 Actions 额度）
4. **不要**勾选 "Add a README file"、"Add .gitignore"、"Choose a license"（我们本地已有）
5. 点击 **Create repository**

创建后会看到一个仓库地址，类似：`https://github.com/你的用户名/short-factory.git`

---

## 三、推送代码到 GitHub

打开 **PowerShell** 或 **CMD**，执行以下命令（把 `你的用户名` 替换成你的 GitHub 用户名）：

```powershell
cd "L:\工具APP开发项目\短视频工场\官网与安装包"

# 初始化 git（如果还没初始化）
git init
git branch -M main

# 添加所有文件（.gitignore 会自动排除 node_modules、安装包等大文件）
git add .

# 提交
git commit -m "短稿工厂 - 初始化提交（含 Mac 远程打包配置）"

# 关联远程仓库（替换成你的仓库地址）
git remote add origin https://github.com/你的用户名/short-factory.git

# 推送
git push -u origin main
```

推送时会要求输入 GitHub 用户名和密码。
> 注意：GitHub 已不支持账号密码，需要用 **Personal Access Token (PAT)** 代替密码。
> 生成方法：GitHub 右上角头像 → Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token → 勾选 `repo` 权限 → 生成。把生成的 token 当密码输入。

---

## 四、触发 Mac 打包

### 方式 1：自动触发（推荐）
推送代码后，GitHub Actions 会**自动**开始打包 Mac 版（因为 workflow 配置了 push 触发）。

### 方式 2：手动触发
1. 打开你的 GitHub 仓库页面
2. 点击顶部 **Actions** 标签
3. 左侧选择 **"打包 Mac 桌面版"**
4. 点击右侧 **Run workflow** → 选择 `main` 分支 → 点击 **Run workflow**

---

## 五、查看打包进度和下载

1. 在 **Actions** 页面，点击最新的一次工作流运行
2. 可以看到实时日志，大约 **5-15 分钟**完成（取决于网络）
3. 打包成功后，页面底部会出现 **Artifacts** 区域
4. 点击 **"短稿工厂-Mac安装包"** 下载 zip 压缩包
5. 解压后得到 4 个 .dmg 文件：
   - `短稿工场-Mac-x64.dmg`（Intel Mac）
   - `短稿工场-Mac-arm64.dmg`（M1/M2/M3/M4 Mac）
   - `短稿工场个人版-Mac-x64.dmg`
   - `短稿工场个人版-Mac-arm64.dmg`

---

## 六、Mac 上安装说明

把 .dmg 文件传到 Mac（微信/U盘/网盘均可），双击打开，把"短稿工场"拖到 Applications 文件夹即可。

> 首次打开可能提示"无法打开，因为无法验证开发者"。解决方法：
> 右键点击应用 → 选择"打开" → 在弹窗中再次点击"打开"。
> （这是因为没有苹果开发者证书签名，不影响使用。后续可以购买苹果开发者账号（$99/年）进行签名。）

---

## 七、已配置的内容

| 文件 | 说明 |
|---|---|
| `.github/workflows/build-mac.yml` | GitHub Actions 打包脚本 |
| `electron/package.json` | MCN 版，已加 `mac` 配置和 `dist:mac` 脚本 |
| `electron-personal/package.json` | 个人版，已加 `mac` 配置和 `dist:mac` 脚本 |
| `electron/build/icon.iconset/` | MCN 版 Mac 图标集（10 个尺寸） |
| `electron-personal/build/icon.iconset/` | 个人版 Mac 图标集（10 个尺寸） |
| `.gitignore` | 排除 node_modules、安装包等大文件 |

---

## 八、常见问题

**Q: 打包失败怎么办？**
A: 在 Actions 页面点击失败的任务，查看红色错误日志。常见原因：
- 网络问题导致 npm install 失败 → 重新触发即可
- 图标生成失败 → 检查 `build/icon.iconset/` 目录是否有 10 个 png 文件

**Q: 能打包 Windows 版吗？**
A: 可以，workflow 可以扩展加 Windows runner。但你已经在本地打包好了 Windows 版，不需要重复。

**Q: 打包的 .dmg 有多大？**
A: 每个约 80-100MB（Electron 应用体积较大，正常现象）。

**Q: 免费额度够吗？**
A: GitHub 免费账号每月有 2000 分钟 Actions 额度（公开仓库无限）。一次 Mac 打包约 10 分钟，完全够用。

**Q: 以后更新代码后怎么重新打包？**
A: 直接 `git push` 推送新代码，会自动触发重新打包。或者在 Actions 页面手动触发。
