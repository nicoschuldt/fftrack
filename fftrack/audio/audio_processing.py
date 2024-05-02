import hashlib
import librosa
import logging
import matplotlib.colors as colors
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.mlab import window_hanning, specgram
from scipy.ndimage import maximum_filter, binary_erosion, generate_binary_structure, iterate_structure
from pydub import AudioSegment

# config


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

# Flags for plotting and logging
PLOT = False
LOG_LEVEL = logging.INFO
# Configure logging
logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s - %(levelname)s - %(message)s')


class AudioProcessing:
    """
    Class for processing audio files and generating fingerprints.
    """

    def __init__(self, fs=DEFAULT_FS, window_size=DEFAULT_WINDOW_SIZE, overlap_ratio=DEFAULT_OVERLAP_RATIO,
                 fan_value=DEFAULT_FAN_VALUE, amp_min=DEFAULT_AMP_MIN, peak_neighborhood_size=PEAK_NEIGHBORHOOD_SIZE,
                 fingerprint_reduction=FINGERPRINT_REDUCTION, max_hash_time_delta=MAX_HASH_TIME_DELTA,
                 min_hash_time_delta=MIN_HASH_TIME_DELTA, peak_sort=PEAK_SORT, plot=PLOT):

        self.fs = fs
        self.window_size = window_size
        self.overlap_ratio = overlap_ratio
        self.fan_value = fan_value
        self.amp_min = amp_min
        self.peak_neighborhood_size = peak_neighborhood_size
        self.fingerprint_reduction = fingerprint_reduction
        self.max_hash_time_delta = max_hash_time_delta
        self.min_hash_time_delta = min_hash_time_delta
        self.sort_peaks = peak_sort
        self.plot = plot

    def load_audio_file(self, file_path):
        """
        Load an audio file as a floating point time series.

        Args:
            file_path (str): Path to the audio file.

        Returns:
            np.ndarray: Audio samples as a 1D numpy array.
            int: Sampling rate of the audio file.
        """
        logging.info(f"Loading audio file: {file_path}")
        audio = AudioSegment.from_file(file_path)
        mono_audio = audio.set_channels(1)
        normalized_audio = mono_audio.apply_gain(-mono_audio.dBFS)
        samples = np.array(normalized_audio.get_array_of_samples(), dtype=np.float32)
        rate = mono_audio.frame_rate


        # Resample the audio to the target sample rate
        if rate != self.fs:
            logging.debug(f"Resampling audio from {rate} Hz to {self.fs} Hz.")
            samples = librosa.resample(samples, orig_sr=rate, target_sr=self.fs)
        logging.info(f"Loaded audio with {len(samples)} samples at {rate} Hz.")

        return samples, self.fs

    def generate_spectrogram(self, samples):
        """
        Generate a spectrogram from the audio samples.
        """
        logging.info("Generating Spectrogram.")

        # Generate the spectrogram using the short-time Fourier transform (STFT)
        # The window size is the number of samples in the FFT window
        # The overlap ratio is the fraction of overlap between consecutive windows
        return specgram(samples, NFFT=self.window_size, Fs=self.fs, window=window_hanning,
                        noverlap=int(self.window_size * self.overlap_ratio))[0]
    def find_peaks(self, spectrogram_2d):
        """
        Find peaks in the 2D array of the spectrogram.
        Args:
            spectrogram_2d (np.ndarray): 2D array of the spectrogram.
        Returns:
            list: List of peak indices in the format [(frequency, time), ...].
        """

        logging.info("Finding Peaks.")
        # The binary stucture defines how the neighborhood of each element should be calculated
        struct = generate_binary_structure(2, 1)  # connectivity: 1 for direct connection, 2 for diagonal
        # The neighborhood is iterated to find the maximum value in the neighborhood
        neighborhood = iterate_structure(struct, self.peak_neighborhood_size)

        # Find local maxima in the 2D array, i.e. peaks in the spectrogram
        local_max = maximum_filter(spectrogram_2d, footprint=neighborhood) == spectrogram_2d
        background = (spectrogram_2d == 0)

        # Erode the background to find the peaks, erosion means that the value of the pixel is set to 1 if all the
        # elemetns in the neighborhood are 1, otherwise it is set to 0
        # this is used to remove the background from the local maximum
        eroded_background = binary_erosion(background, structure=neighborhood, border_value=1)

        # The detected peaks are the local maxima that are not part of the eroded background
        detected_peaks = local_max != eroded_background

        amps = spectrogram_2d[detected_peaks]

        freq_indices, time_indices = np.where(detected_peaks)

        amps = amps.flatten()
        filter_idxs = np.where(amps > self.amp_min)

        freq_indices_filter = freq_indices[filter_idxs]
        time_indices_filter = time_indices[filter_idxs]

        return list(zip(freq_indices_filter, time_indices_filter))

    def generate_fingerprints_from_peaks(self, peaks):
        """
        Generate hashes from the peaks.
        Args:
            peaks (list): Peaks in the format [(frequency, time), ...].
        Returns:
            list: A list of hashes representing the audio fingerprint.
        """
        logging.info("Generating Fingerprints.")
        if self.sort_peaks:
            peaks.sort(key=lambda x: x[1])

        hashes = []
        for i in range(len(peaks)):
            for j in range(1, self.fan_value):
                if i + j < len(peaks):
                    freq1, t1 = peaks[i]
                    freq2, t2 = peaks[j + i]
                    t_delta = t2 - t1

                    if MIN_HASH_TIME_DELTA <= t_delta <= MAX_HASH_TIME_DELTA:
                        h = hashlib.sha1(f"{freq1}|{freq2}|{t_delta}".encode('utf-8'))
                        hashes.append((h.hexdigest()[0:FINGERPRINT_REDUCTION], int(t1)))

        return hashes

    @staticmethod
    def plot_peaks(peaks):
        """
        Plot the peaks on the spectrogram.
        """
        fig, ax = plt.subplots()
        ax.scatter([p[0] for p in peaks], [p[1] for p in peaks], s=1)
        ax.set_xlabel('Time')
        ax.set_ylabel('Frequency')
        ax.set_title('Peaks in Spectrogram')
        plt.show()

    def generate_fingerprints_from_samples(self, samples):
        """
        Full audio processing pipeline: generate spectrogram, find peaks, and generate hashes.

        Args:
            samples (np.ndarray): Audio samples as a 1D numpy array.

        Returns:
            list: A list of hashes representing the audio fingerprint.
        """
        spectrogram = self.generate_spectrogram(samples)

        # Convert the spectrogram to decibels to compress the range of values and make it easier to find peaks
        spectrogram = 10 * np.log10(spectrogram, out=np.zeros_like(spectrogram), where=(spectrogram != 0))
        # log spectrogram

        peaks = self.find_peaks(spectrogram)
        logging.info(f"Found {len(peaks)} peaks. Peaks: {peaks[:10]}")
        fingerprints = self.generate_fingerprints_from_peaks(peaks)
        return fingerprints


    def generate_fingerprints_from_file(self, file_path):
        """
        Full audio processing pipeline: load, generate spectrogram, find peaks, and generate hashes.

        Args:
            file_path (str): Path to the audio file.

        Returns:
            list: A list of hashes representing the audio fingerprint.
        """
        samples, rate = self.load_audio_file(file_path)
        return self.generate_fingerprints_from_samples(samples)

    def crop_samples(self, samples, start_time, end_time):
        """
        Crop audio samples to a specified time range.

        Args:
            samples (np.ndarray): Audio samples.
            start_time (float): Start time in seconds.
            end_time (float): End time in seconds.

        Returns:
            np.ndarray: Cropped audio samples.
        """
        start_index = int(start_time * self.fs)
        end_index = int(end_time * self.fs)
        return samples[start_index:end_index]


    def offset_to_seconds(self, offset):
        hop_size = DEFAULT_WINDOW_SIZE * (1 - self.overlap_ratio)
        frame_duration = hop_size / self.fs
        offset_in_seconds = offset * frame_duration
        return offset_in_seconds
