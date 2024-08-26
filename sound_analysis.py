import wave
from matplotlib import pyplot as plt
import numpy as np
import math
import wavio 


def display_pegel(file):
    try:
        waveList = waveToList(file)
    except:
        waveList = file
    xAxis = [i for i in range(len(waveList))]
    plt.plot(xAxis, waveList)
    plt.show()

def waveToList(file):
    try: 
        fileWave = wave.open(file, 'rb').readframes(-1)
        fileWave_Array = np.frombuffer(fileWave, np.int16)
        fileWave_List = fileWave_Array.tolist()
        return fileWave_List
    except:
        fileWave_List = file
        return fileWave_List
    
def find_lowest_bass_match(difference, accuracy=0):
    for i in difference:
        if i<=accuracy:
            return i
        
def equality_factor(difference):
    max = 0
    for i in difference:
        if abs(i) > max:
            max = abs(i)
    return max

def synchpoint(file, lookupRange):
    #turn to list
    fileWave_List = waveToList(file)
    #looking up synchpoint
    minIndex = 0
    maxIndex = 0
    for i in range(lookupRange-1):
        if fileWave_List[i] <= fileWave_List[minIndex]:
            minIndex = i
        if fileWave_List[i] >= fileWave_List[maxIndex]:
            maxIndex = i
    return maxIndex

def spectrum_analysis(file, offset, lowpassLimit=20, highpassLimit=20000, frameRate=44100, display=False):    
    #converting to list    
    waveList = waveToList(file)
    #compute frequency domain
    frequencyIntensity = np.abs(np.fft.fft(waveList[0+offset : frameRate+offset]))[lowpassLimit:highpassLimit]
    #display or return
    if not display:
        return (frequencyDomain, frequencyIntensity, lowpassLimit, highpassLimit)
    else:
        #setting up x-scale
        frequencyDomain_range = highpassLimit-lowpassLimit
        frequencyDomain = np.linspace(lowpassLimit, highpassLimit, frequencyDomain_range)
        plt.plot(frequencyDomain, frequencyIntensity)
        plt.xscale('log')
        plt.yscale('log')
        plt.show()

def spectrum_analysis_sweep(file, lowpassLimit=20, highpassLimit=20000, frameRate=44100, display=False):    
    #converting to list    
    waveList = waveToList(file)
    #making sure wave list is in form 2n
    if len(waveList)%2 != 0:
        waveList.append(0)
    #compute frequency domain
    bins_per_whole_frequency = int(len(waveList)/frameRate)
    start_index_positive_values = int(len(waveList)/2)
    frequencyIntensity = np.fft.fftshift(np.abs(np.fft.fft(waveList)))[start_index_positive_values:]
    frequencyIntensity_whole_frequencies = [0 for frequency in range(int(frameRate/2))]
    for bin_whole_frequency in range(len(frequencyIntensity_whole_frequencies)):
        whole_frequency_intensity = 0
        bin_start_index = bin_whole_frequency*bins_per_whole_frequency
        for bin_fft in range(bins_per_whole_frequency):
            whole_frequency_intensity += frequencyIntensity[bin_start_index+bin_fft]
        whole_frequency_intensity /= bins_per_whole_frequency
        frequencyIntensity_whole_frequencies[bin_whole_frequency] = whole_frequency_intensity/start_index_positive_values
        frequencyIntensities = frequencyIntensity_whole_frequencies[lowpassLimit : highpassLimit]
    for i in range(len(frequencyIntensities)):
        frequencyIntensities[i] /= (len(waveList)/2)
    if not display:
        return frequencyIntensities
    else:
        frequencyDomain_range = highpassLimit-lowpassLimit
        frequencyDomain = np.linspace(lowpassLimit, highpassLimit, frequencyDomain_range)
        plt.plot(frequencyDomain, frequencyIntensities)
        plt.yscale('log')
        plt.xscale('log')
        plt.show()
    

