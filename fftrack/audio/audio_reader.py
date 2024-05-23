import wave
from threading import Thread

import pyaudio
import pydub

from fftrack import config as cfg

# config
config = cfg.load_config()

# Constants for recording audio
CHUNK = config["audio"]["chunk_size"]  # Number of frames per buffer
FORMAT = pyaudio.paInt16  # Sample format
CHANNELS = config["audio"]["channels"]  # Number of channels (mono)
RATE = config["audio"]["rate"]  # Sampling rate


class AudioReader:
    """
    Handles the process of recording/retrieving an audio file and convert it into the right format (.wav)
    """

    def __init__(self, chunk=CHUNK, frmt=FORMAT, channels=CHANNELS, rate=RATE):

        self.chunk = chunk  # Number of frames per buffer
        self.format = frmt  # Sample format
        self.channels = channels  # Number of channels (mono)
        self.rate = rate  # Sampling rate

        self.output_filename = 'output.wav'  # Path to save the audio file
        self.p = pyaudio.PyAudio()  # Instantiate the PyAudio class
        self.is_recording = False  # Flag to check if recording is in progress
        self.stream = None  # Audio stream
        self.record_thread = None  # Thread for recording audio

    def record_audio(self):
        """
        Record an audio file from the user's microphone.

        Returns:
            None
        """

        self.is_recording = True

        # Opening the audio stream
        self.stream = self.p.open(format=self.format,
                                  channels=self.channels,
                                  rate=self.rate,
                                  input=True,
                                  output=True,
                                  frames_per_buffer=self.chunk)

        frames = []
        while self.is_recording:
            data = self.stream.read(self.chunk)
            frames.append(data)

        # Calls the save_audio method to save the audio file and closes the stream
        self.save_audio(frames)
        self.stream.stop_stream()
        self.stream.close()

    def start_recording(self):
        """
        Start recording audio.

        Returns:
            None
        """

        # Set the value of is_recording to True and start the recording in a separate thread.
        self.is_recording = True
        self.record_thread = Thread(target=self.record_audio)
        self.record_thread.start()

    def stop_recording(self):
        """
        Stop the audio recording.

        Returns:
            None
        """

        # Set the value of is_recording to False and join the recording thread.
        self.is_recording = False
        if self.record_thread is not None:
            self.record_thread.join()

    def save_audio(self, frames):
        """
        Save the audio to the output_filename.

        Args:
            frames (list): List of audio frames.
        Returns:
            None
        """

        wf = wave.open(self.output_filename, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.p.get_sample_size(self.format))
        wf.setframerate(self.rate)
        wf.writeframes(b''.join(frames))
        wf.close()
        print('Audio saved as', self.output_filename)

    def audio_to_wav(self, filename):
        """
        Convert an audio file into .wav format.

        Args:
            filename (str): The filename of the audio file to be converted.
        Returns:
            None
        """
        sound = pydub.AudioSegment.from_file(filename)
        sound.export(self.output_filename, format='wav')
