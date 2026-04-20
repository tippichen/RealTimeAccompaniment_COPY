import sys
import time
import queue
import threading
import os
from rtmidi.midiutil import open_midioutput, open_midiinput
from rtmidi.midiconstants import NOTE_OFF, NOTE_ON, SYSTEM_EXCLUSIVE, END_OF_EXCLUSIVE
import numpy as np

import tools.score_grapher_v0 as score_grapher_v0
import tools.score_sort_v0 as score_sort_v0
import matplotlib.pyplot as plt

import calculate_jerk

# piece=input('which piece (4,16,g)?')
# if piece=='4':
#     inputscorefile='SMC2024/gt/SMC_little_star_RH/outputscore.txt'
#     outputscorefile='SMC2024/gt/SMC_little_star_LH4/outputscore.txt'
# if piece=='16':
#     inputscorefile='SMC2024/gt/SMC_little_star_RH/outputscore.txt'
#     outputscorefile='SMC2024/gt/SMC_little_star_LH16/outputscore.txt'
# if piece=='g':
#     inputscorefile='SMC2024/gt/SMC_gounod_16_1/outputscore_concat.txt'
#     outputscorefile='SMC2024/gt/SMC_gounod_melody_1/outputscore_concat.txt'

# logtype=input('which type (h,a)?')

# #import scores
# with open(inputscorefile) as f:
#     inputscore=eval(f.read())

# with open(outputscorefile) as f:
#     outputscore=eval(f.read())

# print("will listen for input score:",inputscore)
# print("will listen for output score:",outputscore)
# #check that the scores are in proper order
# for index,note in enumerate(inputscore):
#     if not note[0]==index:
#         print("invalid inputscore")
#         exit()
# for index,note in enumerate(outputscore):
#     if not note[0]==index:
#         print("invalid outputscore")
#         exit()

def write_interpretation(performance,interpretation, piece_type):
    #make a list of all unique note-on inputscorepositions
    inputscorepositions=[-1]
    for note in interpretation:
        if not note[3]==inputscorepositions[-1] and note[1]==144:
            inputscorepositions+=[note[3]]
    inputscorepositions.append(10000) #to avoid error when processing the last note
    #print(inputscorepositions)
    lastinputIndex=-1
    lastinputscorepositionIndex=0

    unmatchednotes=0
    for msg in performance:
        foundmatch=0
        if msg[0]==144: 
            #print('looking in'+str(inputscorepositions[lastinputscorepositionIndex])+' to '+str(inputscorepositions[lastinputscorepositionIndex+1]+1.01)+' for '+str(interpretation[lastinputIndex+1][0:4])+str(interpretation[lastinputIndex+2][0:4])+str(interpretation[lastinputIndex+3][0:4]))
            # max_lookahead_index = min(lastinputscorepositionIndex + 4, len(inputscorepositions) - 1)
            for note in interpretation:
                if note[1]==144 and note[3]>=inputscorepositions[lastinputscorepositionIndex]-0.01 and note[3]<=inputscorepositions[lastinputscorepositionIndex+1]+5.01: #search between latest events' beat and next events' beat + 0.5
                # if note[1]==144 and note[3] >= inputscorepositions[lastinputscorepositionIndex] - 0.1 and note[3] <= inputscorepositions[max_lookahead_index] + 1.0:
                    if (note[2]==msg[1] or (not piece_type=="g" and note[0]<9 and (note[2]-msg[1])%12==0)) and note[4:]==[0,0]: #i.e. if it's the right note and hasn't been played yet
                        note[4]=msg[3] #time
                        note[5]=msg[2] #velocity
                        lastinputIndex=max(lastinputIndex,note[0])
                        lastinputscorepositionIndex=inputscorepositions.index(interpretation[lastinputIndex][3])
                        #print('lastinputscorepositionIndex',lastinputscorepositionIndex)
                        foundmatch=1
                        #print(str(time.time_ns())+'received '+str(msg)+' matched to '+str(note))
                        break
        if msg[0]==128:
            for note in reversed(interpretation): #find the last time that note was played
                if note[1]==144 and note[2]==msg[1] and not note[4:]==[0,0]:
                    for offnote in interpretation[note[0]:]: #search forward to find the nearest noteoff event
                        if offnote[1]==128 and offnote[2]==msg[1]:
                            if not offnote[4:]==[0,0]:
                                # print('already got this noteoff')
                                pass
                            offnote[4]=msg[3]
                            offnote[5]=msg[2]
                            foundmatch=1
                            #print(str(time.time_ns())+'received '+str(msg)+' matched to '+str(offnote))
                            break
                    break



        if foundmatch==0: #i.e. didn't find a match
            # print('could not match '+str(msg))
            unmatchednotes+=1

    total_msgs = len(performance)
    matched_msgs = total_msgs - unmatchednotes
    return interpretation, matched_msgs, total_msgs


