import numpy as np
import pyaudio
import time

class MusicNote:
    """表示单个音乐音符"""
    NOTE_TO_SEMITONE = {
        '1': 0, '2': 2, '3': 4, '4': 5, 
        '5': 7, '6': 9, '7': 11, '0': -240
    }
    
    def __init__(self, base_freq=261.63, base_beat_duration=0.5):
        """
        初始化音符参数
        :param base_freq: 基准频率 (默认为C4=261.63Hz)
        :param base_beat_duration: 标准拍长 (四分音符的时长，秒)
        """
        self.base_freq = base_freq
        self.base_beat_duration = base_beat_duration
    
    def parse(self, note_str):
        """
        解析简谱字符串
        :param note_str: 简谱字符串 (如 "1.04", "2.-4", "1.+2")
        :return: (频率, 持续时间)
        """
        parts = note_str.split('.')
        if len(parts) != 2:
            raise ValueError(f"无效的格式: {note_str}")
        
        note_symbol, suffix = parts
        
        # 验证音符符号
        if note_symbol not in self.NOTE_TO_SEMITONE:
            raise ValueError(f"无效的音符: {note_symbol}")
        
        # 解析八度偏移和节拍分母
        octave_offset = 0
        if suffix.startswith('0'):
            # 中音区
            beat_denom_str = suffix[1:].replace(':','.')
        elif suffix.startswith('-'):
            # 低八度
            octave_offset = -1
            beat_denom_str = suffix[1:].replace(':','.')
        elif suffix.startswith('+'):
            # 高八度
            octave_offset = 1
            beat_denom_str = suffix[1:].replace(':','.')
        else:
            # 默认中音区
            beat_denom_str = suffix.replace(':','.')
        
        # 验证节拍分母
        # if not beat_denom_str.isdigit():
        #     raise ValueError(f"无效的节拍分母: {beat_denom_str}")
        
        beat_denom = float(beat_denom_str)
        if beat_denom <= 0:
            raise ValueError(f"节拍分母必须为正数: {beat_denom}")
        
        # 计算实际频率
        semitone_shift = octave_offset * 12 + self.NOTE_TO_SEMITONE[note_symbol]
        freq = self.base_freq * (2 ** (semitone_shift / 12))
        
        # 计算持续时间
        duration = self.base_beat_duration * (4 / beat_denom)  # 四分音符为基础
        
        return freq, duration

class MusicPlayer:
    """音乐播放器类"""
    def __init__(self, base_freq=261.63, base_beat_duration=0.5, sample_rate=44100):
        """
        初始化音乐播放器
        :param base_freq: 基准频率
        :param base_beat_duration: 标准拍长(四分音符的时长)
        :param sample_rate: 音频采样率
        """
        self.note_parser = MusicNote(base_freq, base_beat_duration)
        self.sample_rate = sample_rate
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.harmonic_amplitudes = [1.0]  # 默认只使用基频
    
    def open_stream(self):
        """打开音频流"""
        if self.stream is None or not self.stream.is_active():
            if self.stream:
                self.stream.close()
            self.stream = self.audio.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=self.sample_rate,
                output=True
            )
    
    def close_stream(self):
        """关闭音频流"""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
    
    def __del__(self):
        """析构函数确保资源释放"""
        self.close_stream()
        self.audio.terminate()
    
    def set_base_freq(self, base_freq):
        """设置基准频率"""
        self.note_parser.base_freq = base_freq
    
    def set_bpm(self, bpm):
        """通过BPM设置标准拍长"""
        self.note_parser.base_beat_duration = 60.0 / bpm

    def set_base_beat_duration(self, duration):
        """设置标准拍长(四分音符的时长)"""
        self.note_parser.base_beat_duration = duration
    
    def set_harmonic_amplitudes(self, amplitudes):
        """设置泛音列的振幅系数"""
        self.harmonic_amplitudes = amplitudes
    
    def generate_tone(self, frequency, duration):
        """生成复合波形音频数据，基于泛音列振幅数组"""
        t = np.linspace(0, duration, int(self.sample_rate * duration), endpoint=False)
        
        # 初始化复合波形
        composite_tone = np.zeros_like(t)
        
        # 生成基频和各次谐波
        for i, amplitude in enumerate(self.harmonic_amplitudes):
            harmonic_freq = frequency * (i + 1)  # 第i个谐波的频率是基频的i+1倍
            composite_tone += amplitude * np.sin(2 * np.pi * harmonic_freq * t)
        
        # 归一化处理，防止溢出
        if np.max(np.abs(composite_tone)) > 0:
            composite_tone /= np.max(np.abs(composite_tone))
        
        # 添加淡入淡出减少爆音
        fade_ms = 50
        fade_samples = int(self.sample_rate * fade_ms / 1000)
        if fade_samples < len(composite_tone):
            # 淡入
            composite_tone[:fade_samples] *= np.linspace(0, 1, fade_samples)
            # 淡出
            composite_tone[-fade_samples:] *= np.linspace(1, 0, fade_samples)
        
        return composite_tone.astype(np.float32)
    
    def play_note(self, note_str):
        """播放单个音符"""
        self.open_stream()  # 确保流已打开
        
        freq, duration = self.note_parser.parse(note_str)
        print(f"播放: {note_str} -> 频率: {freq:.2f}Hz, 时长: {duration:.3f}秒")
        tone = self.generate_tone(freq, duration)
        self.stream.write(tone.tobytes())
        
        # 添加短暂静音分隔音符
        silence = np.zeros(int(self.sample_rate * 0.05), dtype=np.float32)
        self.stream.write(silence.tobytes())
    
    def play_sequence(self, note_sequence):
        """播放音符序列"""
        self.open_stream()  # 确保流已打开
        for note_str in note_sequence:
            self.play_note(note_str)

