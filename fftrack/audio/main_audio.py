# Demo for how to use the audio unit
import time

from .audio_processing import AudioProcessing
from .audio_reader import AudioReader


def main():
    # 1. Initialize the AudioReader and AudioProcessing classes
    print("Initializing audio reader and processor...")
    audio_reader = AudioReader()
    audio_processor = AudioProcessing()
    audio_processor2 = AudioProcessing()

    # 2 Get audio from the user :
    if input("Would you like to record audio from the microphone? (y/n): ") == "y":
        # 2.1 Record audio from microphone
        print("Recording audio...")
        audio_reader.start_recording()
        time.sleep(5)
        audio_reader.stop_recording()
        print("Audio recording complete.")
    else:
        # 2.2 Load an audio file
        print("Loading audio file...")
        path = input("Please provide the path to an audio file: ")
        audio_reader.audio_to_wav(path)

    # 3. Process the audio file
    print("Processing audio...")
    start_time = time.time()
    fingerprints = audio_processor.generate_fingerprints_from_file(
        audio_reader.output_filename)
    end_time = time.time()

    time1 = end_time - start_time
    print("Time taken for generate_fingerprints_from_file: ", time1, "seconds")

    print("Processing audio (multithreading).")
    start_time = time.time()
    fingerprints2 = audio_processor2.generate_fingerprints_from_file_threads(
        audio_reader.output_filename)
    end_time = time.time()

    time2 = end_time - start_time
    print("Time taken for generate_fingerprints_from_file_threads: ", time2, "seconds")

    # 4. Print the fingerprints
    print("Fingerprints audio:")
    print("generated ", len(fingerprints2), " fingerprints")
    print('Time taken: ', time1)

    print("Fingerprints audio (multithreading):")
    print("generated ", len(fingerprints2), " fingerprints")
    print('Time taken: ', time2)


if __name__ == "__main__":
    main()
