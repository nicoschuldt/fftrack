import argparse
import hashlib
import logging
from collections import defaultdict, Counter

import librosa
import matplotlib.colors as colors
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.mlab import window_hanning, specgram
from pydub import AudioSegment
from scipy.ndimage import maximum_filter, binary_erosion, generate_binary_structure, iterate_structure

from fftrack.audio.audio_processing import AudioProcessing
from fftrack.database.db_manager import DatabaseManager
from fftrack.database.models import create_database

# Constants for fingerprinting
DEFAULT_FS = 44100  # Sampling rate
DEFAULT_WINDOW_SIZE = 4096  # Size of the FFT window
DEFAULT_OVERLAP_RATIO = 0.5  # Overlap ratio for FFT
DEFAULT_FAN_VALUE = 15  # Degree for pairing peaks in fingerprinting
DEFAULT_AMP_MIN = 10  # Minimum amplitude in spectrogram for considering a peak
PEAK_NEIGHBORHOOD_SIZE = 20  # Size of the neighborhood around a peak
FINGERPRINT_REDUCTION = 20  # Reduction in fingerprint to trim hash value size
MAX_HASH_TIME_DELTA = 200  # Max time delta between peaks in a hash
MIN_HASH_TIME_DELTA = 0  # Min time delta between peaks in a hash
PEAK_SORT = True  # Whether to sort peaks for hashing

# Constants for matching
CONFIDENCE_THRESHOLD = 0.5  # Confidence threshold for a match

# Flags for plotting and logging
PLOT = False
LOG_INFO = True

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def find_matches(sample_hashes, plot=False):
    results, hashes_no_dupl = [], defaultdict(int)

    for sample_hash, offset in sample_hashes:
        matching_fingerprints = dbm.get_fingerprint_by_hash(sample_hash)
        for song_id, db_offset in matching_fingerprints:
            # Ensure both offsets are integers
            db_offset = int(db_offset)
            offset = int(offset)  # This should already be an integer, but just to be safe

            offset_difference = db_offset - offset
            results.append((song_id, offset_difference))
            hashes_no_dupl[song_id] += 1

    return results, hashes_no_dupl



def align_matches(matches):
    """
    Aligns matches to find the most probable song match.

    Params:
        matches (list): List of matches in the format [(song_id, offset_difference), ...].

    Returns:
        dict: A dictionary of aligned match results for each song.
    """
    ap = AudioProcessing()
    logging.info(f"Aligning {len(matches)} matches.") if LOG_INFO else None

    offset_by_song = defaultdict(list)

    # Group offset differences by song
    for sid, offset_difference in matches:
        offset_by_song[sid].append(offset_difference)

    # Analyze offset differences to find the best match
    aligned_results = {}
    for sid, offsets in offset_by_song.items():
        # Find the most common offset and its count
        offset_counts = Counter(offsets)
        most_common_offset, count = offset_counts.most_common(1)[0]

        aligned_results[sid] = {
            "song_id": sid,
            "offset": most_common_offset,
            "count": count,
            "confidence": count / len(offsets)
        }
        logging.info(f"Song ID: {sid}, "
                     f"Most Common Offset: {most_common_offset} ({ap.offset_to_seconds(most_common_offset)}s, "
                     f"Matches: {count}, "
                     f"Confidence: {count / len(offsets):.2f}") if LOG_INFO else None

    if PLOT:
        # Plot the distribution of offset differences for each song
        plt.figure(figsize=(15, 7))
        for sid, offsets in offset_by_song.items():
            plt.hist(offsets, bins=50, alpha=0.5, label=sid)
        plt.title('Distribution of Offset Differences')
        plt.xlabel('Offset Difference')
        plt.ylabel('Count')
        plt.legend()
        plt.show()

    return aligned_results


def find_best_match(aligned_results):
    """
    Finds the best match from aligned results based on the highest count (confidence).

    :param aligned_results: A dictionary of aligned match results for each song.
    :return: A tuple of the best matching song ID and its match details.
    """
    best_match = max(aligned_results.items(), key=lambda x: x[1]["count"])
    return best_match

def parse_arguments():
    """Parse command line arguments for song file paths."""
    parser = argparse.ArgumentParser(description='Compare two songs and determine if they are the same.')
    parser.add_argument('song1', type=str, help='Path to the first song file.')
    parser.add_argument('song2', type=str, help='Path to the second song file.')
    return parser.parse_args()