def plottimecurve(interpretation,savefile):
    plt.clf()

    plt.figure(figsize=(20,20))

    plot_on_scorepositions=[]
    plot_on_times=[]

    plot_off_scorepositions=[]
    plot_off_times=[]
    for event in interpretation:
        if event[1]==144:
            plot_on_scorepositions+=[event[3]]
            plot_on_times+=[event[4]]
        else:
            plot_off_scorepositions+=[event[3]]
            plot_off_times+=[event[4]]

    plt.plot(plot_on_scorepositions,plot_on_times,'o')
    plt.plot(plot_off_scorepositions,plot_off_times,'x')

    if savefile=='show':
        plt.show()
    else:
        plt.savefig(savefile)
    plt.clf()
    return False


#datasetID=str(input('dataset ID?'))

#gh
# datasetIDs=[
#    '1_10',
#     '10_8',
#     '11_5',
#     '11_7',
#     '12_8',
#     '13_6',
#     '14_5',
#     '15_5',
#     '16_8',
#     '17_5',
#     '18_5',
#     '2_6',
#     '3_8',
#     '4_8',
#     '5_5',
#     '6_5',
#     '8_6',
#     '9_6']

#16h
# datasetIDs=['1_5',
# '1_8',
# '2_3',
# '3_4',
# '5_4',
# '6_4',
# '8_4',
# '10_4',
# '11_3',
# '12_5',
# '12_7',
# '13_3',
# '14_4',
# '15_3',
# '16_4',
# '17_3',
# '18_4']

#4h
# datasetIDs=['1_1',
# '10_2',
# '11_2',
# '12_1',
# '12_2',
# '13_2',
# '14_2',
# '15_2',
# '16_2',
# '17_2',
# '18_2',
# '2_2',
# '3_1',
# '5_1',
# '6_1',
# '8_1',
# '9_1']

#4a
# datasetIDs=['1_2',
# '1_3',
# '10_1',
# '11_1',
# '12_3',
# '13_1',
# '13_7',
# '14_1',
# '15_1',
# '16_1',
# '16_3',
# '17_1',
# '18_1',
# '2_1',
# '3_2',
# '5_2',
# '6_2',
# '8_2',
# #'9_2',
# '9_3']

# #16a
# datasetIDs=['1_4',
# '1_6',
# '10_3',
# '10_5',
# '11_4',
# '12_4',
# '12_6',
# '13_4',
# '14_3',
# '15_4',
# '16_5',
# '17_4',
# '18_3',
# '2_4',
# '3_3',
# '4_10',
# '4_2',
# '4_3',
# '4_6',
# '5_3',
# '6_3',
# '8_3',
# '9_4']

#ga
# datasetIDs=['1_11',
# '1_12',
# '1_13',
# '10_7',
# '11_6',
# '12_10',
# '12_11',
# '13_5',
# '14_6',
# '15_6',
# '16_6',
# '16_7',
# '17_6',
# '18_6',
# '2_5',
# '3_5',
# '3_7',
# '4_7',
# '5_6',
# '6_6',
# '6_7',
# '7_1',
# '8_5',
# '9_7']


