#!/usr/bin/env python3
"""
BuildFingerprintDatabase.py

Script to fingerprint audio files from the dataset and build the fingerprint database.
Supports both MP3 and WAV files. Converts MP3 to WAV automatically.
"""

import os
import sys
import glob
import pickle
import subprocess
from pathlib import Path
from timeit import default_timer as timer

# Add the current directory to path to import local modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import AudioModule
import DBModule


def ConvertMP3ToWAV(mp3_path, wav_path):
    """Convert an MP3 file to WAV format using ffmpeg."""
    try:
        print(f"  Converting {os.path.basename(mp3_path)} to WAV...", end=" ")
        subprocess.run(
            ['ffmpeg', '-i', mp3_path, '-y', '-q:a', '9', wav_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
        print("✓")
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def EnsureWAVFile(audio_file):
    """Ensure a WAV file exists. If given an MP3, convert it."""
    if audio_file.lower().endswith('.wav'):
        return audio_file
    elif audio_file.lower().endswith('.mp3'):
        wav_path = audio_file.replace('.mp3', '.wav')
        if not os.path.exists(wav_path):
            if not ConvertMP3ToWAV(audio_file, wav_path):
                return None
        return wav_path
    else:
        print(f"⚠ Unsupported format: {audio_file}")
        return None


def FingerprintSong(audio_file, song_id, pointer=0):
    """Generate fingerprint for a song and return the pointer."""
    try:
        pointer = AudioModule.GenerateConstellationMap(audio_file, song_id, pointer)
        return pointer
    except Exception as e:
        print(f"✗ Error fingerprinting {os.path.basename(audio_file)}: {e}")
        return None


def BuildDatabase(dataset_dir, output_dir=None):
    """
    Build the fingerprint database from audio files in dataset_dir.
    
    Args:
        dataset_dir: Directory containing audio files (MP3 or WAV)
        output_dir: Directory to save fingerprint database (defaults to current dir)
    """
    if output_dir is None:
        output_dir = os.getcwd()
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all audio files
    audio_files = []
    for ext in ['*.mp3', '*.wav', '*.MP3', '*.WAV']:
        audio_files.extend(glob.glob(os.path.join(dataset_dir, ext)))
    
    if not audio_files:
        print(f"✗ No audio files found in {dataset_dir}")
        return False
    
    print(f"✓ Found {len(audio_files)} audio file(s)")
    print()
    
    # Initialize or load existing database and song mapping
    fingerprint_db_path = os.path.join(output_dir, 'fingerprintDatabase.txt')
    song_map_path = os.path.join(output_dir, 'songMap.txt')
    
    if os.path.exists(fingerprint_db_path):
        print(f"Loading existing fingerprint database from {fingerprint_db_path}")
        fingerprint_db = DBModule.LoadHashTable('fingerprintDatabase')
    else:
        print("Creating new fingerprint database")
        fingerprint_db = {}
    
    if os.path.exists(song_map_path):
        print(f"Loading existing song mapping from {song_map_path}")
        song_map = DBModule.LoadHashTable('songMap')
        next_song_id = max(int(k) for k in song_map.keys()) + 1 if song_map else 1
    else:
        print("Creating new song mapping")
        song_map = {}
        next_song_id = 1
    
    print()
    
    # Process each audio file
    start_time = timer()
    for idx, audio_file in enumerate(audio_files, 1):
        print(f"[{idx}/{len(audio_files)}] Processing: {os.path.basename(audio_file)}")
        
        # Ensure WAV format
        wav_file = EnsureWAVFile(audio_file)
        if not wav_file:
            continue
        
        # Generate fingerprint
        song_id_binary = bin(next_song_id)[2:].zfill(32)
        print(f"  Fingerprinting (Song ID: {next_song_id})...", end=" ")
        
        try:
            # Clear previous fingerprint file
            fingerprint_file = os.path.join(output_dir, "SampleFingerprint.txt")
            if os.path.exists(fingerprint_file):
                os.remove(fingerprint_file)
            
            # Generate fingerprint
            pointer = FingerprintSong(wav_file, next_song_id, 0)
            if pointer is None:
                print("✗")
                continue
            
            print("✓")
            
            # Read the generated fingerprint
            if os.path.exists(fingerprint_file):
                with open(fingerprint_file, 'r') as f:
                    fingerprint_data = f.read().strip()
                if fingerprint_data:
                    print(f"  Fingerprint generated ({len(fingerprint_data.split())} peaks)")
                    
                    # Extract addresses and couples from fingerprint
                    addresses, couples = DBModule.GenerateAddressCoupleDB(
                        fingerprint_file, song_id_binary
                    )
                    
                    # Add to database
                    DBModule.AddToFingerprintTable(addresses, couples, fingerprint_db)
                    print(f"  Added {sum(len(addr) for addr in addresses)} hash entries to database")
                else:
                    print(f"  ⚠ No fingerprint data generated")
            else:
                print(f"  ⚠ Fingerprint file not created")
            
            # Store song metadata
            song_name = os.path.splitext(os.path.basename(audio_file))[0]
            song_map[song_id_binary] = (song_name, "Unknown Artist", "Single", "Unknown")
            print(f"  Added to song map: {song_name}")
            
            next_song_id += 1
            print()
        
        except Exception as e:
            print(f"✗ Error: {e}")
            print()
            continue
    
    # Save databases
    print("-" * 60)
    print("Saving databases...")
    
    try:
        # Change to output directory for saving
        original_cwd = os.getcwd()
        os.chdir(output_dir)
        
        DBModule.SaveHashTable(fingerprint_db, 'fingerprintDatabase')
        print(f"✓ Saved fingerprint database ({len(fingerprint_db)} entries)")
        
        DBModule.SaveHashTable(song_map, 'songMap')
        print(f"✓ Saved song map ({len(song_map)} songs)")
        
        os.chdir(original_cwd)
    except Exception as e:
        print(f"✗ Error saving databases: {e}")
        return False
    
    elapsed = timer() - start_time
    print("-" * 60)
    print(f"✓ Database build complete in {elapsed:.1f} seconds")
    return True


if __name__ == '__main__':
    # Default dataset directory
    dataset_dir = '/home/atharva-parkhi/raagam/dataset'
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        dataset_dir = sys.argv[1]
    
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    else:
        output_dir = os.getcwd()
    
    print("=" * 60)
    print("Fingerprint Database Builder")
    print("=" * 60)
    print(f"Dataset directory: {dataset_dir}")
    print(f"Output directory: {output_dir}")
    print("=" * 60)
    print()
    
    if not os.path.isdir(dataset_dir):
        print(f"✗ Dataset directory not found: {dataset_dir}")
        sys.exit(1)
    
    success = BuildDatabase(dataset_dir, output_dir)
    sys.exit(0 if success else 1)
