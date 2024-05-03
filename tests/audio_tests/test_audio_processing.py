import pytest
import numpy as np
import soundfile as sf
from fftrack.audio.audio_processing import AudioProcessing
import tempfile
import os

# Constants
FREQUENCY = 440  # Frequency of A4 note in Hz
DURATION = 1  # Duration of the audio clip in seconds
SAMPLE_RATE = 44100  # Sample rate in Hz


@pytest.fixture
def audio_processor():
    """Fixture for creating an instance of the AudioProcessing class."""
    return AudioProcessing(fs=SAMPLE_RATE)


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


def test_load_audio_file(audio_processor, test_audio_path):
    samples, rate = audio_processor.load_audio_file(test_audio_path)
    assert samples is not None, "Failed to load audio samples."
    assert rate == SAMPLE_RATE, "Sample rate mismatch."
    assert len(samples) == SAMPLE_RATE * DURATION, "Incorrect number of samples."


def test_generate_spectrogram(audio_processor, test_audio_path):
    samples, _ = audio_processor.load_audio_file(test_audio_path)
    spectrogram = audio_processor.generate_spectrogram(samples)
    assert spectrogram is not None, "Failed to generate spectrogram."
    assert spectrogram.shape == (2049, 20)


def test_find_peaks(audio_processor, test_audio_path):
    samples, _ = audio_processor.load_audio_file(test_audio_path)
    spectrogram = audio_processor.generate_spectrogram(samples)
    peaks = audio_processor.find_peaks(spectrogram)
    assert len(peaks) > 0, "No peaks found."
    assert peaks == [(41, 11), (123, 19), (204, 19), (286, 0), (368, 12), (450, 19), (531, 6), (613, 3), (695, 12), (776, 13), (858, 6), (940, 6), (1022, 12), (1103, 0), (1185, 6), (1267, 6), (1349, 13), (1430, 12), (1512, 6), (1594, 6)]


def test_generate_fingerprints_from_samples(audio_processor, test_audio_path):
    samples, _ = audio_processor.load_audio_file(test_audio_path)
    fingerprints = audio_processor.generate_fingerprints_from_samples(samples)
    assert len(fingerprints) > 0, "No fingerprints generated."
    assert fingerprints[:10] == [('4a6c980f20d94166ae1d', 0), ('9f7755c2590a6a29574f', 0), ('13b49f8aac3e101be40c', 0), ('af48499f16c3376c1af4', 0), ('68fa3d1b72d78368f1ba', 0), ('7d91c052ae29d4572df5', 0), ('60cf766cf8607f3f09e9', 0), ('692a41d9491ba747302f', 0), ('c011ad1c0f187defda3c', 0), ('b1341a2633b12a1841e6', 0)]


def test_crop_samples(audio_processor):
    # Generate a test signal of 3 seconds
    duration = 3  # seconds
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    waveform = np.sin(2 * np.pi * FREQUENCY * t)

    # Crop the middle second from the waveform
    start_time, end_time = 1, 2  # seconds
    cropped_samples = audio_processor.crop_samples(waveform, start_time, end_time)

    # The number of samples in the cropped segment should match the sample rate
    assert len(cropped_samples) == SAMPLE_RATE, "Cropped segment length does not match expected."


def test_offset_to_seconds(audio_processor):
    offset = 1000
    offset_seconds = audio_processor.offset_to_seconds(offset)
    assert 46.439 < offset_seconds < 46.440, "Offset to seconds conversion failed."