datasetIDs=['4_1']

pieces_to_test = ['4', '16', 'g']
logtypes_to_test = ['h', 'a']

outputjerksum=[]

for datasetID in datasetIDs:
    print('processing '+str(datasetID))
    with open('SMC2024/data/'+datasetID+'/inputmsglog.txt') as f:
        performance=eval(f.read())

    best_match_rate = -1
    best_config = None
    best_results = None

    for p in pieces_to_test:
        for lt in logtypes_to_test:
            if p == '4':
                inputscorefile='SMC2024/gt/SMC_little_star_RH/outputscore.txt'
                outputscorefile='SMC2024/gt/SMC_little_star_LH4/outputscore.txt'
            elif p == '16':
                inputscorefile='SMC2024/gt/SMC_little_star_RH/outputscore.txt'
                outputscorefile='SMC2024/gt/SMC_little_star_LH16/outputscore.txt'
            elif p == 'g':
                inputscorefile='SMC2024/gt/SMC_gounod_16_1/outputscore_concat.txt'
                outputscorefile='SMC2024/gt/SMC_gounod_melody_1/outputscore_concat.txt'

            with open(inputscorefile) as f:
                inputscore=eval(f.read())

            with open(outputscorefile) as f:
                outputscore=eval(f.read())

            inputperformance=[]
            outputperformance=[]
            for event in performance:
                if event[0]=='Keyboard2' or event[0]=='Input':
                    inputperformance+=[event[1:]]
                else:
                    outputperformance+=[event[1:]]

            if lt=='a':
                try:
                    with open('SMC2024/data/'+datasetID+'/realoutputlog.txt') as f:
                        outputtimings=eval(f.read())
                    outputperformance = []
                    i=0
                    for note in outputscore:
                        if note[1]==144:
                            outputperformance+=[[144,note[2],1,outputtimings[i]]]
                            i+=1
                            if i>len(outputtimings):
                                break   
                except FileNotFoundError: 
                    continue
            
            inputinterpretation=[event+[0,0] for event in inputscore]
            outputinterpretation=[event+[0,0] for event in outputscore]

            aligned_in, in_match, in_total=write_interpretation(inputperformance,inputinterpretation,p)
            aligned_out, out_match, out_total=write_interpretation(outputperformance,outputinterpretation,p)

            total_events = in_total + out_total
            match_rate = (in_match + out_match) / total_events if total_events > 0 else 0

            print(f"Test [Piece: {p:2}, Type: {lt}] -> match rate: {match_rate:.2%} ({in_match+out_match}/{total_events})")

            if match_rate > best_match_rate:
                best_match_rate = match_rate
                best_config = (p, lt)
                best_results = (aligned_in, aligned_out)

    if best_config:
        best_p, best_lt = best_config
        print(f"\nDataset {datasetID}: Best Piece={best_p}, LogType={best_lt} (match rate: {best_match_rate:.2%})")

        inputinterpretation = best_results[0]
        outputinterpretation = best_results[1]

        with open('SMC2024/data/'+datasetID+'/inputinterpretation.txt',"w") as f:
            f.write(str(inputinterpretation))

        with open('SMC2024/data/'+datasetID+'/outputinterpretation.txt',"w") as f:
            f.write(str(outputinterpretation))

        # outputfile=open('SMC2024/data/'+datasetID+'/inputinterpretation.txt',"w")
        # outputfile.write(str(inputinterpretation))
        # outputfile.close()

        # outputfile=open('SMC2024/data/'+datasetID+'/outputinterpretation.txt',"w")
        # outputfile.write(str(outputinterpretation))
        # outputfile.close()

        inputjerk=calculate_jerk.jerk(inputinterpretation)
        outputjerk=calculate_jerk.jerk(outputinterpretation)

        outputjerksum+=[outputjerk]


    # plottimecurve(inputinterpretation,'data/'+datasetID+'/inputTimeCurve.png')
    # plottimecurve(outputinterpretation,'data/'+datasetID+'/outputTimeCurve.png')

    #totalinterpretation=score_sort_v0.sort(4,inputinterpretation+outputinterpretation)
    # score_grapher_v0.graph(inputinterpretation,'data/'+datasetID+'/inputinterpretation.png')
    # score_grapher_v0.graph(outputinterpretation,'data/'+datasetID+'/outputinterpretation.png')