def delta_spectrum(realSound, virtualSound, lowpassLimit, highpassLimit, synch=False, framerate=44100, noAmplification=True, display=False):
    frequencyRange = highpassLimit-lowpassLimit
    if synch:
        startIndex_real = synchpoint(realSound, 44100)
        startIndex_virtual = synchpoint(virtualSound, 44100)
    else:
        startIndex_real = 0
        startIndex_virtual = 0
    realSpectrum = spectrum_analysis(realSound, startIndex_real, lowpassLimit, highpassLimit, framerate, False)[1]
    virtualSpectrum = spectrum_analysis(virtualSound, startIndex_virtual, lowpassLimit, highpassLimit, framerate, False)[1]
    difference = [virtualSpectrum[i] - realSpectrum[i] for i in range(0, frequencyRange)]
    if noAmplification:
        differenceMax = max(difference)
        difference = [difference[i]-differenceMax for i in range(0, frequencyRange)]
    if not display:
        return difference
    else:
        frequencyX = np.linspace(lowpassLimit, highpassLimit, highpassLimit-lowpassLimit).tolist()
        plt.plot(frequencyX, difference)
        plt.xscale('log')
        plt.show()

def adjustment_profile(realSound, virtualSound, lowpassLimit, highpassLimit, filterSize=True, framerate=44100):
    target_response = delta_spectrum(realSound, virtualSound, lowpassLimit, highpassLimit, False, 44100, False)
    difference = target_response
    iCoefficients = np.fft.ifft(target_response)
    coefficients = [abs(i) for i in iCoefficients]
    if filterSize == True:
        return (coefficients, difference)
    else:
        coefficient_subset = []
        averagingRange = math.floor(len(coefficients)//filterSize)
        for i in range(filterSize):
            coefficient = 0
            for x in range(math.floor(averagingRange//2)):
                coefficient += coefficients[i*averagingRange + x]
                coefficient += coefficients[i+1*averagingRange - x]
            coefficient /= averagingRange
            coefficient_subset.append(coefficient)
        return (coefficient_subset, difference)


def adjustment_profile_2(difference, centerFrequencies):
    koeffs = []
    for x in range(len(centerFrequencies)-1):
        koeff = 0
        n_values = len(difference[centerFrequencies[x]:centerFrequencies[x+1]])
        for i in range(n_values):
            koeff += difference[centerFrequencies[x]+i]
        koeff/=n_values
        koeffs.append(koeff)
    return koeffs

def dingennns():
    waveList = waveToList(r"C:\Users\Fritz\Documents\Bachelorarbeit\Tests\die_5.wav")
    fft_normiert = [0 for i in range(19980)]
    chunksize = 1024
    n_chunks = math.floor((len(waveList)-44100)/chunksize)
    for i in range(n_chunks):
        spectrum = spectrum_analysis(waveList, i*chunksize, 20, 19000, 44100)[1]
        for x in range(len(fft_normiert)):
            fft_normiert[x] += spectrum[x]
    for i in range(len(fft_normiert)):
        fft_normiert[i] /= n_chunks
    x = np.linspace(20, 20000, 19980)
    y = fft_normiert
    plt.plot(x, y)
    plt.xscale('log')
    plt.yscale('log')
    plt.show()


def list_to_wave(liste, wave_path):
    wave_file = wave.open(wave_path, 'wb')
    nframes = len(liste)
    wave_data = np.array(liste)
    wave_file.setnframes(nframes)   
    wave_file.setnchannels(1)
    wave_file.setframerate(44100)
    wave_file.setsampwidth(2)
    wave_file.writeframes(wave_data)
    wave_file.close()

def spectrum_analysis(file, offset=0, lowpassLimit=20, highpassLimit=20000):    
    waveList = waveToList(file)
    n_frequency_bins = len(waveList)
    frequencyIntensity = np.abs(np.fft.fft(waveList[offset : offset+n_frequency_bins]))[lowpassLimit:highpassLimit]
    return frequencyIntensity



def ifft_levels(sweep_wave, noise_level=None):
    sweep_list = waveToList(sweep_wave)
    sweep_synch = synchpoint(sweep_list, 22050)
    #get noise level
    if noise_level == None:
        noise = sweep_list[0:(sweep_synch-500)] + sweep_list[(sweep_synch+1000):(sweep_synch+22050)]
        noise_level = max(noise)  
    max_pegel = max(sweep_list)
    for index in range(len(sweep_list)):    #denoise and get frequency levels
        sample = sweep_list[index]  
        if sample <= noise_level:   #denoiseing
            sweep_list[index] = 0
        sweep_list[index] = 32767 - abs(sample)   #get frequency levels
    return sweep_list


def ifft_frequencies(ifft_levels, wave_file, lowpass_limit=20, highpass_limit=20000, framerate=44100):
    #levels
    ifft_levels_synch = synchpoint(ifft_levels, 22050)
    ifft_levels_start = ifft_levels_synch + 11025
    ifft_levels_values = ifft_levels[ifft_levels_start:]
    #frequencies
    wave_list = waveToList(wave_file)
    wave_list_synch = synchpoint(wave_list, 22050)
    wave_list_start = wave_list_synch + 11025
    wave_list_frequencies = wave_list[wave_list_start:]
    wave_list_frequencies_padded = [0 for i in range(22050)] + wave_list_frequencies + [0 for i in range(22050)]
    #get filter start index
    filter_start_index = 0
    for index in range(len(ifft_levels_values)):
        if ifft_levels_values[index] <= 10000:
            filter_start_index = index
            break
    #prepare frequency catching
    n_fft_datapoints = int(framerate/2)
    n_frequency_samples = len(ifft_levels_values[filter_start_index:])
    ifft_frequencies = []
    for current_index in range(n_frequency_samples):
        #prepare spectrum analysis
        filter_index = filter_start_index + current_index
        frequency_chunk = wave_list_frequencies_padded[filter_index-n_fft_datapoints: filter_index+n_fft_datapoints]
        blackman_window = np.blackman(len(frequency_chunk))
        frequency_chunk_blackmanned = [frequency_chunk[index] * blackman_window[index] for index in range(len(frequency_chunk))]
        #analyse
        frequency_spectrum = spectrum_analysis(frequency_chunk_blackmanned)
        #find target frequency
        max_frequency_intensity = 0
        target_frequency = 0
        for frequency in range(len(frequency_spectrum)):
            frequency_intensity = frequency_spectrum[frequency]
            if frequency_intensity > max_frequency_intensity:
                max_frequency_intensity = frequency_intensity
                target_frequency = frequency
        ifft_frequencies.append(target_frequency)
        print(target_frequency)
    return ifft_frequencies
    
def ifft_profile_2(ifft_levels, wave_file, lowpass_limit=20, highpass_limit=20000, framerate=44100):
    #levels
    ifft_levels_synch = synchpoint(ifft_levels, 22050)
    ifft_levels_start = ifft_levels_synch + 11025
    ifft_levels_values = ifft_levels[ifft_levels_start:]
    #frequencies
    wave_list = waveToList(wave_file)
    wave_list_synch = synchpoint(wave_list, 22050)
    wave_list_start = wave_list_synch + 11025
    wave_list_frequencies = wave_list[wave_list_start:]
    #get filter start index
    filter_start_index = 0
    
    n_samples = len(wave_list_frequencies[wave_list_start:])
    complement_frequency_response = []
    for index in range(n_samples):
        complement_frequency_response_sample = (ifft_levels_values[filter_start_index+index]) * wave_list_frequencies[filter_start_index+index]
        complement_frequency_response.append(complement_frequency_response_sample)
    return complement_frequency_response


a = ifft_levels(r"C:\Users\Fritz\Documents\Bachelorarbeit\Tests\linear_sweep_synch_rec.wav", None)

ifft_frequencies(a, r"C:\Users\Fritz\Documents\Bachelorarbeit\Tests\1Hz-20kHz linear_sweep_synch.wav")