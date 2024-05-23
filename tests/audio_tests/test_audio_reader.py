import pytest
import numpy as np
import soundfile as sf
import tempfile
import os
import time
from fftrack.audio.audio_reader import AudioReader

# Constants
FREQUENCY = 440  # Frequency of A4 note in Hz
DURATION = 1  # Duration of the audio clip in seconds
SAMPLE_RATE = 44100  # Sample rate in Hz


@pytest.fixture
def audio_reader():
    """Fixture for creating an instance of the AudioReader class."""
    return AudioReader()


@pytest.fixture
def test_audio_path():
    """Fixture to generate a synthetic audio file and provide its file path."""
    # Generate a sine wave for the test audio
    t = np.linspace(0, DURATION, int(SAMPLE_RATE * DURATION), endpoint=False)
    waveform = np.sin(2 * np.pi * FREQUENCY * t)

    # Create a temporary file to save the test audio
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav', prefix='test_audio_')
    sf.write(temp_file.name, waveform, SAMPLE_RATE)

    # Yield the path to the test audio file for use in tests
    yield temp_file.name

    # Cleanup - delete the temporary file after use
    os.remove(temp_file.name)


def test_save_audio(audio_reader):
    """Test the save_audio method of the AudioReader class."""
    # Create dummy audio frames
    frames = [b'\x00\x00', b'\x00\x00']

    audio_reader.save_audio(frames)
    assert os.path.exists('output.wav')
    os.remove('output.wav')


def test_audio_to_wav(audio_reader, test_audio_path):
    """Test the audio_to_wav method of the AudioReader class."""
    audio_reader.audio_to_wav(test_audio_path)
    assert os.path.exists('output.wav')
    os.remove('output.wav')


# def test_audio_record(audio_reader):
#     """Test the methods used to record audio from the AudioReader class."""
#     audio_reader.start_recording()
#     assert audio_reader.is_recording is True
#     # Record audio for 5 seconds
#     time.sleep(5)
#
#     audio_reader.stop_recording()
#     assert os.path.exists('output.wav')
#     assert audio_reader.is_recording is False
#     os.remove('output.wav')