if __name__ == "__main__":
    player = MusicPlayer(base_freq=261.63)
    player.set_bpm(388)  # 设置120BPM
    
    
spring_shadow_notes = [
        "3.+1","2.+2","1.+1","2.+2","3.+2","4.+4","3.+2","2.+1","3.+1","2.+2","1.+1","2.+2","3.+2","4.+4","3.+2","2.+1",
        "3.+1","2.+2","1.+1","2.+2","3.+2","4.+4","3.+2","2.+1","3.+1","2.+2","1.+1","2.+2","3.+2","4.+4","3.+2","2.+1","1.04","1.04",
        "3.02","3.02","2.02","4.02","3.02","2.02","2.02","2.02","1.04","1.04","4.02","3.02","2.02","2.01","1.04","2.04","3.01","0.01","3.02","5.02","1.+2",
        "7.01","1.+2","7.01","1.+2","7.04","6.04","5.01","5.02","2.02","4.02","4.01","3.02","3.01","5.-2","4.02","3.02","2.02","3.01","5.02",
        "1.01","0.01","1.02","2.02","1.02","7.-4","1.02","5.02","1.02","4.01","3.02","2.02","1.02","1.01","0.01","1.04","2.04",
        "3.02","3.02","2.02","4.02","3.02","2.02","2.02","2.02","1.02","4.02","3.02","2.02","2.01","1.04","2.04","3.01","0.01","3.02","5.02","1.+2",
        '7.01', '1.+2', '7.01', '1.+2', '7.04', '6.04', '5.01', '5.02', '2.02', '4.02','4.02', '3.02', '3.02', '3.01', '5.-2', '4.02', '3.02', '2.02', '3.01', '5.02',
        '1.01', '0.01', '1.04', '1.04', '2.02', '1.01', '1.02', '5.02', '1.02', '4.02', '4.04', '4.04', '3.04','2.04', '2.02', '1.02', '1.02', '1.01',
        '6.02', '5.02', '5.02', '5.02', '4.02', '4.02', '3.02', '2.02', '2.02', '2.01', '3.02', '4.02', '3.04', '3.04', '3.04', '3.04', '3.02', '2.02', '3.02', '2.+1', '1.+2', '1.+1', '1.+2',
        '7.02', '6.02', '6.02', '6.01', '0.01', '6.02', '6.02', '5.02', '4.04', '4.04', '4.01', '3.02', '3.04', '4.04', '5.00:5',
        '3.04', '2.04', '3.04', '2.04', '3.04', '4.04', '5.01', '4.04', '5.04', '6.01', '6.04', '7.04', '1.+1', '2.+4', '1.+4', '5.01', '5.02', '4.02', '4.02', '3.01', '4.04', '3.04', '5.01',
        '3.04', '2.04', '3.04', '2.04', '3.02', '5.01', '4.04', '5.04', '6.01', '0.04', '6.04', '7.01', '0.04', '3.04', '3.+2', '3.+2', '3.+4', '4.+2', '3.+2', '2.+2', '2.+1', '1.+4', '7.04', '1.+1', '5.04', '1.+4',
        '2.+2', '1.+2', '1.+2', '1.+1', '5.02', '2.+2', '1.+2', '1.+2', '5.04', '1.+4', '2.+2', '1.+2', '1.+2', '5.04', '1.+4', '2.+2', '3.+4', '2.+2', '1.+1', '1.+2',
        '7.02', '6.02', '6.02', '6.01', '5.02', '5.01', '4.02', '4.02', '3.02', '2.02', '3.01', '3.02', '4.02', '3.02', '4.02', '3.02', '2.02',
        '1.01', '0.01', '0.01', '0.02', '1.04', '2.04', '3.02', '3.02', '2.02', '4.02', '3.02', '2.02', '2.02', '2.02', '1.04', '1.04', '4.02', '3.02', '2.02',
        '2.01', '1.04', '2.04', '3.01', '0.01', '3.02', '5.02', '1.+2', '7.01', '1.+2', '7.01', '1.+2', '7.04', '6.04', '5.02', '2.02', '4.02',
        '4.02', '3.02', '3.02', '3.01', '4.02', '3.02', '2.02', '3.01', '5.02', '1.01', '0.01', '1.04', '1.04', '2.02', '1.01', '1.02', '5.02', '1.02',
        '4.01', '3.02', '2.01', '1.02', '1.01', '6.02', '5.02', '5.02', '5.02', '4.02', '4.02', '4.02', '3.02', '2.02', '2.02', '2.01', '5.02',
        '5.02', '4.04', '4.04', '4.02', '4.02', '3.02', '2.02', '2.01', '1.04', '7.-4', '1.01', '6.02', '5.02', '5.02', '5.02', '4.02', '4.02', '3.02', '2.02', '2.02', '2.01', '3.02',
        '4.02', '3.04', '3.04', '3.04', '3.04', '3.02', '2.02', '3.02', '2.+1', '1.+2', '1.+1', '1.+2', '7.01', '6.02', '6.01', '0.01', '6.02', '5.02', '4.04', '4.04',
        '4.01', '3.02', '3.04', '4.04', '2.01','2.01', '4.02', '6.04', '1.+4', '3.+2','3.+2', '1.+2', '4.02', '4.02', '6.02', '3.+2','3.+2', '6.02', '6.02', '4.02',
        '1.+1', '1.+4', '2.+4', '2.+1', '2.+4', '1.+4', '1.+1', '1.+2', '1.+2', '1.+2', '1.+2', '4.02', '6.04', '1.+4', '3.+2', '3.+2', '1.+2', '4.02', '4.02', '6.02', '3.+2', '3.+2', '6.02', '4.02',
        '1.+1', '1.+4', '2.+4', '2.+1', '2.+4', '1.+4', '1.+1', '1.+4', '3.+4', '3.+1', '3.+4', '2.+4', '2.+4', '1.+4', '1.+4', '1.+4', '1.+4', '1.+4', '3.+2', '1.+1', '2.+4', '1.+4', '1.+4', '1.+4', '1.+4', '1.+4', '2.+2', '1.+2', '1.+4', '6.04',
        '5.02', '3.+2', '2.+2', '2.+1', '2.+4', '2.+4', '2.+2', '5.04', '5.04', '2.+1', '1.+2', '1.+1', '1.+2', '1.+2', '1.+2', '1.+4', '1.+4', '2.+2', '1.+2', '2.+4', '2.+4', '1.+1',
        '0.01', '2.+2', '2.+4', '1.+4', '2.+2', '2.+2', '3.+2', '2.+2', '3.01', '4.02', '3.+1', '0.01', '0.01', '0.01',
        '5.+2', '5.+2', '5.+2', '5.+2', '3.+2', '2.+2', '1.+2', '7.02', '7.02', '7.02', '3.+1', '2.+2', '2.+2', '1.+2', '5.02', '6.01', '0.01',
        '0.01', '7.02', '7.02', '7.02', '1.+2', '7.02', '5.04', '5.02', '2.02', '3.02', '3.04', '2.04', '3.04', '2.04', '3.04', '4.04', '5.01', '4.04', '5.04', '6.01', '6.04', '7.04', '1.+1', '2.+4', '1.+4'
        '5.01', '5.02', '4.02', '4.02', '3.01', '4.04', '3.04', '5.01', '3.04', '2.04', '3.04', '2.04', '3.02', '5.01', '4.04', '5.04', '6.01', '0.04', '6.04', '7.01', '0.04', '3.04',
        '3.+2', '3.+2', '3.+4', '4.+2', '3.+2', '2.+2', '2.+1', '1.+4', '7.04', '1.+1', '5.04', '1.+4', '2.+1', '1.+2', '1.+1', '5.02', '2.+1', '1.+2', '1.+1', '5.04', '1.+4'
        '2.+2', '1.+2', '1.+2', '1.+1', '5.04', '1.+4', '2.+2', '3.+4', '2.+2', '1.+1', '1.+2', '7.02', '6.02', '6.02', '6.01', '5.02', '5.01', '4.02', '4.02', '3.02', '2.02', '3.01',
        '3.02', '4.02', '3.02', '4.02', '3.02', '2.02', '1.01', '4.02', '4.01', '5.01', '1.+2', '1.+1', '1.+2', '2.+2', '1.+2', '2.+2',
        '1.+1', '2.+2', '1.+1', '2.+2', '3.+2', '4.+4', '3.+2', '2.+1', '3.+1', '2.+2', '1.+1', '2.+2', '3.+2', '4.+4', '3.+2', '2.+1'
        ]
# player.play_sequence(spring_shadow_notes)