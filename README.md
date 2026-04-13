# 📝 英语默写练习 - 完整使用指南

## 目录
- [快速开始](#快速开始)
- [文件说明](#文件说明)
- [导入新词库](#导入新词库)
- [公网部署](#公网部署)
- [格式规范](#格式规范)

---

## 快速开始

### 方式一：直接打开（推荐）
双击 `index.html`，用浏览器（Chrome/Edge/QQ浏览器）打开即可使用。

> 💡 建议使用 Chrome 浏览器，效果最佳。

### 方式二：启动本地服务器
```bash
cd english-dictation
python -m http.server 8765
```
然后浏览器访问 http://127.0.0.1:8765

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `index.html` | 主程序，默写练习网页 |
| `import_from_qqdocs.py` | 腾讯文档导入工具 |
| `deploy.py` | 一键部署脚本（公网穿透） |
| `README.md` | 本文档 |

---

## 导入新词库

### 方法一：通过网页批量导入（最简单）

1. 打开 `index.html`
2. 进入「**词库**」页面
3. 点击「**批量导入**」按钮
4. 选择或新建分组
5. 粘贴内容（格式见下方），点击「导入」

### 方法二：通过腾讯文档链接导入

1. 确保腾讯文档设置为「**任何人可查看**」
2. 复制文档链接
3. 运行导入工具：

```bash
# 安装依赖（首次使用）
pip install requests beautifulsoup4

# 运行导入工具
python import_from_qqdocs.py
```

4. 按提示粘贴腾讯文档链接
5. 生成的 `import_output.json` 或 `import_output.txt` 复制到网页批量导入框

### 方法三：命令行模式（批量处理多个文档）

```bash
python import_from_qqdocs.py "https://docs.qq.com/doc/文档ID" "分组名称"
```

---

## 公网部署

### 一键公网部署（推荐）

运行部署脚本：
```bash
python deploy.py
```

脚本会引导你选择：
- **ngrok**（推荐）：稳定，生成永久 https 地址
- **localtunnel**：无需注册，但可能被限速
- **局域网访问**：同 WiFi 下手机/平板可直接访问

### 手动部署

详见 `deploy.py` 中的「手动部署说明」，支持：
- ngrok
- Cloudflare Tunnel
- VPS + Nginx
- GitHub Pages

> ⚠️ **重要**：关闭部署窗口会停止服务。如需长期运行，推荐使用 VPS 或 GitHub Pages。

---

## 格式规范

### 腾讯文档格式要求

文档内容需符合以下格式之一：

```
英文内容 | 中文释义
focus on the key points | 专注于关键点
curiosity | 好奇心
appeal | 呼吁；恳求；上诉；吸引力
```

### 关键要求

| 要求 | 说明 |
|------|------|
| 使用 ` | ` 分隔 | 竖线两侧各有一个空格 |
| 每行一条 | 英文和中文之间用竖线分隔 |
| 中文在右侧 | 不要交换顺序 |

### 示例文档结构

```
# 每日词汇 Unit 1

focus on the key points | 专注于关键点
develop this important skill | 培养这一重要技能
come across things worth reporting | 遇到值得报道的事情
on one's mind | 萦绕在心头；惦记着
in one's mind | 在脑海里
...
```

---

## 常见问题

### Q: 导入后数据丢失？
A: 数据保存在浏览器本地存储（localStorage），清理浏览器或更换浏览器会丢失。建议定期导出备份。

### Q: 手机上显示不正常？
A: 请使用 Chrome 或 Safari 浏览器，确保网页缩放比例为 100%。

### Q: 腾讯文档抓取失败？
A: 请确保文档设置为「任何人可查看」，且网络可以正常访问 docs.qq.com。

### Q: 想删除内置词库？
A: 在词库页面，点击每个词条旁边的删除按钮（🗑️）逐条删除，或在浏览器控制台执行：
```javascript
localStorage.removeItem('english_dictation_db');
```
然后刷新页面重置。

---

## 技术信息

- **前端**：纯 HTML + CSS + JavaScript，无任何外部依赖
- **数据存储**：浏览器 localStorage
- **兼容浏览器**：Chrome、Edge、Firefox、Safari
- **响应式**：支持手机、平板、电脑
