import tkinter as tk
from tkinter import filedialog
import os
import threading
from player import MusicPlayer, spring_shadow_notes

class RCPPlayerUI:
    def __init__(self, root):
        self.root = root
        self.root.title("RCP 乐谱播放器")

        # 初始化音乐播放器，使用与 UI 输入框相同的默认值
        self.player = MusicPlayer(base_freq=261.63, base_beat_duration=0.2)
        piano_amplitudes = [
            1.0,   # 基频
            0.7,   # 二次谐波
            0.5,   # 三次谐波
            0.3,   # 四次谐波
            0.2,   # 五次谐波
            0.15,  # 六次谐波
            0.1,   # 七次谐波
            0.08,  # 八次谐波
            0.05,  # 九次谐波
            0.03   # 十次谐波
        ]
        self.player.set_harmonic_amplitudes(piano_amplitudes)

        # 播放控制标志
        self.is_playing = False
        self.play_thread = None

        # 创建 UI 组件
        self.create_widgets()
        # 配置行列权重，使组件适应窗口大小变化
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

    def create_widgets(self):
        # 创建滚动条
        scrollbar = tk.Scrollbar(self.root)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 修改文本框，关联滚动条
        self.note_text = tk.Text(self.root, height=20, width=50, yscrollcommand=scrollbar.set, wrap=tk.NONE)
        self.note_text.pack(pady=10, expand=True, fill=tk.BOTH)
        scrollbar.config(command=self.note_text.yview)

        self.note_text.bind("<Delete>", self.delete_selected_notes)

        # 按钮
        self.load_button = tk.Button(self.root, text="加载 RCP 文件", command=self.load_rcp)
        self.load_button.pack(pady=5)

        self.save_button = tk.Button(self.root, text="保存为 RCP 文件", command=self.save_rcp)
        self.save_button.pack(pady=5)

        self.play_button = tk.Button(self.root, text="播放乐谱", command=self.play_music)
        self.play_button.pack(pady=5)

        self.pause_button = tk.Button(self.root, text="暂停播放", command=self.pause_music, state=tk.DISABLED)
        self.pause_button.pack(pady=5)

        # 添加 BPM 输入框
        tk.Label(self.root, text="BPM:").pack()
        self.bpm_entry = tk.Entry(self.root, width=20)
        self.bpm_entry.insert(0, "388")  # 默认值统一为 120
        self.bpm_entry.pack(pady=5)

        # 添加基准频率输入框
        tk.Label(self.root, text="基准频率 (Hz):").pack()
        self.base_freq_entry = tk.Entry(self.root, width=20)
        self.base_freq_entry.insert(0, "261.63")  # 默认值
        self.base_freq_entry.pack(pady=5)

        # 添加标准拍长输入框
        tk.Label(self.root, text="标准拍长 (秒):").pack()
        self.base_beat_duration_entry = tk.Entry(self.root, width=20)
        self.base_beat_duration_entry.insert(0, "0.2")  # 默认值统一为 0.5
        self.base_beat_duration_entry.pack(pady=5)

        # 初始化文本框内容
        self.set_default_notes()

    def set_default_notes(self):
        # 设置默认乐谱，每行显示4个音符
        notes = spring_shadow_notes
        formatted_notes = []
        for i in range(0, len(notes), 4):
            formatted_notes.append(" ".join(notes[i:i+4]))
        default_notes = "\n".join(formatted_notes)
        self.note_text.delete(1.0, tk.END)
        self.note_text.insert(tk.END, default_notes)

    def save_rcp(self):
        # 打开保存文件对话框
        file_path = filedialog.asksaveasfilename(defaultextension=".rcp", filetypes=[("RCP 文件", "*.rcp")])
        if file_path:
            try:
                # 获取当前参数值
                bpm = self.bpm_entry.get()
                base_freq = self.base_freq_entry.get()
                base_beat_duration = self.base_beat_duration_entry.get()
                notes = self.note_text.get(1.0, tk.END)
                
                # 将参数写入文件第一行，音符内容从第二行开始
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(f"{bpm},{base_freq},{base_beat_duration}\n")
                    file.write(notes)
                print(f"文件已保存到: {file_path}")
            except Exception as e:
                print(f"保存文件时出错: {e}")

    def load_rcp(self):
        # 打开文件选择对话框
        file_path = filedialog.askopenfilename(filetypes=[("RCP 文件", "*.rcp")])
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    lines = file.readlines()
                    if lines:
                        # 读取第一行参数
                        params = lines[0].strip().split(',')
                        if len(params) == 3:
                            self.bpm_entry.delete(0, tk.END)
                            self.bpm_entry.insert(0, params[0])
                            self.base_freq_entry.delete(0, tk.END)
                            self.base_freq_entry.insert(0, params[1])
                            self.base_beat_duration_entry.delete(0, tk.END)
                            self.base_beat_duration_entry.insert(0, params[2])
                        
                        # 从第二行开始读取音符内容
                        notes = ''.join(lines[1:])
                        self.note_text.delete(1.0, tk.END)
                        self.note_text.insert(tk.END, notes)
            except Exception as e:
                print(f"加载文件时出错: {e}")

    def play_music(self):
        if not self.is_playing:
            try:
                # 获取输入值
                bpm_text = self.bpm_entry.get().strip()
                base_freq = float(self.base_freq_entry.get())
                base_beat_duration_text = self.base_beat_duration_entry.get().strip()

                # 设置基准频率
                self.player.set_base_freq(base_freq)

                if bpm_text:
                    # 如果有 BPM 输入，优先使用 BPM 设置
                    bpm = float(bpm_text)
                    self.player.set_bpm(bpm)
                    # 更新标准拍长输入框显示
                    self.base_beat_duration_entry.delete(0, tk.END)
                    self.base_beat_duration_entry.insert(0, f"{60.0 / bpm:.6f}")
                elif base_beat_duration_text:
                    # 只有标准拍长输入时，设置标准拍长并计算 BPM 更新输入框
                    base_beat_duration = float(base_beat_duration_text)
                    self.player.set_base_beat_duration(base_beat_duration)
                    self.bpm_entry.delete(0, tk.END)
                    self.bpm_entry.insert(0, f"{60.0 / base_beat_duration:.6f}")
                else:
                    print("请输入 BPM 或标准拍长！")
                    return
            except ValueError:
                print("输入值必须为数字，请检查输入！")
                return

            self.is_playing = True
            self.play_button.config(state=tk.DISABLED)
            self.pause_button.config(state=tk.NORMAL)
            self.play_thread = threading.Thread(target=self._play_sequence)
            self.play_thread.start()

    def _play_sequence(self):
        notes_text = self.note_text.get(1.0, tk.END)
        import re
        # 使用正则表达式确保音符之间有空格分隔
        notes_text = re.sub(r'(\d\.[+-]?\d+)(?=\d\.)', r'\1 ', notes_text)
        notes = notes_text.strip().split(' ')
        try:
            print("开始播放乐谱...")
            for line in notes:
                if not self.is_playing:
                    break
                # 按空格分割每行的音符
                note_strs = line.split()
                # 检查并分割长度为8的音符
                processed_notes = []
                for note in note_strs:
                    if len(note) == 8:
                        # 将8字符音符分割为两个4字符音符
                        processed_notes.append(note[:4])
                        processed_notes.append(note[4:])
                    else:
                        processed_notes.append(note)
                # 使用处理后的音符列表
                for note_str in processed_notes:
                    if note_str:
                        self.player.play_note(note_str)
            print("播放完成！")
        except Exception as e:
            print(f"播放时出错: {e}")
        finally:
            self.is_playing = False
            self.play_button.config(state=tk.NORMAL)
            self.pause_button.config(state=tk.DISABLED)

    def pause_music(self):
        if self.is_playing:
            self.is_playing = False
            self.play_button.config(state=tk.NORMAL)
            self.pause_button.config(state=tk.DISABLED)

    def delete_selected_notes(self, event):
        try:
            selected_text = self.note_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            if selected_text:
                self.note_text.delete(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            pass

    def insert_notes(self, event):
        input_text = self.input_entry.get()
        if input_text:
            insert_index = self.note_text.index(tk.INSERT)
            self.note_text.insert(insert_index, f"\n{input_text}")
            self.input_entry.delete(0, tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = RCPPlayerUI(root)
    root.mainloop()