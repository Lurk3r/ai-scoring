import json
import base64
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox, font
import os
import time

# Attempt to import necessary libraries, providing user-friendly errors if they are missing.
try:
    import requests
    from openai import OpenAI
    from json_repair import repair_json
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.edge.service import Service as EdgeService
    from webdriver_manager.microsoft import EdgeChromiumDriverManager
except ImportError as e:
    messagebox.showerror("缺少依赖库", f"程序需要以下库: requests, openai, json_repair, selenium, webdriver-manager. 请先通过 pip install 安装它们。\n错误: {e}")
    exit()

# --- Default Configuration ---
LOGIN_URL = "https://www.zhixue.com/htm-vessel/#/teacher"
DEFAULT_SYSTEM_PROMPT_FILE = 'system_prompt.txt'
DEFAULT_SYSTEM_PROMPT = """你是一位严格、严谨的初中地理阅卷老师。
你的任务是根据提供的“标准答案”和“评分标准”，对学生的“手写答案”进行打分。

【评分标准】
1.  完全符合“标准答案”或与“标准答案”意思一致，得满分。
2.  部分答对或意思相近，请根据符合程度酌情给分。
3.  错答、漏答或完全不相关，得0分。

【输出格式】
你必须以JSON格式返回结果，该JSON对象应包含三个字段：
1.  `得分`: 一个整数，表示最终给定的分数。
2.  `评价`: 对学生答案的简要评价（例如：“回答正确，思路清晰。”，“基本正确，但缺少关键点。”，“回答错误。”）。
3.  `扣分点`: 如果没有得满分，请明确指出具体的扣分原因。如果得了满分，此字段应为空字符串。

【示例】
标准答案：亚洲东部和南部地区。
学生手写答案：亚洲的东边和南边。
输出：
{
  "得分": 2,
  "评价": "回答正确，准确指出了区域。",
  "扣分点": ""
}
"""

# --- Core Logic Classes (from notebook) ---

class AIService:
    def __init__(self, api_key, vl_model, reasoning_model, system_prompt, status_callback):
        self.client = OpenAI(api_key=api_key, base_url="https://api.siliconflow.cn/v1")
        self.vl_model = vl_model
        self.reasoning_model = reasoning_model
        self.system_prompt = system_prompt
        self.status_callback = status_callback

    def recognize_handwriting(self, img_base64):
        self.status_callback("正在识别手写内容...")
        response = self.client.chat.completions.create(
            model=self.vl_model,
            messages=[
                {"role": "system", "content": "这是某张试卷中学生手写答案的截图，请识别并仅返回学生的手写作答内容，不要添加额外的描述。"},
                {"role": "user", "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}},
                    {"type": "text", "text": "识别并仅返回学生的手写作答内容。"}
                ]}
            ],
        )
        content = response.choices[0].message.content
        self.status_callback(f"✅ 手写内容识别结果：\n{content}")
        return content

    def get_score(self, handwriting):
        self.status_callback("正在根据标准答案进行评分...")
        response = self.client.chat.completions.create(
            model=self.reasoning_model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": handwriting}
            ],
            response_format={"type": "json_object"}
        )
        repaired_json_str = repair_json(response.choices[0].message.content)
        self.status_callback(f"✅ 评分JSON结果：\n{repaired_json_str}")
        score_data = json.loads(repaired_json_str)
        return score_data

