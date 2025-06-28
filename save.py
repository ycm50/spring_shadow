import wave
import math
import struct
import numpy as np
from player import MusicNote, MusicPlayer  # 修改导入语句

def rcp_to_wav(input_file, output_file, sample_rate=44100, harmonic_amplitudes=[1.0]):  # 添加音色参数
    # 读取rcp文件
    with open(input_file, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]
        
    if not lines:
        raise ValueError("RCP文件为空")
        
    # 解析第一行参数 (BPM, 基准频率, 拍长)
    params = lines[0].split(',')
    if len(params) != 3:
        raise ValueError("RCP文件格式错误，第一行必须包含3个参数")
        
    bpm = float(params[0])
    base_freq = float(params[1])
    base_beat_duration = float(params[2])
    
    # 初始化音符解析器和播放器
    note_parser = MusicNote(base_freq, base_beat_duration)
    player = MusicPlayer(base_freq, base_beat_duration, sample_rate)  # 创建播放器实例
    player.set_harmonic_amplitudes(harmonic_amplitudes)  # 设置音色
    
    audio_data = bytearray()
    
    # 解析后续行的音符内容
    for line in lines[1:]:
        note_strs = line.split()
        for note_str in note_strs:
            # 使用player.py中的解析逻辑转换简谱
            freq, duration = note_parser.parse(note_str)
            
            # 生成音频数据（使用player的generate_tone方法）
            tone = player.generate_tone(freq, duration)
            
            # 转换为16位整数并添加到音频数据
            tone_int16 = (tone * 32767).astype(np.int16)
            audio_data += tone_int16.tobytes()
    
    # 写入WAV文件
    with wave.open(output_file, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data)

if __name__ == '__main__':
    # 示例：设置不同的音色（泛音振幅）
    # 钢琴音色示例
    piano_timbre = [1.0, 0.5, 0.3, 0.2, 0.1, 0.05]
    # 小提琴音色示例
    violin_timbre = [1.0, 0.7, 0.5, 0.3, 0.2, 0.15, 0.1]
    
    # 使用钢琴音色保存
    rcp_to_wav('1.rcp', 'output_piano.wav', harmonic_amplitudes=piano_timbre)
    # 或者使用小提琴音色
    # rcp_to_wav('1.rcp', 'output_violin.wav', harmonic_amplitudes=violin_timbre)