result=open(str(time.time())+'jerk.txt','w')
result.write(str(outputjerksum))


# #initialize arduino mirror
# arduinoarray=[[-1,0,0,0,0]]*50



# #get MIDI ports
# port = sys.argv[1] if len(sys.argv) > 1 else None
# try:
#     midiout, port_name_out = open_midioutput(port)
#     midiin, port_name_in = open_midiinput(port)
# except (EOFError, KeyboardInterrupt):
#     sys.exit()

# q = queue.Queue()

# def sendRealTimeStamp():
#     timeStamp = time.time_ns()
#     timeStampSysEx = []
#     timeStampSysEx.append(SYSTEM_EXCLUSIVE)
#     timeStampSysEx.append(0x00)
#     timeStampSysEx.append(0x00)
#     timeStampSysEx.append(0x00)
#     for i in str(timeStamp):
#         timeStampSysEx.append(int(i)) 
#     timeStampSysEx.append(END_OF_EXCLUSIVE)
#     midiout.send_message(timeStampSysEx)


# def sendEventTimeStamp(messageType, dataByte1, dataByte2,dataByte3, predictionTimeStamp):
#     timeStamp = predictionTimeStamp
#     timeStampSysEx = []
#     timeStampSysEx.append(SYSTEM_EXCLUSIVE)
#     timeStampSysEx.append(messageType - 127)
#     timeStampSysEx.append(dataByte1)
#     timeStampSysEx.append(dataByte2)
#     timeStampSysEx.append(dataByte3)
#     for i in str(timeStamp)[1:]:
#         timeStampSysEx.append(int(i)) 
#     timeStampSysEx.append(END_OF_EXCLUSIVE)
#     midiout.send_message(timeStampSysEx)
#     print(timeStampSysEx)

# def sendEvent(arduinoarrayElement,arrayPosition): #arduinoarrayElement has following structure: [index,type,note,time,velocity]
#                                                     #timeStampSysEx: [240,arrayposition,type-127,note,velocity,index,time...]
#     #print('writing arduinoarrayElement',arduinoarrayElement,' to array position',arrayPosition)
#     timeStamp = arduinoarrayElement[3]
#     timeStampSysEx = []
#     timeStampSysEx.append(SYSTEM_EXCLUSIVE)
#     timeStampSysEx.append(arrayPosition)
#     timeStampSysEx.append(arduinoarrayElement[1] - 127)
#     timeStampSysEx.append(arduinoarrayElement[2])
#     timeStampSysEx.append(arduinoarrayElement[4])
#     timeStampSysEx.append(arduinoarrayElement[0])
#     for i in str(timeStamp)[1:]:
#         timeStampSysEx.append(int(i)) 
#     timeStampSysEx.append(END_OF_EXCLUSIVE)
#     midiout.send_message(timeStampSysEx)
#     print(timeStampSysEx)


# framerate=100
# theta1=np.zeros(200*framerate)
# theta2=np.zeros(200*framerate)
# theta3=np.zeros(200*framerate)

# reactiontime=10 #in frames

# Omega2=0.002
# Omega3=0.002
# theta2[0]=0
# theta2[1]=Omega2
# theta3[0]=0
# theta3[1]=Omega2

# K21=0.1
# K23=0.1
# K32=0.1

