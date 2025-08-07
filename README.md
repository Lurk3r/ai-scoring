# 智学网 AI 自动阅卷助手 (AI-Scoring Assistant for Zhixue.com)

![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-stable-brightgreen)
![GUI](https://img.shields.io/badge/GUI-Tkinter-orange)

**智学网 AI 自动阅卷助手** 是一个桌面应用程序，旨在将教师从繁琐重复的阅卷工作中解放出来。它通过模拟人类操作，利用先进的视觉语言模型（Vision-Language Model, VLM）技术，实现了在智学网平台上对学生主观题手写答案的自动化识别、打分和提交。

---

## 核心特性

- **🤖 智能评分核心**:
  - **手写内容识别**: 集成强大的 `Qwen-VL` 模型，能准确识别学生在试卷图片中的手写文字。
  - **逻辑推理打分**: 利用 `Qwen` 系列大型语言模型，根据用户自定义的“标准答案”和“评分标准”对识别出的文字进行智能打分。
  - **结构化输出**: AI返回标准、可解析的JSON格式结果，包含`得分`、`评价`和`扣分点`，确保评分过程的透明和一致性。

- **🖥️ 浏览器自动化**:
  - **无缝集成**: 使用 `Selenium` 自动控制Edge浏览器，直接在智学网的阅卷页面上执行操作。
  - **自动化流程**: 自动抓取学生答题卡图片、在评分框中输入分数、并点击“下一份”按钮，实现阅卷流程的闭环自动化。

- **✨ 用户友好的图形界面**:
  - **简洁直观**: 基于 `Tkinter` 构建，提供清晰的图形用户界面（GUI），所有操作一目了然。
  - **实时日志**: 内置滚动日志窗口，实时显示程序运行状态、AI分析过程和潜在错误，让一切尽在掌握。
  - **高度可配置**: 用户可以直接在界面上修改AI的“系统提示词”（System Prompt），灵活调整评分标准以适应不同科目和题目的需求。

## 工作流程

项目的工作流程被设计为一个人机协作的模式，将AI的效率与教师的监督结合起来。

1.  **启动与登录**: 用户启动程序，点击按钮后，程序会自动打开一个浏览器窗口并导航至智学网登录页面。
2.  **人工登录**: 用户在浏览器中手动完成登录操作，确保账户安全。
3.  **开始自动批改**: 用户在程序界面点击“开始自动批改”。
4.  **循环批阅**: 程序接管浏览器，并开始循环执行以下任务：
    a. **获取图片**: 自动截取当前学生的答题卡图片。
    b. **识别文字**: 将图片发送给AI视觉模型进行手写识别。
    c. **分析评分**: 将识别出的文字和预设的评分标准一同发送给AI语言模型进行打分。
    d. **提交分数**: 将AI返回的分数填入网页的评分框。
    e. **进入下一份**: 模拟点击“提交”或“下一份”按钮，处理下一位学生。
5.  **完成**: 直到所有试卷批改完毕或用户手动停止。

## 安装与配置

在开始之前，请确保您的系统满足以下先决条件：

- **Python 3.9** 或更高版本。
- **Microsoft Edge** 浏览器已安装。

**第一步：克隆项目仓库**
```bash
git clone https://github.com/your-username/ai-scoring-zhixue.git
cd ai-scoring-zhixue
```

**第二步：创建虚拟环境并激活**
```bash
# Windows
python -m venv venv
venv\Scripts\activate
```

**第三步：安装依赖**

为了方便管理，建议创建一个 `requirements.txt` 文件，内容如下：

```txt
requests
openai
json_repair
selenium
webdriver-manager
```

然后通过 pip 一键安装：
```bash
pip install -r requirements.txt
```

**第四步：配置 API Key**

程序需要一个有效的 API Key 来访问 AI 模型。该 Key 来自于 [SiliconFlow](https://www.siliconflow.cn/) 或其他兼容 OpenAI 接口的服务。

## 使用指南

1.  **运行程序**:
    ```bash
    python ai-scoring.py
    ```
2.  **输入 API Key**: 在程序主界面的 "API Key" 输入框中，填入您的密钥。
3.  **(可选) 自定义评分标准**:
    - 程序启动时会尝试加载 `system_prompt.txt` 文件作为AI的评分标准。
    - 您可以修改此文件，或者直接在界面的“系统提示”文本框中编辑内容，以适应您的阅卷需求。
4.  **启动浏览器**: 点击 **`1. 启动浏览器并登录`** 按钮。程序会自动打开Edge浏览器。
5.  **手动登录**: 在打开的浏览器中，完成您的智学网账号登录。登录成功后，回到程序界面点击弹窗的“确定”。
6.  **开始批改**: 点击 **`2. 开始自动批改`** 按钮，程序将正式接管浏览器开始自动化阅卷。
7.  **监控与结束**:
    - 在“运行日志”窗口中观察整个过程。
    - 当所有试卷批改完成后，程序会提示。
    - 您可以随时关闭程序窗口来中止任务，程序会自动安全地关闭浏览器。

## 贡献

欢迎任何形式的贡献！如果您有好的想法或发现了Bug，请随时提出 Issue 或提交 Pull Request。

1.  Fork 本仓库
2.  创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3.  提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4.  推送到分支 (`git push origin feature/AmazingFeature`)
5.  打开一个 Pull Request

## 许可证

本项目采用 [MIT 许可证](LICENSE)授权。
