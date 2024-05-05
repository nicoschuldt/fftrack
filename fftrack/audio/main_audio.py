# Demo for how to use the audio unit
from audio_reader import AudioReader
from audio_processing import AudioProcessing
import time


def main():
    # 1. Initialize the AudioReader and AudioProcessing classes
    print("Initializing audio reader and processor...")
    audio_reader = AudioReader()
    audio_processor = AudioProcessing()


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
    fingerprints = audio_processor.generate_fingerprints_from_file(audio_reader.output_filename)


    # 4. Print the fingerprints
    print("Fingerprints:")
    print(fingerprints)


if __name__ == "__main__":
    main()