# def calculating(stop_flag):
#     starttime=time.time_ns()/1000000000
#     global lastinputIndex,lastinputscorepositionIndex
#     global theta1,theta2,theta3
#     global outputinterpretation
#     global arduinoarray
#     while not stop_flag.is_set():
#         if not q.empty():
#             msg = q.get()
#             #sendEventTimeStamp(msg[0], msg[1]+4, msg[2], msg[3]+250000000)
#             #figure out which input note msg corresponds to. 
#             foundmatch=0
#             if msg[0]==144: 
#                 for note in inputinterpretation:
#                     if note[1]==144 and note[3]>=inputscorepositions[lastinputscorepositionIndex]-0.01 and note[3]<=inputscorepositions[lastinputscorepositionIndex+1]+0.51: #search between latest events' beat and next events' beat + 0.5
#                         if note[2]==msg[1] and note[4:]==[0,0]: #i.e. if it's the right note and hasn't been played yet
#                             note[4]=msg[3]/1000000000
#                             note[5]=msg[2]
#                             lastinputIndex=max(lastinputIndex,note[0])
#                             lastinputscorepositionIndex=inputscorepositions.index(inputinterpretation[lastinputIndex][3])
#                             #print('lastinputscorepositionIndex',lastinputscorepositionIndex)
#                             foundmatch=1
#                             print(str(time.time_ns())+'received '+str(msg)+' matched to '+str(note))
#                             break
#             if msg[0]==128:
#                 for note in reversed(inputinterpretation): #find the last time that note was played
#                     if note[1]==144 and note[2]==msg[1] and not note[4:]==[0,0]:
#                         for offnote in inputinterpretation[note[0]:]: #search forward to find the nearest noteoff event
#                             if offnote[1]==128 and offnote[2]==msg[1]:
#                                 if not offnote[4:]==[0,0]:
#                                     print('already got this noteoff')
#                                 offnote[4]=msg[3]/1000000000
#                                 offnote[5]=msg[2]
#                                 foundmatch=1
#                                 print(str(time.time_ns())+'received '+str(msg)+' matched to '+str(offnote))
#                                 break
#                         break



#             if foundmatch==0: #i.e. didn't find a match
#                 print('could not match '+str(msg))
#             else:
#                 #model
#                 #create piecewise linear theta1
#                 points=[[0,-1]]
#                 for position in inputscorepositions:
#                     timing=[]
#                     for note in inputinterpretation:
#                         if note[1]==144 and note[3]==position and not note[4:]==[0,0]:
#                             timing+=[note[4]-starttime]
#                         if note[3]>position:
#                             break
#                     if position>inputscorepositions[lastinputscorepositionIndex]+1:
#                         break
#                     if not len(timing)==0:
#                         points+=[[np.mean(timing),position]]
#                 points.sort(key = lambda x: x[0])
#                 #print('points',points)
#                 for i in range(1,len(points)):
#                     for t in range(int(points[i-1][0]*framerate),int(points[i][0]*framerate)):
#                         theta1[t]=points[i-1][1]+(t/framerate-points[i-1][0])*(points[i][1]-points[i-1][1])/(points[i][0]-points[i-1][0])

#                         if t<100:
#                             currentspeed2=Omega2
#                             currentspeed3=Omega2
#                         if t>99:
#                             currentspeed2=(theta2[t]-theta2[t-100])/100
#                             currentspeed3=(theta3[t]-theta3[t-100])/100
#                         theta2[t+1]=theta2[t]+currentspeed2+K21*(theta1[t]-theta2[t])+K23*(theta3[t]-theta2[t])
#                         theta3[t+1]=theta3[t]+currentspeed3+K32*(theta2[t]-theta3[t])

