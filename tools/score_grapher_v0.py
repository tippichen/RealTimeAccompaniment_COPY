from __future__ import print_function
import numpy as np


import matplotlib.pyplot as plt

def graph(score,savefile):
    try:
        lastnotetiming=score[-1][3]
    except:
        lastnotetiming=0
        print('score is empty')
        
    interpretation=0
    if len(score[0])==6:
        interpretation=1
        alltimes=[]
        for event in score:
            if not event[4]==0:
                alltimes+=[event[4]]  
        starttime=np.min(alltimes)
#        print(starttime)
#        exit()

    if savefile[0:1]=='-i':
        interpretation=0
        savefile=savefile[2:]

    #plotting
    plt.figure(figsize=(2*lastnotetiming,15))

    on_x=[]
    on_y=[]
    off_x=[]
    off_y=[]
    annotate_txt=[]
    annotate_int=[]
    annotate_x=[]
    annotate_y=[]
    #make endpoints of each note
    for index,event in enumerate(score):
        if event[1]==144:
            on_x+=[event[3]]
            on_y+=[event[2]]
            annotate_txt+=[event[0]]
            if interpretation==1:
                if event[4:]==[0,0]:
                    annotate_int+=['']
                else:
                    annotate_int+=[str(event[4]-starttime)[:4]+','+str(event[5])]
            annotate_x+=[event[3]]
            annotate_y+=[event[2]]
        if event[1]==128:
            off_x+=[event[3]]
            off_y+=[event[2]]
            annotate_txt+=[event[0]]
            if interpretation==1:
                if event[4:]==[0,0]:
                    annotate_int+=['']
                else:
                    annotate_int+=[str(event[4]-starttime)[:4]+','+str(event[5])]
            annotate_x+=[event[3]]
            annotate_y+=[event[2]]
            found=0
            searchlist=reversed(score[0:index])#search backwards for the last noteon event, assuming that the score is in the correct order
            for a in searchlist: 
                if a[2]==event[2] and a[3]<event[3]:
                    if a[1]==144: #if it's not, that means it finds a noteoff event first, i.e. the note had 0 duration. we hope this never happens.
                        plt.plot([a[3], event[3]],[event[2],a[2]],'m-')
                    found=1
                    break
                        
    plt.plot(on_x, on_y,'o')
    plt.plot(off_x, off_y,'*')
    plt.xticks(np.arange(0, lastnotetiming+2))
    xmin, xmax, ymin, ymax = plt.axis()
    plt.yticks(np.arange(int(ymin), int(ymax)))
    for t in range(0,int(lastnotetiming)+2):
        plt.axvline(x=t)
    for i,txt in enumerate(annotate_txt):
        plt.annotate(txt,(annotate_x[i],annotate_y[i]+0.25)) #label each event with its number
    if interpretation==1:
        for i,txt in enumerate(annotate_int):
            plt.annotate(txt,(annotate_x[i],annotate_y[i]-0.25)) #label each event with its number
    if savefile=='show':
        plt.show()
    else:
        plt.savefig(savefile)

    return False

if __name__ == "__main__":
#    quantize_per_beat=int(input("quantize per beat\n"))
    score=eval(input("score\n"))
    savefile=input("file\n")
    graph(score,savefile)