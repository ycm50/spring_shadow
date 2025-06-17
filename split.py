from player import *
player = MusicPlayer(base_freq=261.63, base_beat_duration=0.2)
player.set_bpm(97*4)  # 设置120BPM
str="1.+1,2.+2,1.+1,2.+2,3.+2,4.+4,3.+2,2.+1,3.+1,2.+2,1.+1,2.+2,3.+2,4.+4,3.+2,2.+1"
str=str.split(',')
player.play_sequence(str)
print(str)