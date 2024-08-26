import socket 
import sound_analysis
import numpy as np
import sys
import pyaudio
import threading
import wavio

#calibration noise
calibration_noise_virtual_path = r"C:\Users\Fritz\Documents\Bachelorarbeit\Tests\neuesTestsignal_3_unverändert.wav"
calibration_noise_virtual = sound_analysis.waveToList(r"C:\Users\Fritz\Documents\Bachelorarbeit\Tests\neuesTestsignal_3_unverändert.wav")

#instances
calibration_host = None
calibration_profile = None

#text based UI
#texts
input_misspelling = "\nThis Input did not resamble a given option.\nPease restate your instruction\n"
index = "\nWelcome to the True Fidelity set up Application!\n"
help_text = "This is a text based user interface, type in given option flag to continue\nThe option flag consists of only the character preceeded by '-'.\nFollowing the option flag you can find the option description.\nIn chase you still have questions that can not be answered via google search for\n'how to work with command line tools',\nfeel free to contact the creator of True Fidelity Friedrich Engelmann via E-Mail at:\nsacreeder@gmx.de\nThank you for being part of making Audio playback transparent!\n"
info_index = "\nThis is the Information page for setting up TrueFidelity db_calibration and assessment.\nIf this is your first time calibrating a devide,\nplease read this page carefully and completly.\n"
db_calibration_index = "\nThis is the db-meter calibration Mode.\nPlay the calibration noise and meassure the noise level at the system microphone using a calibrated db-meter or \nset the calibration offset directly."
#info
standard_definition = "\nstandard definition\n"
equipment_requirements = "\nquipment requirements\n"
environment_requirements = "\nenvironmental requirements\n"
setup_requirements = "\nsetup requirements\n"
#menus
index_menu = "\n-w connect device via WiFi\n-i True Fidelity info and Setup-Manual\n-q quit\n"
connect_menu = "\n-i True Fidelity info and Setup-Manual\n-c start db_calibration\n-r reconnect to different peer address\n-q quit\n"
info_menu = "\n-t True Fidelity Standard definition and classes\n-e True Fidelity Equipment requierement\n-n environment requierements\n-s setup requirements\n-q quit\n"
db_calibration_menu = "\n-p Play calibration noise and meassure manually\n-m set calibration offset directly\n-q quit\n"

#functions
#wifi
local_ip = '127.0.0.1'
peer_ip = None
local_port_number = 51515
peer_port_number = 15151
#db_meter
db_accuracy = None
db_calibration = 0
#recording/analysis stream
chunk_size = 1024
nchunks_sent = 0
new_chunk_sent = False
calibration_noise_recording = []
framerate = 44100
profile_accumulator = None
averaging_range = 10
convergence_factor = 1
difference = None
desired_accuracy = 1
durchgang = 0
calibration_start = None
#stream thread handles
stream_on = False
stream_terminate = False
#analysis thread handles
analysis_on = False
analysis_terminate = False

#dialogues
def calibration_dialogue_wifi():
            global calibration_host
            calibration_host = wifi_connect()
            if calibration_host != 1:
                eingabe = input(connect_menu)
                while True:
                    if eingabe=='i':
                        info_dialogue()
                        eingabe = input(connect_menu)
                    elif eingabe=='c':
                            calibrate()
                            eingabe = input(connect_menu)
                    elif eingabe=='r':
                        calibration_host.close()
                        wifi_connect()
                    elif eingabe=='q':
                        calibration_host.close()
                        break
                    else:
                        print(input_misspelling)
                        eingabe = input(connect_menu)
                pass

def info_dialogue():
    print(info_index)
    eingabe = input(info_menu)
    while True:
        if eingabe=='t':
            print(standard_definition)
            eingabe = input(info_menu)
        elif eingabe=='e':
            print(equipment_requirements)
            eingabe = input(info_menu)
        elif eingabe=='n':
            print(environment_requirements)
            eingabe = input(info_menu)
        elif eingabe=='s':
            print(setup_requirements)
            eingabe = input(info_menu)
        elif eingabe=='q':
            break
        else:
            print(input_misspelling)
            eingabe = input(info_menu)

