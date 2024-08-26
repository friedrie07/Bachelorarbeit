import wave
import sound_analysis
import numpy as np
import ctypes
import wavio 
import math
import ctypes

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
    #print(pcm_data)
    nframes = len(pcm_data)
    wave_file.setnframes(nframes)
    wave_file.setnchannels(1)
    wave_file.setframerate(44100)
    wave_file.setsampwidth(2)
    wave_file.writeframes(pcm_data)
    wave_file.close()
    pcm_file.close()

def list_to_wave(liste, wave_path):
    wave_file = wave.open(wave_path, 'wb')
    nframes = len(liste)
    wave_data = np.array(liste)
    wave_file.setnframes(nframes)
    wave_file.setnchannels(1)
    wave_file.setframerate(44100)
    wave_file.setsampwidth(2)
    wave_file.writeframes(wave_data + wave_data)
    wave_file.close()

def list_to_pcm(liste, pcm_path):
    pcm_file = open(pcm_path, 'wb')
    pcm_data = np.array(liste)
    pcm_file.write(pcm_data)
    pcm_file.close()

def normalized_int(binary_float_fir_output, normalisation_factor=None):
    double_file = open(binary_float_fir_output, 'rb')
    double_data = double_file.read()
    double_output_list = np.frombuffer(double_data, np.float64)
    print(len(double_output_list))
    if normalisation_factor==None:
        synchpoint =  sound_analysis.synchpoint(double_output_list, 44100)
        output_max = double_output_list[synchpoint]
        normalisation_factor = 32766/output_max
    double_output_list_normal = [double_output_list[i]*normalisation_factor for i in range(len(double_output_list))]
    double_output_list_normal_int = [int(double_output_list_normal[i]) for i in range(len(double_output_list))]
    return double_output_list_normal_int
    
def adjustment_profile(realSound, virtualSound, lowpassLimit, highpassLimit, filterSize=True, framerate=44100):
    target_response = sound_analysis.delta_spectrum(realSound, virtualSound, lowpassLimit, highpassLimit, False, framerate)
    difference = target_response
    if filterSize == True:
        iCoefficients = np.fft.ifft(target_response)
        coefficients = [abs(i) for i in iCoefficients]
        return (coefficients, difference)
    else:
        response_subset = []
        averagingRange = math.floor(len(target_response)//filterSize)
        for i in range(filterSize):
            response = 0
            for x in range(averagingRange):
                response += target_response[i*averagingRange+x]
            response /= averagingRange
            response_subset += response
        iCoefficients = np.fft.ifft(response_subset)
        coefficients = [abs(i) for i in iCoefficients]
        return (coefficients, difference)



def create_band_centers(n_bands, lowpass_limit, highpass_limit):
    global_bandwidth = highpass_limit - lowpass_limit
    band_centers = []
    local_bandwidth = global_bandwidth/(n_bands+1)
    pre_current_index = lowpass_limit
    current_index = 0
    for i in range(n_bands):
        i+=1
        current_index = pre_current_index + local_bandwidth/(n_bands/(2*i))
        band_center = pre_current_index + (current_index-pre_current_index)/2
        pre_current_index = current_index
        band_centers.append(band_center)
    return band_centers

def create_center_bandwidth(band_centers, lowpass_limit):
    boarder = lowpass_limit
    band_widths = []
    for center in band_centers:
        width = 2*(center - boarder)
        boarder = center + width/2
        band_widths.append(width)
    return band_widths

def sweep(n_cycles, lowpass_limit=20, highpass_limit=20000, framerate=44100):
    sweep_out = []
    n_frequencies = (highpass_limit-lowpass_limit)+1
    for i in range(n_frequencies):
        frequency = lowpass_limit + i
        n_samples = framerate//frequency
        for x in range(n_cycles):
            for o in range(n_samples):
                sweep_out.append(32766*(np.sin(2*np.pi*(o/n_samples))))
    return sweep_out

#wave_to_pcm(r"C:\Users\Fritz\Documents\Bachelorarbeit\Tests\1Hz-20kHz linear_sweep_synch.wav", r"C:\Users\Fritz\Documents\Bachelorarbeit\Tests\input.pcm")
wave_to_pcm(r"C:\Users\Fritz\Documents\Bachelorarbeit\Tests\Im Awake_mono_short.wav", r"C:\Users\Fritz\Documents\Bachelorarbeit\Tests\input.pcm")

#pcm_to_wave(r"C:\Users\Fritz\Documents\Bachelorarbeit\Tests\outputFloat.pcm", r"C:\Users\Fritz\Documents\Bachelorarbeit\Tests\die_5.wav")
data = open(r"C:\Users\Fritz\Documents\Bachelorarbeit\Tests\output.bin", 'rb')
data_pieces = data.read()
zeug = np.frombuffer(data_pieces, np.int16)
daraaa = np.array(zeug)
wavio.write(r"C:\Users\Fritz\Documents\Bachelorarbeit\Tests\die_5.wav", daraaa , 44100, None, 2)
