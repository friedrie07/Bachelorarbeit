import numpy as np
import wavio
import sound_analysis
def dingens():
    dings = sound_analysis.waveToList(r"C:\Users\Fritz\Documents\Bachelorarbeit\Tests\neuesTestsignal_3_unverändert.wav")
    out = []
    for i in (dings):
        i /= 32767
        #out.append(band_20.filter(i))
    outing = np.array(out)
    wavio.write(r"C:\Users\Fritz\Documents\Bachelorarbeit\Tests\die_5.wav", outing, 44100, None , 2)

class filt():
    def __init__(self, centerFrequency_Hz, bandwidth_Hz, boostCut_linear, buffer_index=None, framerate=44100):
        self.buffer_index = buffer_index
        self.centerFrequency_Hz = centerFrequency_Hz
        self.bandwidth_Hz = bandwidth_Hz
        self.boostCut_linear = boostCut_linear
        self.sampleTime_s = 1/framerate
        self.x = [0 for i in range(3)] 
        self.y = [0 for i in range(3)] 
        self.a = [0 for i in range(3)] 
        self.b = [0  for i in range(3)] 
        M_PI = 3.1415926535897932384626433
        wcT = 2.0 * np.tan( M_PI * centerFrequency_Hz * self.sampleTime_s) 
        Q = bandwidth_Hz / centerFrequency_Hz 

        self.a[0] = 4.0 + 2.0 * (boostCut_linear / Q) * wcT + wcT * wcT 
        self.a[1] = 2.0 * wcT * wcT -8.0 
        self.a[2] = 4.0 - 2.0 * (boostCut_linear / Q) * wcT + wcT * wcT 

        self.b[0] = 1.0 / (4.0 + 2.0 / Q * wcT + wcT * wcT) 
        self.b[1] = -(2.0 * wcT * wcT - 8.0) 
        self.b[2] = -(4.0 - 2.0 / Q * wcT + wcT * wcT) 

    def peakingFselfer_updateParams(self, centerFrequency_Hz, bandwidth_Hz, boostCut_linear):
        M_PI = 3.1415926535897932384626433
        wcT = 2.0 * np.arctan( M_PI * centerFrequency_Hz * self.sampleTime_s) 
        Q = bandwidth_Hz / centerFrequency_Hz 

        self.a[0] = 4.0 + 2.0 * (boostCut_linear / Q) * wcT + wcT * wcT 
        self.a[1] = 2.0 * wcT * wcT -8.0 
        self.a[2] = 4.0 - 2.0 * (boostCut_linear / Q) * wcT + wcT * wcT 

        self.b[0] = 1.0 / (4.0 + 2.0 / Q * wcT + wcT * wcT) 
        self.b[1] = -(2.0 * wcT * wcT - 8.0) 
        self.b[2] = -(4.0 - 2.0 / Q * wcT + wcT * wcT) 


    def filter(self, input):
        self.x[2] = self.x[1] 
        self.x[1] = self.x[0] 
        self.x[0] = input 

        self.y[2] = self.y[1] 
        self.y[1] = self.y[0] 

        self.y[0] = (self.a[0] * self.x[0] + self.a[1] * self.x[1] + self.a[2] * self.x[2] +
                        (self.b[1] * self.y[1] + self.b[2] * self.y[2])) * self.b[0] 
        return self.y[0]

class equalizer():
    def __init__(self, n_bands, lowpass_limit=20, highpass_limit=20000, overlap=1, framerate=44100):
        self.n_bands = n_bands
        self.lowpass_limit = lowpass_limit
        self.highpass_limit = highpass_limit
        self.overlap = overlap
        self.framerate = framerate
        self.bands = []
        self.buffer = [0 for i in range(self.n_bands)]
        #create band centers
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
        boarder = lowpass_limit
        band_widths = []
        for center in band_centers:
            width = 2*(center - boarder)+overlap
            boarder = center + width/2
            band_widths.append(width)
        #instanciate filter bands
        buffer_index = 0
        for i in range(self.n_bands):
            band_center = band_centers[i]
            band_width = band_widths[i]
            default_boost = 1
            buffer_index = i
            self.bands.append(filt(band_center, band_width, default_boost, buffer_index))

    def set_band_boost(self, band_boost_factor):
        for i in range(self.n_bands):
            band = self.bands[i]
            band.boostCut_linear = band_boost_factor[i]

    def set_singel_band(self, band, centerfrequency, bandwidth, band_boost_factor):
        self.bands[band].boostCut_linear = band_boost_factor
        self.bands[band].centerFrequency_Hz = centerfrequency
        self.bands[band].bandwidth_Hz = bandwidth

    def equalize(self, input):
        input/=32767
        self.buffer[0] = input
        for i in range(self.n_bands-1):
            filt_obj = self.bands[i]
            input = self.buffer[i]
            output = filt_obj.filter(input)
            self.buffer[i+1] = output
        return self.buffer[self.n_bands-1]
    def equlize_2(self, input_list):
        out = input_list
        for i in self.bands:
            for x in range(len(out)):
                input = out[x]
                input/=32767
                erg = i.filter(input)
                out[x] = erg
        return out
        




x = equalizer(50, 20, 20000, 5, 44100)
x.set_band_boost([1 for i in range(25)] + [0.01 for i in range(25)])
dings = sound_analysis.waveToList(r"C:\Users\Fritz\Documents\Bachelorarbeit\Tests\neuesTestsignal_3_unverändert.wav")[0:200000]
neu = x.equlize_2(dings)
print(sound_analysis.synchpoint(neu, 44100))

neuer = np.array(neu)
wavio.write(r"C:\Users\Fritz\Documents\Bachelorarbeit\Tests\die_5.wav", neuer, 44100, None , 2)

sound_analysis.synchpoint()