def main():
    audio_processor = AudioProcessing(plot=False)
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Parse arguments
    args = parse_arguments()

    # Load and process the first song
    logging.info(f"Loading and processing {args.song1}")
    samples1, rate1 = audio_processor.load_audio_file(args.song1)

    fingerprints1 = set(fingerprint(samples1))

    # Load and process the second song
    logging.info(f"Loading and processing {args.song2}")
    samples2, rate2 = audio_processor.load_audio_file(args.song2)
    fingerprints2 = fingerprint(samples2)

    # Simulate adding the fingerprints of the first song to the database
    db_fingerprints = {"song1": fingerprints1}

    # Find matches between the second song and the database
    matches, hashes_no_dupl = find_matches(fingerprints2, db_fingerprints, plot=PLOT)

    # Align matches and find the best match
    aligned_results = align_matches(matches)
    best_match_sid, best_match_details = find_best_match(aligned_results)

    # Determine if the songs are the same based on the best match
    song_match = "same" if best_match_details['confidence'] > CONFIDENCE_THRESHOLD else "different"

    # Print the conclusion and relevant data
    logging.info(f"The songs are {song_match}.")
    logging.info(f"Song ID: {best_match_sid}")
    logging.info(f"Offset in s: {audio_processor.offset_to_seconds(best_match_details['offset'])}")
    logging.info(f"Confidence: {best_match_details['confidence']:.2f}")


# if __name__ == "__main__":
#     main()

# Example usage with an audio file
if __name__ == "__main__":

    audio_processor = AudioProcessing(plot=False)  # Enable plotting for demonstration


    # initialize database
    create_database()

    dbm = DatabaseManager()

    print("Adding a new song...")
    song_id_studio = dbm.add_song("Crazy Little Thing Called Love - Studio", "Queen",
                                  "A Night at the Opera", "1975-10-31")
    print(f"Added song with ID: {song_id_studio}")

    song_id_live = dbm.add_song("Crazy Little Thing Called Love - Live", "Queen",
                                "A Night at the Opera", "1975-10-31")
    print(f"Added song with ID: {song_id_live}")

    file_path1 = "/Users/nicolas/Developer/workspace/Uni/L2/S4/Projet/SONGS/crazy-little-thing.mp3"
    file_path2 = "/Users/nicolas/Developer/workspace/Uni/L2/S4/Projet/SONGS/crazy-little-thing-LIVE.mp3"
    file_path3 = "/Users/nicolas/Developer/workspace/Uni/L2/S4/Projet/SONGS/crazy-little-thing-cropped.mp3"
    # # # Load audio
    samples1, rate1 = audio_processor.load_audio_file(file_path1)
    print(f"Samples shape: {samples1.shape}, type: {type(samples1)}")

    samples2, rate2 = audio_processor.load_audio_file(file_path2)
    #
    # # crop to 0:60s for testing
    samples1 = audio_processor.crop_samples(samples1, 0, 10)

    samples2 = audio_processor.crop_samples(samples2, 0, 10)
    #
    # # crop to 5:10s
    samples3 = audio_processor.crop_samples(samples1, 3, 6)

    # fingerprints1 = fingerprint(samples1)
    # fingerprints2 = fingerprint(samples2)
    # fingerprints3 = fingerprint(samples3)

    # Generate fingerprints
    fingerprints1 = audio_processor.generate_fingerprints_from_samples(samples1)
    fingerprints2 = audio_processor.generate_fingerprints_from_samples(samples2)
    fingerprints3 = audio_processor.generate_fingerprints_from_samples(samples3)


    if PLOT:
        plt.figure(figsize=(15, 7))
        plt.bar(["Studio", "Cropped", "Live"], [len(fingerprints1), len(fingerprints3), len(fingerprints2)])
        plt.title('Number of Fingerprints')
        plt.xlabel('Sample')
        plt.ylabel('Number of Fingerprints')
        plt.show()

    # add fingerprints to database
    for fingerprint in fingerprints1:
        dbm.add_fingerprint(song_id_studio, fingerprint[0], fingerprint[1])

    for fingerprint in fingerprints2:
        dbm.add_fingerprint(song_id_live, fingerprint[0], fingerprint[1])

    # Find matches
    matches, hashes_no_dupl = find_matches(fingerprints3, plot=PLOT)

    # determine song with most matches, and also the offset
    aligned_results = align_matches(matches)
    best_match_sid, best_match_details = find_best_match(aligned_results)

    # Print results
    match_found = best_match_details["confidence"] > CONFIDENCE_THRESHOLD
    if match_found:
        print(f"Match found!: {best_match_sid}")
        print(f"Offset: {best_match_details['offset']} ({audio_processor.offset_to_seconds(best_match_details['offset'])}s)")
        print(f"Confidence: {best_match_details['confidence']:.2f}")
    else:
        print("No match found.")
