import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pyautogui
import time
import json
import threading
import os
from pynput import mouse, keyboard
import keyboard as kb

class AutomationRecorder:
    def __init__(self, root):
        self.root = root
        self.root.title("ضبط و پخش خودکار حرکات موس")
        self.root.geometry("700x600")

        # متغیرها
        self.recording = False
        self.playing = False
        self.actions = []
        self.play_count = 0
        self.play_times = tk.IntVar(value=1)
        self.delay_var = tk.DoubleVar(value=0.0)  # تاخیر بین تکرارها
        self.speed_var = tk.DoubleVar(value=1.0)  # سرعت پخش (1.0 = سرعت ضبط)
        self.output_folder = "automation_rolls"
        os.makedirs(self.output_folder, exist_ok=True)

        # ایجاد ویجت‌ها
        self.create_widgets()

        # تنظیمات pyautogui
        pyautogui.FAILSAFE = False

        # ثبت دکمه‌های میانبر
        self.setup_hotkeys()

    def create_widgets(self):
        # فریم ضبط
        record_frame = ttk.LabelFrame(self.root, text="ضبط رول", padding=10)
        record_frame.pack(pady=10, padx=10, fill=tk.X)

        self.record_button = ttk.Button(
            record_frame,
            text="شروع ضبط (F1)",
            command=self.toggle_recording,
        )
        self.record_button.pack(side=tk.LEFT, padx=5)

        self.status_label = ttk.Label(record_frame, text="آماده ضبط", foreground="blue")
        self.status_label.pack(side=tk.LEFT, padx=5)

        ttk.Label(record_frame, text="دکمه توقف ضبط: F2").pack(side=tk.LEFT, padx=5)

        # فریم پخش
        play_frame = ttk.LabelFrame(self.root, text="پخش رول", padding=10)
        play_frame.pack(pady=10, padx=10, fill=tk.X)

        ttk.Label(play_frame, text="تکرار:").pack(side=tk.LEFT, padx=5)
        ttk.Spinbox(play_frame, from_=1, to=100, textvariable=self.play_times, width=5).pack(side=tk.LEFT, padx=5)

        ttk.Label(play_frame, text="تاخیر بین تکرارها (ثانیه):").pack(side=tk.LEFT, padx=5)
        ttk.Spinbox(play_frame, from_=0.0, to=10, increment=0.1, textvariable=self.delay_var, width=5).pack(side=tk.LEFT, padx=5)

        # اسلایدر سرعت
        speed_frame = ttk.Frame(play_frame)
        speed_frame.pack(side=tk.LEFT, padx=5)

        ttk.Label(speed_frame, text="سرعت پخش:").pack(side=tk.LEFT)
        self.speed_scale = ttk.Scale(
            speed_frame,
            from_=0.1,
            to=5,
            orient=tk.HORIZONTAL,
            variable=self.speed_var,
            command=lambda v: self.speed_label.config(text=f"{float(v):.1f}x")
        )
        self.speed_scale.pack(side=tk.LEFT, padx=5)
        self.speed_label = ttk.Label(speed_frame, text=f"{self.speed_var.get():.1f}x")
        self.speed_label.pack(side=tk.LEFT)

        self.play_button = ttk.Button(
            play_frame,
            text="پخش رول",
            command=self.start_playback,
        )
        self.play_button.pack(side=tk.LEFT, padx=5)

        self.stop_play_button = ttk.Button(
            play_frame,
            text="توقف پخش (Ctrl)",
            command=self.stop_playback,
        )
        self.stop_play_button.pack(side=tk.LEFT, padx=5)
        self.stop_play_button.config(state=tk.DISABLED)

        # فریم لیست رول‌ها
        rolls_frame = ttk.LabelFrame(self.root, text="رول‌های ذخیره‌شده", padding=10)
        rolls_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        self.rolls_listbox = tk.Listbox(
            rolls_frame,
            height=10,
            font=("Arial", 10),
            bg="#f9f9f9",
            selectbackground="#4CAF50"
        )
        self.rolls_listbox.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        scrollbar = ttk.Scrollbar(rolls_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.rolls_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.rolls_listbox.yview)

        # دکمه‌های مدیریت رول
        button_frame = ttk.Frame(rolls_frame)
        button_frame.pack(fill=tk.X, pady=5)

        ttk.Button(
            button_frame,
            text="ذخیره رول",
            command=self.save_roll,
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame,
            text="بارگذاری رول",
            command=self.load_roll,
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame,
            text="حذف رول",
            command=self.delete_roll,
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame,
            text="تازه‌سازی",
            command=self.refresh_rolls,
        ).pack(side=tk.RIGHT, padx=5)

        # فریم اطلاعات
        info_frame = ttk.LabelFrame(self.root, text="اطلاعات", padding=10)
        info_frame.pack(pady=10, padx=10, fill=tk.X)

        self.info_label = ttk.Label(
            info_frame,
            text="آماده استفاده | دکمه‌ها: F1=شروع ضبط, F2=توقف ضبط, Ctrl=توقف پخش"
        )
        self.info_label.pack()

        # تازه‌سازی لیست رول‌ها
        self.refresh_rolls()

    def setup_hotkeys(self):
        kb.add_hotkey('F1', self.start_recording_hotkey)
        kb.add_hotkey('F2', self.stop_recording_hotkey)
        kb.add_hotkey('Ctrl', self.stop_playback_hotkey)

    def start_recording_hotkey(self, event=None):
        if not self.recording:
            self.start_recording()

    def stop_recording_hotkey(self, event=None):
        if self.recording:
            self.stop_recording()

    def stop_playback_hotkey(self, event=None):
        if self.playing:
            self.stop_playback()

    def toggle_recording(self):
        if not self.recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        self.recording = True
        self.actions = []
        self.record_button.config(text="توقف ضبط (F2)")
        self.status_label.config(text="در حال ضبط...", foreground="red")
        self.info_label.config(text="در حال ضبط حرکات موس و کلیک‌ها... (F2 برای توقف)")

        # شروع گوش دادن به موس
        self.mouse_listener = mouse.Listener(on_move=self.on_move, on_click=self.on_click)
        self.mouse_listener.start()

    def stop_recording(self):
        self.recording = False
        self.record_button.config(text="شروع ضبط (F1)")
        self.status_label.config(text="آماده ضبط", foreground="blue")
        self.info_label.config(text=f"رول ضبط شد: {len(self.actions)} عمل")

        if hasattr(self, 'mouse_listener'):
            self.mouse_listener.stop()
            self.mouse_listener.join()

    def on_move(self, x, y):
        if self.recording:
            self.actions.append({"type": "move", "x": x, "y": y, "time": time.time()})

    def on_click(self, x, y, button, pressed):
        if self.recording and pressed:
            button_str = self.normalize_button(button)
            self.actions.append({
                "type": "click",
                "x": x,
                "y": y,
                "button": button_str,
                "time": time.time()
            })

    def normalize_button(self, button):
        if button == mouse.Button.left:
            return 'left'
        elif button == mouse.Button.right:
            return 'right'
        elif button == mouse.Button.middle:
            return 'middle'
        else:
            return 'left'

    def start_playback(self):
        if not self.actions:
            messagebox.showwarning("هشدار", "هیچ رولی برای پخش وجود ندارد!")
            return

        self.playing = True
        self.play_count = 0
        self.play_button.config(state=tk.DISABLED)
        self.stop_play_button.config(state=tk.NORMAL)
        self.info_label.config(text=f"در حال پخش رول ({self.play_times.get()} بار)... (Ctrl برای توقف)")

        # شروع پخش در یک thread جداگانه
        threading.Thread(
            target=self.play_roll,
            args=(self.play_times.get(), self.delay_var.get(), self.speed_var.get()),
            daemon=True
        ).start()

    def stop_playback(self):
        self.playing = False
        self.play_button.config(state=tk.NORMAL)
        self.stop_play_button.config(state=tk.DISABLED)
        self.info_label.config(text="پخش متوقف شد.")

    def play_roll(self, times, delay_between_repeats, speed):
        start_time = time.time()
        for repeat in range(times):
            if not self.playing:
                break

            for i, action in enumerate(self.actions):
                if not self.playing:
                    break

                # محاسبه زمان نسبی عمل
                if i == 0:
                    relative_time = 0
                else:
                    relative_time = action["time"] - self.actions[0]["time"]

                # محاسبه زمان فعلی از شروع پخش
                current_time = time.time() - start_time

                # اگر عمل باید در آینده انجام شود، منتظر بمان
                target_time = relative_time / speed
                if current_time < target_time:
                    time.sleep(target_time - current_time)

                # انجام عمل
                if action["type"] == "move":
                    pyautogui.moveTo(action["x"], action["y"])
                elif action["type"] == "click":
                    pyautogui.click(action["x"], action["y"], button=action["button"])

            # تاخیر بین تکرارها
            if repeat < times - 1:
                time.sleep(delay_between_repeats)

        self.playing = False
        self.root.after(0, lambda: [
            self.play_button.config(state=tk.NORMAL),
            self.stop_play_button.config(state=tk.DISABLED),
            self.info_label.config(text=f"پخش رول به پایان رسید.")
        ])

    def save_roll(self):
        if not self.actions:
            messagebox.showwarning("هشدار", "هیچ رولی برای ذخیره وجود ندارد!")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialdir=self.output_folder,
            title="ذخیره رول"
        )

        if not file_path:
            return

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.actions, f, ensure_ascii=False, indent=4)

        messagebox.showinfo("موفقیت", f"رول با موفقیت ذخیره شد: {file_path}")
        self.refresh_rolls()

    def load_roll(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json")],
            initialdir=self.output_folder,
            title="بارگذاری رول"
        )

        if not file_path:
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            self.actions = json.load(f)

        messagebox.showinfo("موفقیت", f"رول با موفقیت بارگذاری شد: {file_path}")
        self.info_label.config(text=f"رول بارگذاری شد: {len(self.actions)} عمل")

    def delete_roll(self):
        selected = self.rolls_listbox.curselection()
        if not selected:
            messagebox.showwarning("هشدار", "لطفاً یک رول انتخاب کنید.")
            return

        file_name = self.rolls_listbox.get(selected[0])
        file_path = os.path.join(self.output_folder, file_name)

        try:
            os.remove(file_path)
            self.refresh_rolls()
            messagebox.showinfo("موفقیت", "رول با موفقیت حذف شد.")
        except Exception as e:
            messagebox.showerror("خطا", f"خطا در حذف رول: {e}")

    def refresh_rolls(self):
        self.rolls_listbox.delete(0, tk.END)
        for file in sorted(os.listdir(self.output_folder)):
            if file.endswith('.json'):
                self.rolls_listbox.insert(tk.END, file)

if __name__ == "__main__":
    root = tk.Tk()
    app = AutomationRecorder(root)
    root.mainloop()
