'''
Includes code to read a finite-state-machine assocaited with a raagam
simulated it using a random see and produce a music21 stream object

Author: Madhavun Candadai
Created: Jan 2018
'''
import sys
import pickle
import subprocess
import numpy as np
import music21
from config import config

def simulate_fsm(raagam,taalam,num_avartanams=50, seed=None):
    '''
    This function simulates a raaga-specific FSM to produce a score.
    ARGS:
    raagam: string - raagam name
    taalam: string - taalam name
    num_avartanams: int - number of repetitions (default: 50)
    seed: int or None - random seed for reproducibility (if None, uses current time)

    RETURNS:
    simulated_fsm: music21.stream.Score object - a score that has 1 part and 1 Measure
    based on simulating the raaga specific FSM for a specific duration

    See config.py for simulation parameters.
    '''
    # Set random seed for variety in generation
    if seed is None:
        import time
        seed = int(time.time() * 1000) % (2**31)
    np.random.seed(seed)
    
    try:
        unotes = list(np.load(config['RAAGAM_BASEPATH']+raagam.lower()+'/metadata.npy'))
    except:
        raise Exception("Raagam metadata (Aarohanam and Avarohanam) is not available")

    # read generic fsm for the raagam
    try:
        fsm = np.load(config['RAAGAM_BASEPATH']+'/'+raagam+'/'+raagam+'_fsm.npy')
    except:
        raise Exception('Generic FSM does not exist for this raagam...')

    # read taalam pickle
    try:
        taalam_dict = pickle.load(open(config['TAALAM_BASEPATH']+'taalam.pkl','rb'))
    except:
        raise Exception('Taalam pickle file does not exist')

    # read taalam beat count from pickle
    try:
        taalam_count = taalam_dict[taalam.lower()]
    except:
        raise Exception('Taalam pickle does not contain this taalam. Add it to taalam.py and re-create pickle')

    note_space_duration = 0.75

    # create a part and assign instrument
    part = music21.stream.Part(id='piano')
    part.append(music21.instrument.Piano())

    prev_swaram_ind = int((len(unotes)-1)/3) # To start from Sa
    prev_note = music21.note.Note(unotes[prev_swaram_ind])
    # create a list of notes that will be added to the stream
    for avartanam_num in range(num_avartanams):
        notes_list = []
        # notes_list.append(prev_note)
        for taalam_num in range(taalam_count):
            # create a new index for what comes next based on fsm
            swaram_ind = np.random.choice(np.arange(len(unotes)),p=fsm[prev_swaram_ind,:])
            #print(avartanam_num,taalam_num,unotes[prev_swaram_ind],unotes[swaram_ind])

            # no gamakam
            if unotes[swaram_ind] == ',' and taalam_num==0:
                print("no ',' at the beginning of an avartanam")
                while unotes[swaram_ind] == ',':
                    swaram_ind = np.random.choice(np.arange(len(unotes)),p=fsm[prev_swaram_ind,:])
                #print("New swaram = "+unotes[swaram_ind])

            # extend note duration if current index denotes a ','
            if unotes[swaram_ind] == ',':
                notes_list[-1].duration.quarterLength += note_space_duration
            else:
                # create a note object for one quarterLength - assuming aadi taalam, I guess
                this_note = music21.note.Note(unotes[swaram_ind])
                this_note.duration.quarterLength = note_space_duration
                # add it to the list
                notes_list.append(this_note)

                # update note and swaram index for next iteration
                prev_swaram_ind = swaram_ind
                prev_note = this_note

        # create measure and add the notes in
        measure = music21.stream.Measure(number=1)
        for note in notes_list:
            measure.append(note)

        # add measure to part
        part.append(measure)

    # create an empty score
    simulated_fsm = music21.stream.Score()

    # add the part to it
    simulated_fsm.append(part)
    # Save MIDI file
    midi_file = 'simulated_'+raagam+'.midi'
    simulated_fsm.write('midi', fp=midi_file)
    print(f"Generated MIDI file: {midi_file}")
    
    # Convert MIDI to WAV using timidity
    wav_file = 'simulated_'+raagam+'.wav'
    try:
        subprocess.run(['timidity', midi_file, '-Ow', '-o', wav_file], 
                      check=True, capture_output=True)
        print(f"Generated audio file: {wav_file}")
    except FileNotFoundError:
        print("timidity not found. Install it with: sudo apt-get install timidity")
    except subprocess.CalledProcessError as e:
        print(f"Error converting MIDI to audio: {e}")

    return simulated_fsm