def db_calibration_dialogue():
    global db_calibration
    while True:
        print(db_calibration_index)
        eingabe = input(db_calibration_menu)
        if eingabe=='p':
            calibration_host.send(("p").encode('utf-8'))
            system_measurement = set_volume('max', False, True)
            while True:
                manual_measurement = input("put in meassured db value: ")
                if type(float(manual_measurement)) == float:
                    db_calibration = manual_measurement-system_measurement
                    print(f"Db-calibration offset is {db_calibration}.")
                    break
                elif manual_measurement=='q':
                    break
                else:
                    print("Invalid input, please type in meassured db value as a number only or q to quit")
        elif eingabe=='m':
            while True:
                eingabe = input("put in meassured db value: ")
                if type(float(eingabe)) == float:
                    db_calibration = eingabe
                    print(f"Db-calibration offset is {db_calibration}.")
                    break
                elif manual_measurement=='q':
                    break
                else:
                    print("Invalid input, please type in desired db calibration offset as a number or q to quit")
        elif eingabe=='q':
            break

def index_dialogue():
    while True:
        print(index, help_text)
        eingabe = input(index_menu)
        while True:
            if eingabe=='w':
                calibration_dialogue_wifi()
                break
            elif eingabe=='i':
                info_dialogue()
                break
            elif eingabe=='c':
                db_calibration_dialogue()
                break
            elif eingabe=='q':
                return
            else:
                print(input_misspelling, help_text)
                eingabe = input(index_menu)

#functions
def wifi_connect(peer_ip=None, local_port_number=local_port_number):
    calibration_host = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    calibration_host.bind((local_ip, local_port_number))
    while True:
        peer_ip = input("Put in peer IP addresse: ")
        print(peer_ip)
        if peer_ip == 'q':
            return 1
        try:
            calibration_host.connect((peer_ip, peer_port_number))
            print("connected\n")
            break
        except:
            print("Peer address could not be connected to.\nPlease restate a valid peer address or press q to quit.\n")
    return calibration_host

def set_volume(volume, play=True, calibration_mode=False, db_calibration=0, db_accuracy=0.09):
    global calibration_host
    FORMAT = pyaudio.paInt16
    CHANNELS = 2
    RATE = 44100
    CHUNK = 1024
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                rate=RATE, input=True,
                frames_per_buffer=CHUNK)
    if volume=='max':
        calibration_host.send((f';{-1}').encode('utf-8'))
        if calibration_mode:
            while True:
                db = 0
                iterations = chunk_size//framerate
                for i in range(iterations):
                    data = stream.read(CHUNK)
                    calibration_noise_recording = np.frombuffer(data, np.int16)
                    db += 20*(np.log10(np.sqrt(np.mean([i**2 for i in calibration_noise_recording]))))+db_calibration
                db /= iterations
                eingabe = input(f"-q stop, meassurement: {db}")
                if eingabe == 'q':
                    return db
                else:
                    eingabe = input("invalid input, press q to stop")
        return
    if play:
        calibration_host.send(("p").encode('utf-8'))
    while True:
        db = 0
        for i in range(10):
            data = stream.read(CHUNK)
            calibration_noise_recording = np.frombuffer(data, np.int16)
            db += 20*(np.log10(np.sqrt(np.mean([i**2 for i in calibration_noise_recording]))))+db_calibration
        db /= 10
        convergenz_factor = 1
        if abs(volume-db)<db_accuracy:
            data = stream.read(CHUNK)
            calibration_noise_recording = np.frombuffer(data, np.int16)
            db = 20*(np.log10(np.sqrt(np.mean([i**2 for i in calibration_noise_recording]))))+db_calibration
            if abs(volume-db)<db_accuracy:
                print("Volume level: ", str(db)[:2])
                if play:
                    calibration_host.send(("s").encode('utf-8'))
                break
        elif (volume-db)<0:
            correctment = convergenz_factor*(volume-db)
            calibration_host.send((f';{correctment}').encode('utf-8'))
            convergenz_factor -= 0.1
        else:
            correctment = convergenz_factor*(volume-db)
            calibration_host.send((f';{correctment}').encode('utf-8'))
            convergenz_factor -= 0.1
    stream.stop_stream()
    stream.close()
    audio.terminate()
    return db

