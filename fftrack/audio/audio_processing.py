import hashlib
import logging
from concurrent.futures import ThreadPoolExecutor

import librosa
import matplotlib.pyplot as plt
from matplotlib import colors
import numpy as np
from matplotlib.mlab import window_hanning, specgram
from pydub import AudioSegment
from scipy.ndimage import maximum_filter, binary_erosion, generate_binary_structure, iterate_structure

from fftrack import config as cfg

# config
config = cfg.load_config()

# Constants for fingerprinting
DEFAULT_FS = config["audio"]["rate"]  # Sampling rate
DEFAULT_WINDOW_SIZE = config["audio"]["window_size"]  # Size of the FFT window
# Overlap ratio for FFT
DEFAULT_OVERLAP_RATIO = config["audio"]["overlap_ratio"]
# Degree for pairing peaks in fingerprinting (number of peaks to pair)
DEFAULT_FAN_VALUE = config["audio"]["fan_value"]
# Minimum amplitude in spectrogram for considering a peak (in dB)
DEFAULT_AMP_MIN = config["audio"]["amp_min"]
# Size of the neighborhood around a peak for peak finding
PEAK_NEIGHBORHOOD_SIZE = config["audio"]["peak_neighborhood_size"]
# Reduction in fingerprint to trim hash value size
FINGERPRINT_REDUCTION = config["audio"]["fingerprint_reduction"]
# Max time delta between peaks in a hash (in number of frames)
MAX_HASH_TIME_DELTA = config["audio"]["max_hash_time_delta"]
# Min time delta between peaks in a hash (in number of frames)
MIN_HASH_TIME_DELTA = config["audio"]["min_hash_time_delta"]
PEAK_SORT = config["audio"]["peak_sort"]  # Whether to sort peaks for hashing

NB_THREADS = config["nb_threads"]  # Number of threads for parallel processing

