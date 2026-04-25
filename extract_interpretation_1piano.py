import json
piece = "faure"
def write_interpretation(performance,interpretation):
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
            for note in interpretation:
                if note[1]==144 and note[3]>=inputscorepositions[lastinputscorepositionIndex]-0.01 and note[3]<=inputscorepositions[lastinputscorepositionIndex+1]+1.01: #search between latest events' beat and next events' beat + 0.5
                    if (note[2]==msg[1] or (not piece=="g" and note[0]<9 and (note[2]-msg[1])%12==0)) and note[4:]==[0,0]: #i.e. if it's the right note and hasn't been played yet
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
                            # if not offnote[4:]==[0,0]:
                                # print('already got this noteoff')
                            offnote[4]=msg[3]
                            offnote[5]=msg[2]
                            foundmatch=1
                            #print(str(time.time_ns())+'received '+str(msg)+' matched to '+str(offnote))
                            break
                    break



        if foundmatch==0: #i.e. didn't find a match
            # print('could not match '+str(msg))
            unmatchednotes+=1

    return interpretation

# Read two output scores
with open(r'logs/faure1_1/outputscore.txt') as f:
    score_0 = eval(f.read())
with open(r'logs/faure1_2/outputscore.txt') as f:
    score_1 = eval(f.read())

# Create a temporary list with tags and old indices
combined_temp = []
for note in score_0:
    combined_temp.append({"note_data": note, "tag": 0, "old_index": note[0]})
for note in score_1:
    combined_temp.append({"note_data": note, "tag": 1, "old_index": note[0]})

# Sort by position (index 3)
combined_temp.sort(key=lambda x: x["note_data"][3])

# Assign new continuous indices and create a mapping dictionary
combined_score = []
mapping = {}

for new_idx, item in enumerate(combined_temp):
    old_note = item["note_data"]
    # Create a new standard format [new_index, on/off, note, position]
    new_note = [new_idx, old_note[1], old_note[2], old_note[3]]
    combined_score.append(new_note)
    
    # Record this new_idx's background
    mapping[new_idx] = {"tag": item["tag"], "old_index": item["old_index"]}

# (Optional) Output the combined score to combine_outputscore.txt
with open("combine_outputscore.txt", "w") as f:
    f.write(str(combined_score))

# Add [0,0] to feed into the logic
combined_interpretation = [event + [0, 0] for event in combined_score]

# Read the recording file (e.g., Take 1)
with open(r'data_management2026/202412 Experiments/20241218/inputmslog_Take_4_Human_1.txt') as f:
    performance = eval(f.read())
    # Here you need to filter out inputperformance or the track you want to align

# ==========================================
# Call the logic directly (no modifications)
# ==========================================
matched_interpretation = write_interpretation(performance, combined_interpretation)

# ==========================================
# Split back into two files and restore indices, keeping time and velocity
# ==========================================
result_interpretation_0 = []
result_interpretation_1 = []

for note in matched_interpretation:
    new_idx = note[0]
    tag = mapping[new_idx]["tag"]
    old_idx = mapping[new_idx]["old_index"]
    
    # Here the note[4] is the aligned time, note[5] is the aligned velocity
    # Restore into the standard interpretation format of length 6
    restored_note = [old_idx, note[1], note[2], note[3], note[4], note[5]]
    
    if tag == 0:
        result_interpretation_0.append(restored_note)
    else:
        result_interpretation_1.append(restored_note)

# Sort back to the original order using the old index
result_interpretation_0.sort(key=lambda x: x[0])
result_interpretation_1.sort(key=lambda x: x[0])
# ==========================================
# Output the final split results (save as interpretation format files)
# ==========================================

# Output the first interpretation
with open(r"data_management2026/202412 Experiments/20241218/inputinterpretation_Take_4_Human_1.txt", "w") as f:
    f.write(str(result_interpretation_0))

# Output the second interpretation
with open(r"data_management2026/202412 Experiments/20241218/inputinterpretation_Take_4_Human_2.txt", "w") as f:
    f.write(str(result_interpretation_1))