#given score in [i,o,#,p] format, MIDI recording in [o,#,v,t] format





def nextscorepos(score,p):
    for note in score:
        if note[3]>p+0.01 and note[0]==144:
            return note[3]
    return max(score,key=lambda x:x[3])[3]

def align(midi,score):
    midi=sorted(midi,key=lambda x:x[3])
    inputinterpretation=[{'part':0,'index':event[0],'on_off':event[1],'note#':event[2],'score_pos':event[3],'time':None,'vel':None} for event in score]
    latest_input_pos=0
    latest_input_index=0
    aligned_events=[]
    unaligned_events=[]
    for inputmsg in midi:
        foundmatch=0
        if inputmsg[0]==144:
            index=0#min(inputscorepositions.get(latest_input_pos)) #we get all the notes, even if the score_pos is off by a float error, by def of inputscorepositions
            while index<len(inputinterpretation) and inputinterpretation[index]['score_pos']<nextscorepos(score,latest_input_pos)+0.51:
                #print(inputmsg,index)
                if [inputinterpretation[index]['on_off'],inputinterpretation[index]['note#']]==[144,inputmsg[1]] and inputinterpretation[index].get('time') is None:
                    inputinterpretation[index]['vel']=inputmsg[2]
                    inputinterpretation[index]['time']=inputmsg[3]
                    latest_input_index=max(index,latest_input_index)
                    latest_input_pos=max(inputinterpretation[index]['score_pos'],latest_input_pos)
                    foundmatch=1
                    break
                index+=1
        if inputmsg[0]==128:
            index=latest_input_index
            foundon=0
            while index>0 and foundon==0: #search backwards
                index-=1
                if inputinterpretation[index]['note#']==inputmsg[1] and not inputinterpretation[index].get('time') is None: #it must be an on event (since can't have 2 offs in a row)
                    foundon=1
            if foundon==1:
                while index<len(inputinterpretation) and foundmatch==0: #search forwards, don't need a limit because any note on in the score will have a note off eventually
                    if [inputinterpretation[index]['on_off'],inputinterpretation[index]['note#']]==[128,inputmsg[1]] and inputinterpretation[index].get('time') is None:
                        inputinterpretation[index]['vel']=inputmsg[2]
                        inputinterpretation[index]['time']=inputmsg[3]
                        latest_input_index=max(index,latest_input_index)
                        foundmatch=1
                    index+=1
        if foundmatch==0:
            unaligned_events+=[inputmsg]
        else:
            aligned_events+=[inputmsg]

    aligned_notes=[]
    unaligned_notes=[]
    for note in inputinterpretation:
        if note.get('time') is None:
            unaligned_notes+=[note]
        else:
            aligned_notes+=[note]

    print('MIDI alignment success/failure: ',len(aligned_events),len(unaligned_events))
    print('score alignment success/failure: ',len(aligned_notes),len(unaligned_notes))

    return inputinterpretation





if __name__=='__main__':
    score_file='logs/debussy1_1/outputscore.txt'
    midi_file='midi4.txt'

    with open(score_file) as f:
        score=eval(f.read())

    with open(midi_file) as f:
        midi=eval(f.read())

    #midi=[[144,83,23,1],[144,71,24,2],[144,74,25,2],[144,79,26,3]]

    with open('test.txt','w') as f:
        f.write(str(align(midi,score)))