#                 #predict output timings
#                 lastcalculatedtheta3frame=int(points[-1][0]*framerate)
#                 theta3slope=theta3[lastcalculatedtheta3frame]-theta3[lastcalculatedtheta3frame-1]
#                 theta3yIntercept=theta3[lastcalculatedtheta3frame]-theta3slope*lastcalculatedtheta3frame
#                 #print(theta3slope,' ',theta3yIntercept)
#                 for note in outputinterpretation:
#                     outputtime=starttime+(note[3]-theta3yIntercept)/theta3slope/framerate
#                     if note[4]<time.time_ns()/1000000000+reactiontime/framerate and note[4]>time.time_ns()/1000000000:
#                         pass
#                     else:
#                         note[4]=outputtime
#                         if note[4]<time.time_ns()/1000000000+reactiontime/framerate and note[4]>time.time_ns()/1000000000:
#                             note[4]=time.time_ns()/1000000000+reactiontime/framerate
#                     #figure out velocity (running average)
#                     velocity_range=[]
#                     for inputnote in inputinterpretation:
#                         if inputnote[1]==144 and inputnote[3]>=note[3]-1 and not inputnote[5]==0: #search for already played notes starting from 1 beat ago
#                             velocity_range+=[inputnote[5]]
#                     current_desired_velocity=int(min(127,20+1.2*np.mean(velocity_range)))
#                     note[5]=current_desired_velocity
#             # now outputting to arduinoarray
#                     wrotetoarray=0
#                     clearpositions=[]
#                     for i in range(50):
#                         if arduinoarray[i][0]==note[0]: #if the indices match, i.e. the note is to be overwritten with the new prediction, or the index is blank:
#                             arduinoarray[i]=[note[0],note[1],note[2],int(note[4]*1000000000),note[5]]
#                             sendEvent(arduinoarray[i],i)
#                             wrotetoarray=1
#                         #print(time.time_ns(),'event at position',i,'happens in',(arduinoarray[i][3]-time.time_ns())/1000000000)
#                         if arduinoarray[i][3]<time.time_ns()-1000000000: #i.e. if it should have already happened more than a second ago
#                             arduinoarray[i][1]=0 #make the array position ready to be assigned to a new event
#                             clearpositions+=[i]
#                             #print('cleared array position', i)
#                     if wrotetoarray==0 and note[4]>=time.time_ns()/1000000000-1:
#                         for i in clearpositions:
#                             arduinoarray[i]=[note[0],note[1],note[2],int(note[4]*1000000000),note[5]]
#                             sendEvent(arduinoarray[i],i)
#                             wrotetoarray=1
#                             break
#                     # if wrotetoarray==0:
#                     #     print('no space in arduinoarray')
#                 #print('outputinterpretation',outputinterpretation)


#             q.task_done()





# stop_flag = threading.Event()
# threading.Thread(target=calculating, args=(stop_flag,)).start()

# while True:
#     try:
#         sendRealTimeStamp()
#         msg = midiin.get_message()
#         if msg:
#             if msg[0][0] == NOTE_ON or msg[0][0] == NOTE_OFF:
#                 q.put((msg[0][0], msg[0][1], msg[0][2], time.time_ns()))
#     except (EOFError, KeyboardInterrupt):
#         stop_flag.set()
#         threading.Thread(target=calculating, args=(stop_flag,)).join
#         q.join()

#         logdirectory="logs/real_accomp_"+str(time.time())
#         os.makedirs(logdirectory)

#         inputfile=open(logdirectory+"/inputinterpretation.txt","w")
#         inputfile.write(str(inputinterpretation))
#         inputfile.close()

#         outputfile=open(logdirectory+"/outputinterpretation.txt","w")
#         outputfile.write(str(outputinterpretation))
#         outputfile.close()

#         combinedinterpretation=score_sort_v0.sort(4,inputinterpretation+outputinterpretation)

#         combinedfile=open(logdirectory+"/combinedinterpretation.txt","w")
#         combinedfile.write(str(combinedinterpretation))
#         combinedfile.close()

#         score_grapher_v0.graph(inputinterpretation,logdirectory+'/inputplot.png')
#         score_grapher_v0.graph(outputinterpretation,logdirectory+'/outputplot.png')
#         score_grapher_v0.graph(combinedinterpretation,logdirectory+'/combinedplot.png')

#         print('Exit')
#         sys.exit()        