def play(play):
    global calibration_host
    if play:
        calibration_host.send(("p").encode('utf-8'))
        print("play")
    if not play:
        calibration_host.send(("s").encode('utf-8'))
    return

def spectrum_stream():
    #thread control handles
    global stream_on
    global stream_terminate
    #data
    global calibration_noise_recording
    global new_chunk_sent
    global nchunks_sent
    #local variables
    FORMAT = pyaudio.paInt16
    CHANNELS = 2
    RATE = 44100
    CHUNK = 1024
    #stream initialization
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                rate=RATE, input=True,
                frames_per_buffer=CHUNK)   
    while not stream_terminate:
        if stream_on:
            data = stream.read(CHUNK)
            calibration_noise_recording += (np.frombuffer(data, np.int16)).tolist()
            new_chunk_sent = True      
            nchunks_sent += 1
    stream.stop_stream()
    stream.close()
    audio.terminate()

def stream_analysis():
    #thread control handles
    global analysis_on
    global stream_on
    global analysis_terminate
    #data and structures
    global calibration_noise_recording
    global calibration_noise_virtual_path
    global chunk_size
    global new_chunk_sent
    global calibration_host
    global profile_accumulator
    global convergence_factor
    global difference
    global calibration_start
    #local variables
    offset = 44100
    end_offset = 44100
    #get synchpoints
    synchpoint_virtual = sound_analysis.synchpoint(calibration_noise_virtual_path, 44100)
    synchpoint_recording = None
    while not analysis_terminate: 
        #wait for recording to get up to length
        if len(calibration_noise_recording)>=44100:
            synchpoint_recording = sound_analysis.synchpoint(calibration_noise_recording, 44100)
            break
    #compare recording to virtual representation
    while not analysis_terminate:
        #wait for recording to get up to length
        if len(calibration_noise_recording)>=(synchpoint_recording + 2*offset):
            while analysis_on:
                if new_chunk_sent:
                    #reset trigger
                    new_chunk_sent = False
                    #window defintion
                    #recording
                    startindex_rec = synchpoint_recording+offset
                    endindex_rec = synchpoint_recording+offset+end_offset
                    #virtual
                    startindex_virt = synchpoint_virtual+offset
                    endindex_virt = synchpoint_virtual+offset+end_offset
                    #analysis
                    difference = sound_analysis.delta_spectrum(calibration_noise_recording[startindex_rec:endindex_rec], 
                                                                            calibration_noise_virtual[startindex_virt:endindex_virt], 
                                                                            20, 20000)
                    #calibration_start = sound_analysis.find_lowest_bass_match(difference, 0)
                    #print("realsound", len(calibration_noise_recording[startindex_rec:endindex_rec]), "virtual sound", len(calibration_noise_virtual[startindex_virt:endindex_virt]))
                    #print("indexe rec", startindex_rec, endindex_rec, "indexe virt", startindex_virt, endindex_virt)
                    #increment window 
                    offset += chunk_size
                    end_offset += chunk_size
                    #initialize accumulator                    
                    calibration_host.send(np.array(difference))
                    print("sent")
                    analysis_on = False
                    

def calibrate():
    #global vairables
    global stream_on
    global analysis_on
    global desired_accuracy
    global calibration_host
    global calibration_noise_recording
    global difference
    global durchgang
    desired_accuracy = 0.75
    accuracy = 10
    while desired_accuracy <= accuracy:
        stream_on = True
        print("play")
        play(True)
        analysis_on = True
        calibration_host.recv(1024)
        durchgang_data = np.array(calibration_noise_recording)
        wavio.write(f"C:\\Users\\Fritz\Documents\\Bachelorarbeit\\Tests\\output_durchgang_recording_{durchgang}.wav",  durchgang_data, 44100, None, 2)
        durchgang += 1
        calibration_noise_recording = []
        accuracy = max(max(difference), abs(min(difference)))
        print(accuracy)
        

t1 = threading.Thread(target=spectrum_stream)
t2 = threading.Thread(target=stream_analysis)
t1.start()
t2.start()
index_dialogue()
sys.exit()
