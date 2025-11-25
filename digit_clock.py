import tkinter as tk
from tkinter import font
from tkinter import simpledialog, messagebox  # 用于创建输入对话框和显示消息
import time
import datetime
import platform
import winsound  # 用于Windows系统的声音提醒
import json  # 用于数据持久化存储
import os  # 用于文件路径操作

# 尝试导入ctypes用于调用系统API
use_ctype = False
try:
    import ctypes
    use_ctype = platform.system() == 'Windows'
except ImportError:
    pass

# 定义常量
if use_ctype:
    # 定义Windows API常量
    ES_CONTINUOUS = 0x80000000
    ES_SYSTEM_REQUIRED = 0x00000001
    ES_DISPLAY_REQUIRED = 0x00000002

class DigitalClock(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("数码管时钟")
        # 计时数据存储文件路径
        self.timer_data_file = os.path.join(os.path.expanduser("~"), ".digital_clock_timer.json")
        # 窗口设置为无边框
        self.overrideredirect(True)
        # 设置窗口始终在最前面
        self.attributes('-topmost', True)
        # 设置窗口背景为透明
        self.attributes('-alpha', 0.95)
        # 窗口可以拖动
        self.bind("<Button-1>", self.start_move)
        self.bind("<B1-Motion>", self.on_move)
        # 右键点击关闭窗口
        self.bind("<Button-3>", self.close_window)
        # F11键切换全屏/窗口模式 - 使用bind_all确保能接收事件
        self.bind_all("<F11>", self.toggle_fullscreen)
        # ESC键关闭应用
        self.bind_all("<Escape>", self.close_window)
        # 初始化全屏状态
        self.fullscreen = False
        
        # 快捷键绑定 - 使用bind_all确保无论焦点在哪里都能接收键盘事件
        self.bind_all("<space>", self.on_space_press)  # 空格：开始/暂停计时
        # 同时绑定大小写字母
        self.bind_all("r", self.on_r_press)            # r键：重置计时
        self.bind_all("R", self.on_r_press)            # R键：重置计时
        self.bind_all("c", self.on_c_press)            # c键：切换回时钟模式
        self.bind_all("C", self.on_c_press)            # C键：切换回时钟模式
        self.bind_all("t", self.on_t_press)            # t键：切换到正向计时模式
        self.bind_all("T", self.on_t_press)            # T键：切换到正向计时模式
        self.bind_all("d", self.on_d_press)            # d键：切换到倒计时模式
        self.bind_all("D", self.on_d_press)            # D键：切换到倒计时模式
        
        # 计时功能相关变量
        self.mode = "clock"  # clock, timer, countdown
        self.timer_running = False
        self.timer_start_time = None
        self.timer_paused_time = 0
        self.timer_accumulated = 0
        self.countdown_time = 0  # 倒计时总时间（秒）
        self.countdown_start = None
        
        # 设置窗口大小
        self.geometry("400x150")
        
        # 创建数码管字体
        self.digit_font = font.Font(family='DS-Digital', size=70, weight='normal')
        
        # 创建时间显示标签
        self.time_label = tk.Label(
            self,
            font=self.digit_font,
            bg='#000000',
            fg='#00FF00',  # 绿色数码管效果
            bd=0,
            padx=20,
            pady=10
        )
        self.time_label.pack(fill=tk.BOTH, expand=True)
        
        # 加载计时数据
        self.load_saved_timer_data()
        # 更新时间
        self.update_time()
    
    def update_time(self):
        # 根据当前模式更新显示
        if self.mode == "clock":
            # 时钟模式
            current_time = datetime.datetime.now().strftime("%H:%M")
            self.time_label.config(text=current_time)
        elif self.mode == "timer":
            # 正向计时模式
            if self.timer_running:
                # 计算经过的时间
                elapsed = time.time() - self.timer_start_time + self.timer_accumulated
                hours, remainder = divmod(int(elapsed), 3600)
                minutes, seconds = divmod(remainder, 60)
                timer_display = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                self.time_label.config(text=timer_display)
        elif self.mode == "countdown":
            # 倒计时模式
            if self.countdown_start is not None:
                elapsed = time.time() - self.countdown_start
                remaining = max(0, self.countdown_time - elapsed)
                hours, remainder = divmod(int(remaining), 3600)
                minutes, seconds = divmod(remainder, 60)
                countdown_display = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                self.time_label.config(text=countdown_display)
                # 检查倒计时是否结束
                if remaining <= 0 and self.timer_running:
                    self.timer_running = False
                    self.time_label.config(text="00:00:00")
                    # 调用闹钟提醒功能
                    self.alarm()
        
        # 防止系统自动息屏：通过Windows API保持系统活动
        if use_ctype:
            # 使用Windows API设置系统保持活动状态
            # 这是防止系统休眠和显示器关闭的最可靠方法
            ctypes.windll.kernel32.SetThreadExecutionState(
                ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
            )
        else:
            # 备用方法：通过生成鼠标移动事件尝试重置系统活动计时器
            self.event_generate("<Motion>")
        
        # 每1000毫秒更新一次
        self.after(1000, self.update_time)
    
    def start_move(self, event):
        self.x = event.x
        self.y = event.y
    
    def on_move(self, event):
        x = self.winfo_pointerx() - self.x
        y = self.winfo_pointery() - self.y
        self.geometry(f"+{x}+{y}")
    
    def close_window(self, event):
        # 右键点击关闭窗口
        self.destroy()
    
    def toggle_fullscreen(self, event=None):
        # 切换全屏/窗口模式
        self.fullscreen = not self.fullscreen
        
        if self.fullscreen:
            # 保存当前窗口状态和属性
            self.old_geometry = self.geometry()
            self.old_overrideredirect = self.overrideredirect()
            # 临时禁用overrideredirect以允许全屏
            self.overrideredirect(False)
            # 进入全屏模式
            self.attributes('-fullscreen', True)
            # 调整字体大小以适应屏幕
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            font_size = int(screen_height * 0.3)  # 全屏时字体大小为屏幕高度的30%
            self.digit_font.configure(size=font_size)
        else:
            # 退出全屏模式
            self.attributes('-fullscreen', False)
            # 恢复原来的窗口大小和位置
            self.geometry(self.old_geometry)
            # 恢复原来的字体大小
            self.digit_font.configure(size=70)
            # 恢复overrideredirect属性
            self.overrideredirect(self.old_overrideredirect)
    
    def toggle_timer(self):
        # 切换计时状态（开始/暂停）
        if not self.timer_running:
            # 开始计时
            self.timer_running = True
            self.timer_start_time = time.time()
            # 如果是时钟模式切换到计时模式
            if self.mode == "clock":
                self.mode = "timer"
                # 重置计时显示
                self.timer_accumulated = 0
                self.time_label.config(text="00:00:00")
        else:
            # 暂停计时
            self.timer_running = False
            # 累计已计时时间
            self.timer_accumulated += time.time() - self.timer_start_time
            self.timer_start_time = None
            # 保存计时数据
            self.save_timer_data()
    
    def reset_timer(self):
        # 重置计时
        self.timer_running = False
        self.timer_accumulated = 0
        self.timer_start_time = None
        self.timer_paused_time = 0
        # 如果当前是计时模式，显示0
        if self.mode == "timer":
            self.time_label.config(text="00:00:00")
    
    def save_timer_data(self):
        """保存计时数据到文件"""
        try:
            data = {
                "timer_accumulated": self.timer_accumulated,
                "mode": self.mode
            }
            with open(self.timer_data_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"保存计时数据失败: {e}")
    
    def load_timer_data(self):
        """从文件加载计时数据"""
        try:
            if os.path.exists(self.timer_data_file):
                with open(self.timer_data_file, 'r') as f:
                    data = json.load(f)
                    return data
        except Exception as e:
            print(f"加载计时数据失败: {e}")
        return None
    
    def load_saved_timer_data(self):
        """在初始化时加载并应用保存的计时数据"""
        data = self.load_timer_data()
        if data:
            self.timer_accumulated = data.get("timer_accumulated", 0)
            saved_mode = data.get("mode", "clock")
            # 如果保存的模式是计时模式，自动切换到计时模式并显示保存的时间
            if saved_mode == "timer" and self.timer_accumulated > 0:
                self.mode = "timer"
                # 显示保存的计时时间
                hours, remainder = divmod(int(self.timer_accumulated), 3600)
                minutes, seconds = divmod(remainder, 60)
                timer_display = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                self.time_label.config(text=timer_display)
    
    def switch_to_clock(self):
        # 切换回时钟模式
        self.mode = "clock"
        self.timer_running = False
        self.countdown_start = None
    
    def set_countdown(self, hours=0, minutes=0, seconds=0):
        # 设置倒计时时间（秒）
        self.countdown_time = hours * 3600 + minutes * 60 + seconds
        self.mode = "countdown"
        self.timer_running = False
        self.countdown_start = None
        # 显示设置的倒计时时间
        hours_display, remainder = divmod(self.countdown_time, 3600)
        minutes_display, seconds_display = divmod(remainder, 60)
        countdown_display = f"{hours_display:02d}:{minutes_display:02d}:{seconds_display:02d}"
        self.time_label.config(text=countdown_display)
    
    def toggle_countdown(self):
        # 切换倒计时状态（开始/暂停）
        if not self.timer_running:
            # 开始倒计时
            self.timer_running = True
            # 如果是第一次开始或从时钟模式切换过来，重置倒计时
            if self.countdown_start is None or self.mode != "countdown":
                self.mode = "countdown"
                # 显示设置的倒计时时间
                hours, remainder = divmod(int(self.countdown_time), 3600)
                minutes, seconds = divmod(int(remainder), 60)
                countdown_display = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                self.time_label.config(text=countdown_display)
            self.countdown_start = time.time()
        else:
            # 暂停倒计时
            self.timer_running = False
            # 计算已经过去的时间并更新剩余时间
            if self.countdown_start is not None:
                elapsed = time.time() - self.countdown_start
                self.countdown_time = max(0, self.countdown_time - elapsed)
                self.countdown_start = None
    
    def reset_countdown(self):
        # 重置倒计时
        self.timer_running = False
        self.countdown_start = None
        # 如果当前是倒计时模式，显示设置的时间
        if self.mode == "countdown":
            hours, remainder = divmod(self.countdown_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            countdown_display = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            self.time_label.config(text=countdown_display)
    
    def alarm(self):
        # 倒计时结束时的闹钟提醒
        try:
            # 播放系统提示音
            winsound.Beep(1000, 1000)  # 1000Hz，持续1000ms
            # 可以添加更多提示音或其他提醒方式
        except Exception as e:
            print(f"无法播放提醒音: {e}")
    
    def on_space_press(self, event=None):
        # 空格键：开始/暂停当前模式的计时
        if self.mode == "timer":
            self.toggle_timer()
        elif self.mode == "countdown":
            self.toggle_countdown()
        elif self.mode == "clock":
            # 从时钟模式按空格，默认开始正向计时
            self.toggle_timer()
    
    def on_r_press(self, event=None):
        # R键：重置当前模式的计时
        if self.mode == "timer":
            self.reset_timer()
            # 清除保存的计时数据文件
            try:
                if os.path.exists(self.timer_data_file):
                    os.remove(self.timer_data_file)
            except Exception as e:
                print(f"清除计时数据失败: {e}")
        elif self.mode == "countdown":
            self.reset_countdown()
    
    def on_c_press(self, event=None):
        # C键：切换回时钟模式
        self.switch_to_clock()
    
    def on_t_press(self, event=None):
        # T键：切换到正向计时模式
        if self.mode != "timer":
            self.mode = "timer"
            self.timer_running = False
            self.timer_start_time = None  # 停止计时但保留累计时间
            # 立即显示当前累计时间
            hours, remainder = divmod(int(self.timer_accumulated), 3600)
            minutes, seconds = divmod(remainder, 60)
            timer_display = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            self.time_label.config(text=timer_display)
    
    def show_countdown_dialog(self):
        # 显示倒计时设置对话框
        # 创建一个模态对话框获取用户输入的时间
        dialog = tk.Toplevel(self)
        dialog.title("设置倒计时")
        dialog.attributes('-topmost', True)
        dialog.geometry("300x200")
        
        # 设置对话框在主窗口中央
        dialog.transient(self)
        dialog.grab_set()
        
        # 创建标签和输入框
        tk.Label(dialog, text="小时:").grid(row=0, column=0, padx=10, pady=10)
        hour_var = tk.StringVar(value="0")
        hour_entry = tk.Entry(dialog, textvariable=hour_var, width=5)
        hour_entry.grid(row=0, column=1, padx=5, pady=10)
        
        tk.Label(dialog, text="分钟:").grid(row=1, column=0, padx=10, pady=10)
        minute_var = tk.StringVar(value="5")  # 默认5分钟
        minute_entry = tk.Entry(dialog, textvariable=minute_var, width=5)
        minute_entry.grid(row=1, column=1, padx=5, pady=10)
        
        tk.Label(dialog, text="秒钟:").grid(row=2, column=0, padx=10, pady=10)
        second_var = tk.StringVar(value="0")
        second_entry = tk.Entry(dialog, textvariable=second_var, width=5)
        second_entry.grid(row=2, column=1, padx=5, pady=10)
        
        # 结果变量
        result = [0, 0, 0]  # [小时, 分钟, 秒]
        
        def ok_pressed():
            # 获取用户输入并验证
            try:
                hours = int(hour_var.get())
                minutes = int(minute_var.get())
                seconds = int(second_var.get())
                
                # 验证输入的有效性
                if hours < 0 or minutes < 0 or seconds < 0:
                    tk.messagebox.showerror("错误", "请输入非负整数")
                    return
                if hours == 0 and minutes == 0 and seconds == 0:
                    tk.messagebox.showerror("错误", "请至少设置一个非零时间")
                    return
                
                # 存储结果
                result[0] = hours
                result[1] = minutes
                result[2] = seconds
                dialog.destroy()
            except ValueError:
                tk.messagebox.showerror("错误", "请输入有效的整数")
        
        # 创建按钮
        button_frame = tk.Frame(dialog)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        ok_button = tk.Button(button_frame, text="确定", command=ok_pressed)
        ok_button.pack(side=tk.LEFT, padx=10)
        
        cancel_button = tk.Button(button_frame, text="取消", command=dialog.destroy)
        cancel_button.pack(side=tk.LEFT, padx=10)
        
        # 等待对话框关闭
        self.wait_window(dialog)
        
        return result
    
    def on_d_press(self, event=None):
        # D键：切换到倒计时模式并显示设置对话框
        if self.mode != "countdown":
            # 显示倒计时设置对话框
            hours, minutes, seconds = self.show_countdown_dialog()
            # 如果用户没有取消且输入有效，则设置倒计时
            if hours > 0 or minutes > 0 or seconds > 0:
                self.set_countdown(hours=hours, minutes=minutes, seconds=seconds)

if __name__ == "__main__":
    try:
        # 尝试使用DS-Digital字体
        app = DigitalClock()
        app.mainloop()
    except Exception as e:
        # 如果没有安装DS-Digital字体，创建一个使用系统字体的备用版本
        print(f"警告: {e}")
        print("请安装DS-Digital字体以获得最佳效果，将使用系统默认字体继续...")
        
        # 创建备用时钟应用
        class FallbackClock(tk.Tk):
            def __init__(self):
                super().__init__()
                self.title("数码管时钟")
                # 计时数据存储文件路径
                self.timer_data_file = os.path.join(os.path.expanduser("~"), ".digital_clock_timer.json")
                # 加载计时数据
                self.load_saved_timer_data()
                self.overrideredirect(True)
                self.attributes('-topmost', True)
                self.attributes('-alpha', 0.95)
                self.bind("<Button-1>", self.start_move)
                self.bind("<B1-Motion>", self.on_move)
                self.bind("<Button-3>", self.close_window)
                # F11键切换全屏/窗口模式 - 使用bind_all确保能接收事件
                self.bind_all("<F11>", self.toggle_fullscreen)
                # ESC键关闭应用
                self.bind_all("<Escape>", self.close_window)
                # 初始化全屏状态
                self.fullscreen = False
                
                # 快捷键绑定 - 使用bind_all确保无论焦点在哪里都能接收键盘事件
                self.bind_all("<space>", self.on_space_press)  # 空格：开始/暂停计时
                # 同时绑定大小写字母
                self.bind_all("r", self.on_r_press)            # r键：重置计时
                self.bind_all("R", self.on_r_press)            # R键：重置计时
                self.bind_all("c", self.on_c_press)            # c键：切换回时钟模式
                self.bind_all("C", self.on_c_press)            # C键：切换回时钟模式
                self.bind_all("t", self.on_t_press)            # t键：切换到正向计时模式
                self.bind_all("T", self.on_t_press)            # T键：切换到正向计时模式
                self.bind_all("d", self.on_d_press)            # d键：切换到倒计时模式
                self.bind_all("D", self.on_d_press)            # D键：切换到倒计时模式
                
                # 计时功能相关变量
                self.mode = "clock"  # clock, timer, countdown
                self.timer_running = False
                self.timer_start_time = None
                self.timer_paused_time = 0
                self.timer_accumulated = 0
                self.countdown_time = 0  # 倒计时总时间（秒）
                self.countdown_start = None
                
                self.geometry("400x150")
                
                # 使用系统可用的等宽字体
                self.digit_font = font.Font(family='Courier', size=70, weight='bold')
                
                self.time_label = tk.Label(
                    self,
                    font=self.digit_font,
                    bg='#000000',
                    fg='#00FF00',
                    bd=0,
                    padx=20,
                    pady=10
                )
                self.time_label.pack(fill=tk.BOTH, expand=True)
                self.update_time()
            
            def update_time(self):
                # 根据当前模式更新显示
                if self.mode == "clock":
                    # 时钟模式
                    current_time = datetime.datetime.now().strftime("%H:%M")
                    self.time_label.config(text=current_time)
                elif self.mode == "timer":
                    # 正向计时模式
                    if self.timer_running:
                        # 计算经过的时间
                        elapsed = time.time() - self.timer_start_time + self.timer_accumulated
                        hours, remainder = divmod(int(elapsed), 3600)
                        minutes, seconds = divmod(remainder, 60)
                        timer_display = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                        self.time_label.config(text=timer_display)
                elif self.mode == "countdown":
                    # 倒计时模式
                    if self.countdown_start is not None:
                        elapsed = time.time() - self.countdown_start
                        remaining = max(0, self.countdown_time - elapsed)
                        hours, remainder = divmod(int(remaining), 3600)
                        minutes, seconds = divmod(remainder, 60)
                        countdown_display = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                        self.time_label.config(text=countdown_display)
                        # 检查倒计时是否结束
                        if remaining <= 0 and self.timer_running:
                            self.timer_running = False
                            self.time_label.config(text="00:00:00")
                            # 调用闹钟提醒功能
                            self.alarm()
                
                # 防止系统自动息屏：通过Windows API保持系统活动
                if use_ctype:
                    # 使用Windows API设置系统保持活动状态
                    ctypes.windll.kernel32.SetThreadExecutionState(
                        ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
                    )
                else:
                    # 备用方法：通过生成鼠标移动事件尝试重置系统活动计时器
                    self.event_generate("<Motion>")
                
                self.after(1000, self.update_time)
            
            def toggle_timer(self):
                # 切换计时状态（开始/暂停）
                if not self.timer_running:
                    # 开始计时
                    self.timer_running = True
                    self.timer_start_time = time.time()
                    # 如果是时钟模式切换到计时模式
                    if self.mode == "clock":
                        self.mode = "timer"
                        # 重置计时显示
                        self.timer_accumulated = 0
                        self.time_label.config(text="00:00:00")
                else:
                    # 暂停计时
                    self.timer_running = False
                    # 累计已计时时间
                    self.timer_accumulated += time.time() - self.timer_start_time
                    self.timer_start_time = None
                    # 保存计时数据
                    self.save_timer_data()
            
            def reset_timer(self):
                # 重置计时
                self.timer_running = False
                self.timer_accumulated = 0
                self.timer_start_time = None
                self.timer_paused_time = 0
                # 如果当前是计时模式，显示0
                if self.mode == "timer":
                    self.time_label.config(text="00:00:00")
            
            def save_timer_data(self):
                """保存计时数据到文件"""
                try:
                    data = {
                        "timer_accumulated": self.timer_accumulated,
                        "mode": self.mode
                    }
                    with open(self.timer_data_file, 'w') as f:
                        json.dump(data, f)
                except Exception as e:
                    print(f"保存计时数据失败: {e}")
            
            def load_timer_data(self):
                """从文件加载计时数据"""
                try:
                    if os.path.exists(self.timer_data_file):
                        with open(self.timer_data_file, 'r') as f:
                            data = json.load(f)
                            return data
                except Exception as e:
                    print(f"加载计时数据失败: {e}")
                return None
            
            def load_saved_timer_data(self):
                """在初始化时加载并应用保存的计时数据"""
                data = self.load_timer_data()
                if data:
                    self.timer_accumulated = data.get("timer_accumulated", 0)
                    saved_mode = data.get("mode", "clock")
                    # 如果保存的模式是计时模式，自动切换到计时模式并显示保存的时间
                    if saved_mode == "timer" and self.timer_accumulated > 0:
                        self.mode = "timer"
                        # 显示保存的计时时间
                        hours, remainder = divmod(int(self.timer_accumulated), 3600)
                        minutes, seconds = divmod(remainder, 60)
                        timer_display = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                        self.time_label.config(text=timer_display)
            
            def switch_to_clock(self):
                # 切换回时钟模式
                self.mode = "clock"
                self.timer_running = False
                self.countdown_start = None
            
            def set_countdown(self, hours=0, minutes=0, seconds=0):
                # 设置倒计时时间（秒）
                self.countdown_time = hours * 3600 + minutes * 60 + seconds
                self.mode = "countdown"
                self.timer_running = False
                self.countdown_start = None
                # 显示设置的倒计时时间
                hours_display, remainder = divmod(self.countdown_time, 3600)
                minutes_display, seconds_display = divmod(remainder, 60)
                countdown_display = f"{hours_display:02d}:{minutes_display:02d}:{seconds_display:02d}"
                self.time_label.config(text=countdown_display)
            
            def toggle_countdown(self):
                # 切换倒计时状态（开始/暂停）
                if not self.timer_running:
                    # 开始倒计时
                    self.timer_running = True
                    # 如果是第一次开始或从时钟模式切换过来，重置倒计时
                    if self.countdown_start is None or self.mode != "countdown":
                        self.mode = "countdown"
                        # 显示设置的倒计时时间
                        hours, remainder = divmod(self.countdown_time, 3600)
                        minutes, seconds = divmod(remainder, 60)
                        countdown_display = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                        self.time_label.config(text=countdown_display)
                    self.countdown_start = time.time()
                else:
                    # 暂停倒计时
                    self.timer_running = False
                    # 计算已经过去的时间并更新剩余时间
                    elapsed = time.time() - self.countdown_start
                    self.countdown_time = max(0, self.countdown_time - elapsed)
                    self.countdown_start = None
            
            def reset_countdown(self):
                # 重置倒计时
                self.timer_running = False
                self.countdown_start = None
                # 如果当前是倒计时模式，显示设置的时间
                if self.mode == "countdown":
                    hours, remainder = divmod(self.countdown_time, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    countdown_display = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                    self.time_label.config(text=countdown_display)
            
            def alarm(self):
                # 倒计时结束时的闹钟提醒
                try:
                    # 播放系统提示音
                    winsound.Beep(1000, 1000)  # 1000Hz，持续1000ms
                except Exception as e:
                    print(f"无法播放提醒音: {e}")
            
            def on_space_press(self, event=None):
                # 空格键：开始/暂停当前模式的计时
                if self.mode == "timer":
                    self.toggle_timer()
                elif self.mode == "countdown":
                    self.toggle_countdown()
                elif self.mode == "clock":
                    # 从时钟模式按空格，默认开始正向计时
                    self.toggle_timer()
            
            def on_r_press(self, event=None):
                # R键：重置当前模式的计时
                if self.mode == "timer":
                    self.reset_timer()
                    # 清除保存的计时数据文件
                    try:
                        if os.path.exists(self.timer_data_file):
                            os.remove(self.timer_data_file)
                    except Exception as e:
                        print(f"清除计时数据失败: {e}")
                elif self.mode == "countdown":
                    self.reset_countdown()
            
            def on_c_press(self, event=None):
                # C键：切换回时钟模式
                self.switch_to_clock()
            
            def on_t_press(self, event=None):
                # T键：切换到正向计时模式
                if self.mode != "timer":
                    self.mode = "timer"
                    self.timer_running = False
                    self.timer_start_time = None  # 停止计时但保留累计时间
                    # 立即显示当前累计时间
                    hours, remainder = divmod(int(self.timer_accumulated), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    timer_display = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                    self.time_label.config(text=timer_display)
            
            def show_countdown_dialog(self):
                # 显示倒计时设置对话框
                # 创建一个模态对话框获取用户输入的时间
                dialog = tk.Toplevel(self)
                dialog.title("设置倒计时")
                dialog.attributes('-topmost', True)
                dialog.geometry("300x200")
                
                # 设置对话框在主窗口中央
                dialog.transient(self)
                dialog.grab_set()
                
                # 创建标签和输入框
                tk.Label(dialog, text="小时:").grid(row=0, column=0, padx=10, pady=10)
                hour_var = tk.StringVar(value="0")
                hour_entry = tk.Entry(dialog, textvariable=hour_var, width=5)
                hour_entry.grid(row=0, column=1, padx=5, pady=10)
                
                tk.Label(dialog, text="分钟:").grid(row=1, column=0, padx=10, pady=10)
                minute_var = tk.StringVar(value="5")  # 默认5分钟
                minute_entry = tk.Entry(dialog, textvariable=minute_var, width=5)
                minute_entry.grid(row=1, column=1, padx=5, pady=10)
                
                tk.Label(dialog, text="秒钟:").grid(row=2, column=0, padx=10, pady=10)
                second_var = tk.StringVar(value="0")
                second_entry = tk.Entry(dialog, textvariable=second_var, width=5)
                second_entry.grid(row=2, column=1, padx=5, pady=10)
                
                # 结果变量
                result = [0, 0, 0]  # [小时, 分钟, 秒]
                
                def ok_pressed():
                    # 获取用户输入并验证
                    try:
                        hours = int(hour_var.get())
                        minutes = int(minute_var.get())
                        seconds = int(second_var.get())
                        
                        # 验证输入的有效性
                        if hours < 0 or minutes < 0 or seconds < 0:
                            messagebox.showerror("错误", "请输入非负整数")
                            return
                        if hours == 0 and minutes == 0 and seconds == 0:
                            messagebox.showerror("错误", "请至少设置一个非零时间")
                            return
                        
                        # 存储结果
                        result[0] = hours
                        result[1] = minutes
                        result[2] = seconds
                        dialog.destroy()
                    except ValueError:
                        messagebox.showerror("错误", "请输入有效的整数")
                
                # 创建按钮
                button_frame = tk.Frame(dialog)
                button_frame.grid(row=3, column=0, columnspan=2, pady=20)
                
                ok_button = tk.Button(button_frame, text="确定", command=ok_pressed)
                ok_button.pack(side=tk.LEFT, padx=10)
                
                cancel_button = tk.Button(button_frame, text="取消", command=dialog.destroy)
                cancel_button.pack(side=tk.LEFT, padx=10)
                
                # 等待对话框关闭
                self.wait_window(dialog)
                
                return result
                
            def on_d_press(self, event=None):
                # D键：切换到倒计时模式并显示设置对话框
                if self.mode != "countdown":
                    # 显示倒计时设置对话框
                    hours, minutes, seconds = self.show_countdown_dialog()
                    # 如果用户没有取消且输入有效，则设置倒计时
                    if hours > 0 or minutes > 0 or seconds > 0:
                        self.set_countdown(hours=hours, minutes=minutes, seconds=seconds)
            
            def start_move(self, event):
                self.x = event.x
                self.y = event.y
            
            def on_move(self, event):
                x = self.winfo_pointerx() - self.x
                y = self.winfo_pointery() - self.y
                self.geometry(f"+{x}+{y}")
            
            def close_window(self, event):
                self.destroy()
                
            def toggle_fullscreen(self, event=None):
                # 切换全屏/窗口模式
                self.fullscreen = not self.fullscreen
                
                if self.fullscreen:
                    # 保存当前窗口状态和属性
                    self.old_geometry = self.geometry()
                    self.old_overrideredirect = self.overrideredirect()
                    # 临时禁用overrideredirect以允许全屏
                    self.overrideredirect(False)
                    # 进入全屏模式
                    self.attributes('-fullscreen', True)
                    # 调整字体大小以适应屏幕
                    screen_width = self.winfo_screenwidth()
                    screen_height = self.winfo_screenheight()
                    font_size = int(screen_height * 0.3)  # 全屏时字体大小为屏幕高度的30%
                    self.digit_font.configure(size=font_size)
                else:
                    # 退出全屏模式
                    self.attributes('-fullscreen', False)
                    # 恢复原来的窗口大小和位置
                    self.geometry(self.old_geometry)
                    # 恢复原来的字体大小
                    self.digit_font.configure(size=70)
                    # 恢复overrideredirect属性
                    self.overrideredirect(self.old_overrideredirect)
        
        fallback_app = FallbackClock()
        fallback_app.mainloop()