def simulate_fsm_with_gamakam(raagam,taalam):
    '''
    This function simulates a raaga-specific FSM to produce a score.
    Importantly, it adds gamakas to the music
    ARGS:
    raagam: string - raagam name

    RETURNS:
    simulated_fsm: music21.stream.Score object - a score that has 1 part and 1 Measure
    based on simulating the raaga specific FSM for a specific duration

    See config.py for simulation parameters.
    '''
    try:
        unotes = list(np.load(config['RAAGAM_BASEPATH']+raagam.lower()+'/metadata.npy'))
    except:
        raise Exception("Raagam metadata (Aarohanam and Avarohanam) is not available")

    # read generic fsm for the raagam
    try:
        fsm = np.load(config['RAAGAM_BASEPATH']+'/'+raagam+'/'+raagam+'_fsm.npy')
    except:
        raise Exception('Generic FSM does not exist for this raagam...')

    # read taalam pickle
    try:
        taalam_dict = pickle.load(open(config['TAALAM_BASEPATH']+'taalam.pkl','rb'))
    except:
        raise Exception('Taalam pickle file does not exist')

    # read taalam beat count from pickle
    try:
        taalam_count = taalam_dict[taalam.lower()]
    except:
        raise Exception('Taalam pickle does not contain this taalam. Add it to taalam.py and re-create pickle')

    note_space_duration = 0.75
    gamakam_density = 4

    # create a part and assign instrument
    part = music21.stream.Part(id='piano')
    part.append(music21.instrument.Piano())

    prev_swaram_ind = int((len(unotes)-1)/3) # To start from Sa
    prev_note = music21.note.Note(unotes[prev_swaram_ind])
    # create a list of notes that will be added to the stream
    for avartanam_num in range(20):#int(config['NUM_AVARTANAMS_SIM'])):
        notes_list = []
        #notes_list.append(prev_note)
        for taalam_num in range(taalam_count):

            # create a new index for what comes next based on fsm
            swaram_ind = np.random.choice(np.arange(len(unotes)),p=fsm[prev_swaram_ind,:])
            print(avartanam_num,taalam_num,unotes[prev_swaram_ind],unotes[swaram_ind])

            # insert gamakam
            if np.random.rand() < 0. and taalam_num != 0:
                # shorten previous note duration because in comes the gamakaa
                notes_list[-1].duration.quarterLength = note_space_duration/gamakam_density

                # insert new notes
                for _ in np.arange(note_space_duration/gamakam_density,note_space_duration,note_space_duration/gamakam_density):
                    if unotes[swaram_ind] == ',':
                        notes_list[-1].duration.quarterLength += note_space_duration/gamakam_density
                    else:
                        # insert a note with duration gamakam_density
                        this_note = music21.note.Note(unotes[swaram_ind])
                        this_note.duration.quarterLength = note_space_duration/gamakam_density
                        notes_list.append(this_note)

                        # update previous swaram to fill in next notein gamakam
                        prev_swaram_ind = swaram_ind
                        prev_note = this_note

                        # get index for next note in gamakam
                        #swaram_ind = np.random.choice(np.arange(len(unotes)),p=fsm[prev_swaram_ind,:])
                        if np.random.rand() < 0.5:
                            swaram_ind += 1
                        else:
                            swaram_ind -= 1

                        if swaram_ind > len(unotes): swaram_ind -= 2
                        if swaram_ind < 0: swaram_ind += 2
            else:
                # no gamakam
                if unotes[swaram_ind] == ',' and taalam_num==0:
                    print("no ',' at the beginning of an avartanam")
                    while unotes[swaram_ind] == ',':
                        swaram_ind = np.random.choice(np.arange(len(unotes)),p=fsm[prev_swaram_ind,:])
                    print("New swaram = "+unotes[swaram_ind])


            # extend note duration if current index denotes a ','
            if unotes[swaram_ind] == ',':
                notes_list[-1].duration.quarterLength += note_space_duration
            else:
                # create a note object for one quarterLength - assuming aadi taalam, I guess
                this_note = music21.note.Note(unotes[swaram_ind])
                this_note.duration.quarterLength = note_space_duration
                # add it to the list
                notes_list.append(this_note)

                # update note and swaram index for next iteration
                prev_swaram_ind = swaram_ind
                prev_note = this_note


        # create measure and add the notes in
        measure = music21.stream.Measure(number=1)
        for note in notes_list:
            measure.append(note)

        # add measure to part
        part.append(measure)

    # create an empty score
    simulated_fsm = music21.stream.Score()

    # add the part to it
    simulated_fsm.append(part)
    simulated_fsm.show('midi')
    simulated_fsm.show()
    return simulated_fsm



if __name__ == "__main__":
    assert len(sys.argv) == 3, "Requires raagam and taalam name to process"
    s = simulate_fsm(sys.argv[1],sys.argv[2])