# Flags for plotting and logging
PLOT = config["log_level"]
LOG_LEVEL = config["log_level"]
# Configure logging
logging.basicConfig(
    level=LOG_LEVEL, format='%(asctime)s - %(levelname)s - %(message)s')


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
            samples (np.ndarray): Audio samples as a 1D numpy array.
            fs (int): Sampling rate of the audio file.
        """

        logging.info(f"Loading audio file: {file_path}")
        audio = AudioSegment.from_file(file_path)
        mono_audio = audio.set_channels(1)
        normalized_audio = mono_audio.apply_gain(-mono_audio.dBFS)
        samples = np.array(
            normalized_audio.get_array_of_samples(), dtype=np.float32)
        rate = mono_audio.frame_rate

        # Resample the audio to the target sample rate
        if rate != self.fs:
            logging.debug(f"Resampling audio from {rate} Hz to {self.fs} Hz.")
            samples = librosa.resample(
                samples, orig_sr=rate, target_sr=self.fs)
        logging.info(f"Loaded audio with {len(samples)} samples at {rate} Hz.")

        return samples, self.fs

    def generate_spectrogram(self, samples):
        """
        Generate a spectrogram from the audio samples.

        Args:
            samples (np.ndarray): Audio samples as a 1D numpy array.
        Returns: the spectrogram.
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

        # The binary structure defines how the neighborhood of each element should be calculated
        # connectivity: 1 for direct connection, 2 for diagonal
        struct = generate_binary_structure(2, 1)
        # The neighborhood is iterated to find the maximum value in the neighborhood
        neighborhood = iterate_structure(struct, self.peak_neighborhood_size)

        # Find local maxima in the 2D array, i.e. peaks in the spectrogram
        local_max = maximum_filter(
            spectrogram_2d, footprint=neighborhood) == spectrogram_2d
        background = (spectrogram_2d == 0)

        # Erode the background to find the peaks, erosion means that the value of the pixel is set to 1 if all the
        # elements in the neighborhood are 1, otherwise it is set to 0
        # this is used to remove the background from the local maximum
        eroded_background = binary_erosion(
            background, structure=neighborhood, border_value=1)

        # The detected peaks are the local maxima that are not part of the eroded background
        detected_peaks = local_max != eroded_background

        amps = spectrogram_2d[detected_peaks]

        freq_indices, time_indices = np.where(detected_peaks)

        amps = amps.flatten()
        filter_idxs = np.where(amps > self.amp_min)

        freq_indices_filter = freq_indices[filter_idxs]
        time_indices_filter = time_indices[filter_idxs]

        if self.plot:
            self.plot_peaks(spectrogram_2d, freq_indices_filter, time_indices_filter)

        return list(zip(freq_indices_filter, time_indices_filter))

    def find_peaks_threads(self, spectrogram_2d):
        """
        Find peaks in the 2D array of the spectrogram.

        Args:
            spectrogram_2d (np.ndarray): 2D array of the spectrogram.
        Returns:
            list: List of peak indices in the format [(frequency, time), ...].
        """

        logging.info("Finding Peaks.")

        # The binary structure defines how the neighborhood of each element should be calculated
        # connectivity: 1 for direct connection, 2 for diagonal
        struct = generate_binary_structure(2, 1)
        neighborhood = iterate_structure(struct, self.peak_neighborhood_size)

        def process_subarray(subarray, offset):
            # Find local maxima in the subarray
            local_max = maximum_filter(
                subarray, footprint=neighborhood) == subarray
            background = (subarray == 0)
            eroded_background = binary_erosion(
                background, structure=neighborhood, border_value=1)
            detected_peaks = local_max != eroded_background

            amps = subarray[detected_peaks]
            freq_indices, time_indices = np.where(detected_peaks)

            # Adjust time indices based on the offset
            time_indices += offset

            amps = amps.flatten()  # flatten the array (convert to 1D)
            # find the indices where the amplitude is above the threshold
            filter_idxs = np.where(amps > self.amp_min)

            # filter the frequency indices
            freq_indices_filter = freq_indices[filter_idxs]
            # filter the time indices
            time_indices_filter = time_indices[filter_idxs]

            return list(zip(freq_indices_filter,
                            time_indices_filter))  # return the list of peaks (zip creates a list of tuples)

        # Divide spectrogram into subarrays along the time axis
        num_chunks = NB_THREADS
        # divide the time axis into chunks,
        chunk_size = spectrogram_2d.shape[1] // num_chunks
        # note that spectrogram_2d.shape[1] is the number of time frames (columns)
        subarrays = [(spectrogram_2d[:, i:i + chunk_size], i)
                     for i in range(0, spectrogram_2d.shape[1], chunk_size)]
        # the subarrays are tuples of the subarray and the offset

        # Process subarrays in parallel
        with ThreadPoolExecutor() as executor:
            results = executor.map(
                lambda args: process_subarray(*args), subarrays)
            # here we use a lambda function to unpack the arguments from the tuple,
            # and then call the process_subarray function in parallel

        # Flatten the list of results, this means that we concatenate the lists of peaks from each subarray
        peaks = [peak for result in results for peak in result]


        return peaks

    def generate_fingerprints_from_peaks(self, peaks):
        """
        Generate hashes from the peaks.

        Args:
            peaks (list): Peaks in the format [(frequency, time), ...].
        Returns:
            hashes (list): A list of hashes representing the audio fingerprint.
        """

        logging.info("Generating Fingerprints.")

        if self.sort_peaks:
            peaks.sort(key=lambda x: x[1])

        hashes = []

        # Here we generate the hashes by pairing peaks that are close in time
        # This means that each fingerprint is the hash of the frequency of two peaks and the time difference between them
        for i in range(len(peaks)):
            for j in range(1, self.fan_value):
                if i + j < len(peaks):
                    freq1, t1 = peaks[i]
                    freq2, t2 = peaks[j + i]
                    t_delta = t2 - t1

                    if self.min_hash_time_delta <= t_delta <= self.max_hash_time_delta:
                        h = hashlib.sha1(
                            f"{freq1}|{freq2}|{t_delta}".encode('utf-8'))
                        hashes.append(
                            (h.hexdigest()[0:self.fingerprint_reduction], int(t1)))

        return hashes

    def generate_fingerprints_from_peaks_threads(self, peaks):
        """
        Generate hashes from the peaks.

        Args:
            peaks (list): Peaks in the format [(frequency, time), ...].
        Returns:
            hashes (list): A list of hashes representing the audio fingerprint.
        """

        logging.info("Generating Fingerprints.")

        if self.sort_peaks:
            peaks.sort(key=lambda x: x[1])

        # Helper function to process a chunk of peaks, this used to be the main function before parallelization
        def process_chunk(chunk):
            chunk_hashes = []
            for i in range(len(chunk)):
                for j in range(1, self.fan_value):
                    if i + j < len(chunk):
                        freq1, t1 = chunk[i]
                        freq2, t2 = chunk[j + i]
                        t_delta = t2 - t1

                        if self.min_hash_time_delta <= t_delta <= self.max_hash_time_delta:
                            h = hashlib.sha1(
                                f"{freq1}|{freq2}|{t_delta}".encode('utf-8'))
                            chunk_hashes.append(
                                (h.hexdigest()[0:self.fingerprint_reduction], int(t1)))
            return chunk_hashes

        # Divide peaks into chunks for parallel processing
        num_chunks = NB_THREADS
        chunk_size = len(peaks) // num_chunks
        chunks = [peaks[i:i + chunk_size]
                  for i in range(0, len(peaks), chunk_size)]

        # Process chunks in parallel
        with ThreadPoolExecutor() as executor:
            results = executor.map(process_chunk, chunks)

        # Flatten the list of results
        hashes = [hash for result in results for hash in result]

        return hashes

    @staticmethod
    def plot_peaks(subarray, freq_indices_filter, time_indices_filter):
        fig, ax = plt.subplots(figsize=(15, 7))
        ax.imshow(subarray, aspect='auto', origin='lower')
        ax.scatter(time_indices_filter, freq_indices_filter, c='b', s=7)
        ax.set_title("Spectrogram with Peaks")
        ax.set_xlabel('Time')
        ax.set_ylabel('Frequency')
        plt.gca().invert_yaxis()
        plt.tight_layout()
        plt.show()

    def generate_fingerprints_from_samples(self, samples):
        """
        Full audio processing pipeline: generate spectrogram, find peaks, and generate hashes.

        Args:
            samples (np.ndarray): Audio samples as a 1D numpy array.
        Returns:
            fingerprints (list): A list of hashes representing the audio fingerprint.
        """

        spectrogram = self.generate_spectrogram(samples)

        if self.plot:
            # plot scpectrogram
            plt.figure(figsize=(10, 4))
            plt.imshow(spectrogram, aspect='auto', origin='lower')
            plt.colorbar()
            plt.title('Spectrogram')
            plt.xlabel('Time')
            plt.ylabel('Frequency')
            plt.show()



        # Convert the spectrogram to decibels to compress the range of values and make it easier to find peaks
        spectrogram = 10 * \
            np.log10(spectrogram, out=np.zeros_like(
                spectrogram), where=(spectrogram != 0))
        # log spectrogram

        peaks = self.find_peaks(spectrogram)

        # if self.plot:
        #     self.plot_peaks(peaks)

        logging.info(f"Found {len(peaks)} peaks. Peaks: {peaks[:10]}")

        fingerprints = self.generate_fingerprints_from_peaks(peaks)

        return fingerprints

    def generate_fingerprints_from_samples_threads(self, samples):
        """
        Full audio processing pipeline: generate spectrogram, find peaks, and generate hashes.

        Args:
            samples (np.ndarray): Audio samples as a 1D numpy array.
        Returns:
            fingerprints (list): A list of hashes representing the audio fingerprint.
        """

        spectrogram = self.generate_spectrogram(samples)


        if self.plot:
            # plot scpectrogram
            plt.figure(figsize=(10, 4))
            plt.imshow(spectrogram, aspect='auto', origin='lower')
            plt.colorbar()
            plt.title('Spectrogram')
            plt.xlabel('Time')
            plt.ylabel('Frequency')
            plt.show()

        # Convert the spectrogram to decibels to compress the range of values and make it easier to find peaks
        spectrogram = 10 * \
            np.log10(spectrogram, out=np.zeros_like(
                spectrogram), where=(spectrogram != 0))
        # log spectrogram

        peaks = self.find_peaks_threads(spectrogram)

        # if self.plot:
        #     self.plot_peaks(peaks)


        logging.info(f"Found {len(peaks)} peaks. Peaks: {peaks[:10]}")

        fingerprints = self.generate_fingerprints_from_peaks_threads(peaks)

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

    def generate_fingerprints_from_file_threads(self, file_path):
        """
        Full audio processing pipeline: load, generate spectrogram, find peaks, and generate hashes.

        Args:
            file_path (str): Path to the audio file.
        Returns:
            list: A list of hashes representing the audio fingerprint.
        """
        samples, rate = self.load_audio_file(file_path)

        return self.generate_fingerprints_from_samples_threads(samples)

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
        """
        Transforms offset into seconds.

        Args:
            offset (int): Offset of the hash, from the beginning of the audio (query or database).
        Returns:
            offset_in_seconds (float): The offset in seconds.
        """

        hop_size = self.window_size * (1 - self.overlap_ratio)
        frame_duration = hop_size / self.fs
        offset_in_seconds = offset * frame_duration

        return offset_in_seconds
