import pyaudio
import wave
import pydub
from threading import Thread


class AudioReader:
    """
    Handles the process of recording/retrieving an audio file and convert it into the right format (.wav)
    """

    def __init__(self):
        # Constants for recording audio
        self.CHUNK = 1024  # Number of frames per buffer
        self.FORMAT = pyaudio.paInt16  # Sample format
        self.CHANNELS = 1  # Number of channels (mono)
        self.RATE = 44100  # Sampling rate

        self.output_filename = 'output.wav'  # Path to save the audio file
        self.p = pyaudio.PyAudio()  # Instantiate the PyAudio class
        self.is_recording = False  # Flag to check if recording is in progress
        self.stream = None  # Audio stream
        self.record_thread = None  # Thread for recording audio

    def record_audio(self) -> None:
        """
        Record an audio file from the user's microphone.
        Args:
            None
        Returns:
            None
        """

        self.is_recording = True
        # Opening the audio stream
        self.stream = self.p.open(format=self.FORMAT,
                                  channels=self.CHANNELS,
                                  rate=self.RATE,
                                  input=True,
                                  output=True,
                                  frames_per_buffer=self.CHUNK)
        frames = []
        while self.is_recording:
            data = self.stream.read(self.CHUNK)
            frames.append(data)

        # Calls the save_audio method to save the audio file and closes the stream.
        self.save_audio(frames)
        self.stream.stop_stream()
        self.stream.close()

    def start_recording(self) -> None:
        """
        Start recording audio.
        Args:
            None
        Returns:
            None
        """

        # Set the value of is_recording to True and start the recording in a separate thread.
        self.is_recording = True
        self.record_thread = Thread(target=self.record_audio)
        self.record_thread.start()

    def stop_recording(self) -> None:
        """
        Stop the audio recording.
        Args:
            None
        Returns:
            None
        """

        # Set the value of is_recording to False and join the recording thread.
        self.is_recording = False
        if self.record_thread is not None:
            self.record_thread.join()

    def save_audio(self, frames: list) -> None:
        """
        Save the audio to the output_filename.
        Args:
            frames (list): List of audio frames.
        Returns:
            None
        """
        wf = wave.open(self.output_filename, 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(self.p.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        print('Audio saved as', self.output_filename)

    def audio_to_wav(self, filename: str) -> None:
        """
        Convert an audio file to the .wav format.
        Args:
            filename (str): The filename of the audio file to be converted.
        Returns:
            None
        """
        sound = pydub.AudioSegment.from_file(filename)
        sound.export(self.output_filename, format='wav')

    # Getters
    def get_audio(self) -> str:
        return self.output_filename

    def get_chunk(self) -> int:
        return self.CHUNK

    def get_format(self) -> int:
        return self.FORMAT

    def get_rate(self) -> int:
        return self.RATE
