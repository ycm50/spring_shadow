import wave
import math
import struct
import numpy as np
import argparse  # 新增：导入argparse模块
import os  # 新增：导入os模块处理文件路径
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
    # 定义支持的音色库
    TIMBRES = {
        'piano': [1.0, 0.5, 0.3, 0.2, 0.1, 0.05],        # 钢琴音色
        'violin': [1.0, 0.7, 0.5, 0.3, 0.2, 0.15, 0.1],  # 小提琴音色
        'flute': [1.0, 0.2, 0.1, 0.05]                   # 长笛音色（新增示例）
    }
    
    # 设置命令行参数解析器
    parser = argparse.ArgumentParser(description='将RCP乐谱文件转换为WAV音频文件')
    parser.add_argument('input_file', nargs='?', default='1.rcp', 
                        help='输入的RCP文件路径（默认：1.rcp）')
    parser.add_argument('--timbre', choices=TIMBRES.keys(), default='piano', 
                        help=f'选择音色（默认：piano，支持：{list(TIMBRES.keys())}）')
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 生成输出文件名（基于输入文件名和音色）
    input_basename = os.path.splitext(os.path.basename(args.input_file))[0]
    output_file = f'output_{input_basename}_{args.timbre}.wav'
    
    # 执行转换
    print(f'正在转换：{args.input_file}，音色：{args.timbre}')
    rcp_to_wav(args.input_file, output_file, harmonic_amplitudes=TIMBRES[args.timbre])
    print(f'转换完成，输出文件：{output_file}')