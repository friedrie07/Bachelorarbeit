import socket
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import threading
import pyaudio
import wave
import sys
import time
import ctypes
import numpy as np
import sound_analysis
import wavio
import iir_filter

#wifi
local_ip = '127.0.0.2'
port_number = 15151
max_eingabe_length = 4096
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#player handles
play_on = False
jump_to_start = False
play_terminate = False

#FIR-Filter handles
chunk = 1024
history = []
normalization_factor = None
durchgang = 0
synch_part = [0 for i in range(11024)] + [-32767] + [32767] + [0 for i in range(11024)]
centerFrequencies = [20, 40, 60, 80, 100, 120, 160, 180, 240, 320, 360, 480, 640, 720, 960, 1280, 1440, 1920, 2560, 2880, 3840, 5120, 5760, 7680, 10240, 11520, 15360, 20000]

#volume controller
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))
#volume controller handles
volumeLevel = 0

def wave_to_pcm(wave_path, pcm_path):
    wave_file = wave.open(wave_path, 'rb')
    pcm_file = open(pcm_path, 'wb')
    wave_data = wave_file.readframes(-1)
    pcm_file.write(wave_data)
    wave_file.close()
    pcm_file.close()

def pcm_to_wave(pcm_path, wave_path):
    pcm_file = open(pcm_path, 'rb')
    wave_file = wave.open(wave_path, 'wb')
    pcm_data = pcm_file.read()
    nframes = len(pcm_data)
    wave_file.setnframes(nframes)
    wave_file.setnchannels(1)
    wave_file.setframerate(44100)
    wave_file.setsampwidth(2)
    wave_file.writeframes(pcm_data)
    wave_file.close()
    pcm_file.close()

def normalized_int(binary_float_fir_output):
    double_file = open(binary_float_fir_output, 'rb')
    double_data = double_file.read()
    double_output_list = np.frombuffer(double_data, np.float64)
    synchpoint =  sound_analysis.synchpoint(double_output_list, 44100)
    output_max = double_output_list[synchpoint]
    normalisation_factor = 32766/output_max
    double_output_list_noise = double_output_list[22050:]
    double_output_list_normal = [double_output_list_noise[i]*normalisation_factor for i in range(len(double_output_list_noise))]
    double_output_list_normal_int = [int(double_output_list_normal[i]) for i in range(len(double_output_list_normal))]
    return (double_output_list_normal_int, normalisation_factor)

def invoke_filter_2(koeffs):
    global centerFrequencies
    global play_on
    play_on = False
    filts = []
    for i in range(len(koeffs)):
        for x in range(len(centerFrequencies)):
            filts.append(iir_filter.filt(centerFrequencies[x], 1, koeffs[i]))
    dings = sound_analysis.waveToList(r"C:\Users\Fritz\Documents\Bachelorarbeit\Tests\die_5.wav")
    for i in range(len(filts)):
        out = []
        for x in dings:
            out.append(filts[i].filter(x))
        outs = np.array(out)
        print(i)
        wavio.write(r"C:\Users\Fritz\Documents\Bachelorarbeit\Tests\die_5.wav", outs, 44100, None , 2)
    connection.send(("done").encode('utf-8'))

def play():
    global play_on
    global play_terminate
    global jump_to_start
    noise = wave.open(r"C:\Users\Fritz\Documents\Bachelorarbeit\Tests\die_5.wav", 'rb')
    p = pyaudio.PyAudio()
    stream = p.open(format =
                    p.get_format_from_width(noise.getsampwidth()),
                    channels = noise.getnchannels(),
                    rate = noise.getframerate(),
                    output = True)
    
    while not play_terminate:
        data = noise.readframes(chunk)
        while data:
            if play_on:
                stream.write(data)
                data = noise.readframes(chunk)
            if jump_to_start:
                noise.close()
                stream.close()    
                p.terminate()
                noise = wave.open(r"C:\Users\Fritz\Documents\Bachelorarbeit\Tests\neuesTestsignal_3.wav", 'rb')
                p = pyaudio.PyAudio()
                stream = p.open(format =
                                p.get_format_from_width(noise.getsampwidth()),
                                channels = noise.getnchannels(),
                                rate = noise.getframerate(),
                                output = True)
                data = noise.readframes(chunk)
                jump_to_start = False
    noise.close()
    stream.close()    
    p.terminate()




def set_volume(eingabe):
    global volumeLevel
    volume_correctment = float(eingabe[1:])
    if (volumeLevel + volume_correctment)<=0:
        volumeLevel += volume_correctment
    else:
        volumeLevel = 0
    volume.SetMasterVolumeLevel(volumeLevel, None)
    return

def control_dialogue():
    print("running")
    global t1
    global play_on
    global volumeLevel
    global jump_to_start
    global durchgang
    global centerFrequencies
    try:
        while True:
            eingabe = connection.recv(max_eingabe_length)
            try:
                eingabe = eingabe.decode('utf-8')
                if eingabe=='p':
                    play_on = True
                elif eingabe=='s':
                    play_on = False
                elif eingabe=='j':
                    jump_to_start = True
                elif eingabe[0]==';':
                    set_volume(eingabe)
                else:
                    pass
            except:
                difference = np.frombuffer(eingabe, np.float64)
                profile = sound_analysis.adjustment_profile_2(difference, centerFrequencies)
                invoke_filter_2(profile)
    except:
        return
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.bind((local_ip, port_number))
print(port_number, local_ip)
volume.SetMasterVolumeLevel(0.0, None)
client.listen()
connection, address = client.accept()
print("connected")    
try:
    t1 = threading.Thread(target=play, args=())
    t2 = threading.Thread(target=control_dialogue, args=[])
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    connection.close()
except:
    connection.close()






