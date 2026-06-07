# 文件整理大师 📁

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**一键整理杂乱的文件夹** — 自动分类、批量重命名、重复检测，让文件井井有条。

## ✨ 功能

| 功能 | 说明 |
|------|------|
| 📂 **智能分类** | 按文件类型（图片、文档、音频、视频...）自动归类到子文件夹 |
| ✏️ **批量重命名** | 加日期前缀、序号编号、替换文字、全部转小写 |
| 🔍 **重复检测** | 用 MD5 哈希精准找出重复文件，释放磁盘空间 |
| 📊 **操作报告** | 整理完成后自动生成详细报告 |
| 🛡️ **安全预览** | 默认预览模式，加 `--go` 才真正执行操作 |

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 试用一下

```bash
# 先扫描看看文件夹里有什么
python -m organizer scan ~/Downloads

# 预览整理计划（不加 --go 不会真的移动文件）
python -m organizer organize ~/Downloads

# 确认无误后，真正执行整理
python -m organizer organize ~/Downloads --go
```

## 📖 完整用法

```
用法：python -m organizer <命令> [参数]

命令：
  scan       扫描目录，预览文件分类
  organize   整理目录中的文件
  rename     批量重命名文件
  dedup      查找重复文件
  full       一键整理（分类 + 去重 + 报告）
```

### 示例

```bash
# 扫描并预览分类
python -m organizer scan ~/Desktop

# 整理桌面（预览模式）
python -m organizer organize ~/Desktop

# 真正整理桌面
python -m organizer organize ~/Desktop --go

# 给所有照片加日期前缀
python -m organizer rename ~/Photos --pattern date

# 把照片用序号重命名
python -m organizer rename ~/Photos --pattern number --text "旅行_"

# 文件名全部转小写
python -m organizer rename ~/Downloads --pattern lower

# 替换文件名中的文字
python -m organizer rename ~/Documents --pattern replace --text "旧文字->新文字"

# 查找重复文件
python -m organizer dedup ~/Pictures

# 删除重复文件（保留最新的）
python -m organizer dedup ~/Pictures --delete

# 一键全搞定
python -m organizer full ~/Desktop --go
```

## 🛠️ 自定义分类规则

编辑项目根目录下的 `config.yaml`，你可以：

- **添加新的文件类型**：在对应分类下加上新的扩展名
- **新增分类**：添加新的分类和它包含的扩展名
- **修改文件夹名**：改变整理后子文件夹的名字

```yaml
categories:
  Images:
    extensions: [.jpg, .png, .gif, ...]
    folder: 图片        # ← 改成你想要的名字
```

## 🧪 运行测试

```bash
pytest tests/ -v
```

## 📁 项目结构

```
my_first_project/
├── config.yaml              # 分类规则配置
├── requirements.txt         # 依赖包
├── README.md                # 项目文档
├── organizer/               # 主代码
│   ├── cli.py               # 命令行界面
│   ├── scanner.py           # 文件扫描分类
│   ├── organizer.py         # 核心整理逻辑
│   ├── renamer.py           # 批量重命名
│   ├── dedup.py             # 重复检测
│   ├── reporter.py          # 报告生成
│   └── utils.py             # 工具函数
└── tests/
    └── test_organizer.py    # 测试代码
```

## 🔧 技术栈

- Python 3.10+
- [Rich](https://github.com/Textualize/rich) — 漂亮的终端输出
- [PyYAML](https://pyyaml.org/) — 配置文件解析
- [Pytest](https://pytest.org/) — 测试框架

## 📄 License

MIT — 随意使用、修改和分享。