class BrowserAutomator:
    def __init__(self, status_callback):
        self.browser = None
        self.status_callback = status_callback

    def start_browser(self):
        self.status_callback("正在启动浏览器驱动...")
        try:
            service = EdgeService(EdgeChromiumDriverManager().install())
            self.browser = webdriver.Edge(service=service)
            self.browser.implicitly_wait(15) # 增加隐式等待
            self.status_callback("✅ 浏览器启动成功。")
            return True
        except Exception as e:
            self.status_callback(f"❌ 浏览器启动失败: {e}")
            messagebox.showerror("浏览器错误", f"无法启动Edge浏览器。请确保已安装Edge浏览器并且驱动程序兼容。\n错误: {e}")
            return False

    def open_login_page(self, url):
        self.status_callback(f"正在打开登录页面: {url}")
        self.browser.get(url)
        self.status_callback("✅ 登录页面已打开。请在浏览器中手动完成登录操作。")

    def get_progress(self):
        try:
            total_elem = self.browser.find_element(By.XPATH, '/html/body/div/div/div[1]/div/div[2]/div/div[1]/div[1]/div[1]/div[2]/i/strong[2]')
            current_elem = self.browser.find_element(By.XPATH, '/html/body/div/div/div[1]/div/div[2]/div/div[1]/div[1]/div[1]/div[2]/i/strong[1]')
            total = int(total_elem.text)
            current = int(current_elem.text)
            return total, current
        except Exception as e:
            self.status_callback(f"❌ 无法获取批改进度: {e}")
            raise

    def get_student_answer_image_base64(self):
        try:
            img_element = self.browser.find_element(By.XPATH, '/html/body/div/div/div[1]/div/div[2]/div/div[1]/div[2]/div[1]/div[4]/div[2]/div[2]/div/div[1]/img')
            img_url = img_element.get_attribute('src')
            # Selenium 4+ can directly get screenshot of element
            img_data = img_element.screenshot_as_png
            return base64.b64encode(img_data).decode('utf-8')
        except Exception as e:
            self.status_callback(f"❌ 无法获取学生答案截图: {e}")
            raise

    def upload_score(self, score):
        try:
            self.status_callback(f"正在填入分数: {score}")
            input_element = self.browser.find_element(By.XPATH, '/html/body/div/div/div[1]/div/div[2]/div/div[2]/div/div[3]/div[2]/div[1]/ul[2]/li/input')
            input_element.clear()
            input_element.send_keys(score)
            
            self.status_callback("正在提交分数...")
            button_element = self.browser.find_element(By.XPATH, '/html/body/div/div/div[1]/div/div[2]/div/div[2]/div/div[3]/div[2]/div[1]/div[5]/button')
            button_element.click()
            time.sleep(2) # 等待页面刷新
            self.status_callback("✅ 分数提交成功，进入下一份。")
        except Exception as e:
            self.status_callback(f"❌ 上传分数失败: {e}")
            raise

    def quit(self):
        if self.browser:
            self.status_callback("正在关闭浏览器...")
            self.browser.quit()
            self.status_callback("✅ 浏览器已关闭。")

# --- Tkinter GUI Application ---

class GradingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("智学网自动阅卷助手 v1.0")
        self.root.geometry("800x700")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.automator = BrowserAutomator(self.log_status)
        self.ai_service = None
        self.is_grading = False

        # --- Setup UI ---
        self.setup_styles()
        self.create_widgets()

    def setup_styles(self):
        self.default_font = font.nametofont("TkDefaultFont")
        self.default_font.configure(family="Microsoft YaHei UI", size=10)
        self.title_font = font.Font(family="Microsoft YaHei UI", size=12, weight="bold")

    def create_widgets(self):
        # --- Top Frame for Configuration ---
        config_frame = tk.Frame(self.root, padx=10, pady=10)
        config_frame.pack(fill='x', side='top')

        # API Key
        tk.Label(config_frame, text="API Key:", font=self.default_font).grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.api_key_entry = tk.Entry(config_frame, width=60, show="*")
        self.api_key_entry.grid(row=0, column=1, sticky='ew', padx=5, pady=5)

        # --- Middle Frame for System Prompt ---
        prompt_frame = tk.LabelFrame(self.root, text="系统提示 (System Prompt)", padx=10, pady=10, font=self.title_font)
        prompt_frame.pack(fill='both', expand=True, padx=10, pady=5)

        self.prompt_text = scrolledtext.ScrolledText(prompt_frame, wrap=tk.WORD, height=10, font=("Microsoft YaHei UI", 10))
        self.prompt_text.pack(fill='both', expand=True)
        self.load_system_prompt()

        # --- Bottom Frame for Controls and Logging ---
        bottom_frame = tk.Frame(self.root, padx=10, pady=10)
        bottom_frame.pack(fill='both', expand=True, side='bottom')
        bottom_frame.columnconfigure(0, weight=1)
        bottom_frame.rowconfigure(1, weight=1)

        # Control Buttons
        control_button_frame = tk.Frame(bottom_frame)
        control_button_frame.grid(row=0, column=0, sticky='ew', pady=5)
        
        self.start_browser_btn = tk.Button(control_button_frame, text="1. 启动浏览器并登录", command=self.start_browser_and_login, bg="#4CAF50", fg="white", font=self.default_font)
        self.start_browser_btn.pack(side='left', padx=5)

        self.start_grading_btn = tk.Button(control_button_frame, text="2. 开始自动批改", command=self.start_grading_thread, state='disabled', bg="#f44336", fg="white", font=self.default_font)
        self.start_grading_btn.pack(side='left', padx=5)

        # Logging Area
        log_frame = tk.LabelFrame(bottom_frame, text="运行日志", padx=10, pady=10, font=self.title_font)
        log_frame.grid(row=1, column=0, sticky='nsew')
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)

        self.log_widget = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state='disabled', font=("Microsoft YaHei UI", 10))
        self.log_widget.grid(row=0, column=0, sticky='nsew')

    def log_status(self, message):
        def _update_log():
            self.log_widget.config(state='normal')
            self.log_widget.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
            self.log_widget.config(state='disabled')
            self.log_widget.see(tk.END)
        self.root.after(0, _update_log)

    def load_system_prompt(self):
        try:
            with open(DEFAULT_SYSTEM_PROMPT_FILE, 'r', encoding='utf-8') as f:
                prompt = f.read()
            self.prompt_text.insert('1.0', prompt)
        except FileNotFoundError:
            self.prompt_text.insert('1.0', DEFAULT_SYSTEM_PROMPT)
            self.log_status(f"警告: {DEFAULT_SYSTEM_PROMPT_FILE} 未找到，已加载默认系统提示。")

    def start_browser_and_login(self):
        self.start_browser_btn.config(state='disabled', text="浏览器运行中...")
        if self.automator.start_browser():
            self.automator.open_login_page(LOGIN_URL)
            if messagebox.askokcancel("请登录", "浏览器已打开。请在浏览器中手动完成登录，然后点击“确定”继续。"):
                self.start_grading_btn.config(state='normal')
                self.log_status("✅ 用户确认登录完成。现在可以开始批改。")
            else:
                self.log_status("❌ 用户取消了操作。")
                self.on_closing()
        else:
            self.start_browser_btn.config(state='normal', text="1. 启动浏览器并登录")


    def start_grading_thread(self):
        api_key = self.api_key_entry.get()
        if not api_key:
            messagebox.showerror("缺少API Key", "请输入您的API Key。")
            return

        self.is_grading = True
        self.start_grading_btn.config(state='disabled', text="批改进行中...")
        self.start_browser_btn.config(state='disabled')

        system_prompt = self.prompt_text.get("1.0", tk.END)
        self.ai_service = AIService(
            api_key=api_key,
            vl_model="Qwen/Qwen2.5-VL-32B-Instruct",
            reasoning_model="Qwen/Qwen3-14B",
            system_prompt=system_prompt,
            status_callback=self.log_status
        )

        # Run the grading process in a separate thread
        threading.Thread(target=self.run_grading_process, daemon=True).start()

    def run_grading_process(self):
        try:
            total, current = self.automator.get_progress()
            num_to_grade = total - current
            self.log_status(f"--- 开始批改任务 ---")
            self.log_status(f"共 {total} 份试卷，当前在第 {current} 份，还需批改 {num_to_grade} 份。")

            for i in range(num_to_grade):
                if not self.is_grading:
                    self.log_status("批改任务被用户终止。")
                    break
                
                self.log_status(f"\n--- 正在处理第 {current + i + 1} / {total} 份 ---")
                try:
                    img_base64 = self.automator.get_student_answer_image_base64()
                    handwriting = self.ai_service.recognize_handwriting(img_base64)
                    score_data = self.ai_service.get_score(handwriting)
                    score = score_data.get('得分', 0) # Safely get score
                    self.automator.upload_score(score)
                except Exception as e:
                    self.log_status(f"❌ 处理单份试卷时出错: {e}")
                    if not messagebox.askyesno("错误", f"处理一份试卷时发生错误:\n{e}\n\n是否继续批改下一份？"):
                        self.is_grading = False
                        break
            
            self.log_status("--- 批改任务完成 ---")

        except Exception as e:
            self.log_status(f"❌ 主流程发生严重错误: {e}")
            messagebox.showerror("严重错误", f"主流程发生严重错误: {e}")
        finally:
            self.root.after(0, self.reset_ui_after_grading)


    def reset_ui_after_grading(self):
        self.is_grading = False
        self.start_grading_btn.config(state='normal', text="2. 开始自动批改")
        self.start_browser_btn.config(state='normal', text="1. 启动浏览器并登录")
        messagebox.showinfo("完成", "所有指定的批改任务已执行完毕。")


    def on_closing(self):
        if messagebox.askokcancel("退出", "确定要退出程序吗？浏览器将会关闭。"):
            self.is_grading = False # Stop grading loop if running
            if self.automator:
                self.automator.quit()
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = GradingApp(root)
    root.mainloop()
