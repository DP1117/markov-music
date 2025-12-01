import mido
import numpy as np
import glob
import os

# get array of notes from midi file
def midi_to_array(midi_file_path):
    try:
        mid = mido.MidiFile(midi_file_path)
    except Exception as e:
        print(f"Error reading MIDI file {midi_file_path}: {e}")
        return []
    notes = []
    for track in mid.tracks:            
        for note in track:
            if note.type == 'note_on' and note.velocity > 0:
                # compress to one octave
                compress_note = note.note % 12
                notes.append(compress_note)
    return notes

# takes an array of notes and generates a 12x12 markov matrix
# representing the different note combinations (e.g C,C or D,E)
def generate_markov_matrix(notes):
    matrix = np.zeros((12, 12))
    # adds note
    for i in range(len(notes) - 1):
        curr = notes[i]
        next = notes[i+1]
        matrix[curr, next] += 1
    # Laplace smoothing (add-one smoothing)
    matrix += 1
    # normalize
    row_sums = matrix.sum(axis=1, keepdims=True)
    prob_matrix = matrix / row_sums
    return prob_matrix

# generates music (array of notes) based off markov-matrix
def generate_music(matrix, start_note, length=50):
    # if start_note isn't given or is some nonsense start at 0
    if start_note < 0 or start_note > 11:
        start_note = 0
    current_note = start_note
    melody = [current_note]
    all_notes = np.arange(12)
    for i in range(length):
        # get all probabilities of the next note based on current note
        probabilities = matrix[current_note]
        # choose the next note randomly based on probabilities
        next_note = np.random.choice(all_notes, p=probabilities)
        melody.append(next_note)
        current_note = next_note
    return melody

# creates a MIDI file from the notes
def save_midi_file(note_list, output_file_path, base_octave=5, velocity=100, note_duration_ticks=480):
    midi_note_offset = base_octave * 12
    
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)
    
    track.append(mido.MetaMessage('set_tempo', tempo=500000)) # 500000 is 120 BPM
    track.append(mido.Message('program_change', program=0, time=0)) # Program 0 is Piano

    for i, relative_note in enumerate(note_list):
        absolute_note = relative_note + midi_note_offset
        track.append(mido.Message(
            'note_on', 
            note=absolute_note, 
            velocity=velocity, 
            time=0 if i == 0 else note_duration_ticks
        ))
        track.append(mido.Message(
            'note_off', 
            note=absolute_note, 
            velocity=velocity, 
            time=note_duration_ticks
        ))
    try:
        mid.save(output_file_path)
        print(f"Generated music to {output_file_path}")
    except Exception as e:
        print(f"Error saving MIDI file: {e}")

# runs the entire generation process
def run(midi_directory, output_midi):    
    # gets all midi files in the directory
    all_midi_files = glob.glob(os.path.join(midi_directory, "*.mid"))

    # gets all notes from all the midi files
    all_notes = []
    for midi_file in all_midi_files:
        note_sequence = midi_to_array(midi_file)
        all_notes.extend(note_sequence)
        
    # generate markov matrix from all notes
    markov_matrix = generate_markov_matrix(all_notes)
    
    # generate the melody (array of notes)
    new_melody = generate_music(markov_matrix, start_note=0, length=100)
    
    # generate a midi file that can be played from on the melody
    save_midi_file(
        note_list=new_melody,
        output_file_path=output_midi,
        base_octave=4,
        note_duration_ticks=240
    )

    print(f"Successfully generated MIDI file")

composer = "beethoven"
midi_directory = "midi_files/" + composer
output_file = "markov_midi_files/" + composer + "_generated.mid"

if __name__ == "__main__":
    run(composer, midi_directory, output_file)