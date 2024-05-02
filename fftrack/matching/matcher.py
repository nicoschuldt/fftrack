from fftrack.audio.audio_processing import AudioProcessing

import logging
from collections import defaultdict, Counter
import matplotlib.pyplot as plt

# Flags for plotting and logging
PLOT = False
LOG_LEVEL = logging.INFO

# Configure logging
logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants for matching
CONFIDENCE_THRESHOLD = 0.5  # Confidence threshold for a match
TOP_N = 5 # Number of top matches to return


class Matcher:
    """
    Matches the fingerprint of the query with the fingerprints of the database.
    """

    def __init__(self, database_manager, plot=PLOT, confidence_threshold=CONFIDENCE_THRESHOLD, top_n=TOP_N):
        """
        Initialises the matcher with the database manager.
        """
        self.db_manager = database_manager
        self.audio_processor = AudioProcessing()
        self.plot = plot
        self.confidence_threshold = confidence_threshold
        self.top_n = top_n


    def get_best_match(self, sample_fingerprint):
        """
        Matches the sample fingerprint with the database.

        Args:
            sample_fingerprint (list): List of hashes in the format [(hash, offset), ...].
        Returns:
            top_matches (list): List of the song IDs and their match details of the top 5 matches
            best_match (tuple): A tuple of the best matching song ID and its match details.
        """

        # Find matches between sample hashes and the database
        hash_matches, matches_per_song = self.find_matches(sample_fingerprint)

        # Align the matches to find the most probable song match
        aligned_results = self.align_matches(hash_matches, matches_per_song)

        # Find the best match based on the highest count (confidence)
        if aligned_results:
            top_matches = self.find_top_n_matches(aligned_results, self.top_n)
            best_match = self.find_best_match(top_matches)

            return top_matches, best_match
        else:
            logging.info("No matches found, the song is not in the database.")
            return None, None


    def find_matches(self, sample_hashes):
        """
        Find matches between sample hashes and the database.

        Args:
            sample_hashes (list): List of hashes in the format [(hash, offset), ...].
        Returns:
            tuple: tuple of the match results and the number of unique hashes for each song.
        """

        logging.info(f"Matching {len(sample_hashes)} fingerprints with the database.")

        # Number of hash matches for each song (before aligning)
        matches_per_song = defaultdict(int)
        # List of all the possible matches
        possible_matches = []

        for hsh, sampled_offset in sample_hashes:
            # extracting the list of (song_id, offset) for the current hash
            matches_curr_hash = self.db_manager.get_fingerprint_by_hash(hsh)

            for sid, db_offset in matches_curr_hash:
                # Counting hash matches per song, without regards to offset
                matches_per_song[sid] += 1

                offset_difference = db_offset - sampled_offset

                # To filter the cases when db_offset > sampled_offset
                if offset_difference >= 0:
                    possible_matches.append((sid, offset_difference))

        return possible_matches, matches_per_song


    def align_matches(self, matches, matches_per_song):
        """
        Aligns the time difference of matches to find the most probable song match.

        Args:
            matches (list): List of matches in the format [(song_id, offset_difference), ...].
            matches_per_song (dict): Dictionary of song and the number of hash matches.
        Returns:
            aligned_results (dict): A dictionary of aligned match results for each song.

        """
        logging.info(f"Aligning {len(matches)} matches.")

        offset_by_song = defaultdict(list)

        # Group offset differences by song
        for sid, offset_difference in matches:
            offset_by_song[sid].append(offset_difference)

        # Analyze offset differences to find the best match
        aligned_results = {}
        # Sum of all the matches to calculate confidence
        sum_matches = 0

        for sid, offsets in offset_by_song.items():
            # Find the most common offset and its count (only if it is over the benchmark)
            # Testing benchmark: 0 matches for the same offset difference
            offset_counts = Counter({freq: count for freq, count in Counter(offsets).items() if count >= 0})

            if offset_counts:
                most_common_offset, count = offset_counts.most_common(1)[0]
                sum_matches += count

                aligned_results[sid] = {
                    "song_id": sid,
                    "offset": most_common_offset,
                    "count": count,
                    "confidence": count / len(offsets)
                }

        # Calculate confidence in a different way than by number of offsets
        aligned_results = self.confidence_by_matches(aligned_results, sum_matches)
        #aligned_results = self.confidence_by_score(aligned_results, matches_per_song)

        if self.plot:
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


    def confidence_by_score(self, aligned_results, matches_per_song):
        """
        Calculates how confident the algorithm is in the correctness of the match,
        which is the sum of hash and offset matches in each song.

        Args:
            aligned_results (dict): A dictionary of aligned match results for each song.
            matches_per_song (dict): Dictionary of songs and the number of their hash matches.
        Returns:
            aligned_result: Updated results.
        """

        for sid, info in aligned_results.items():
            most_common_offset = info["offset"]
            count = info["count"]
            matches_per_song[sid] += count
            info["confidence"] = matches_per_song[sid]
            confidence = info["confidence"]

            logging.info(f"Song ID: {sid}, "
                         f"Most Common Offset: {most_common_offset} "
                         f"({self.audio_processor.offset_to_seconds(most_common_offset)}s, "
                         f"Matches: {count}, "
                         f"Confidence: {confidence:.2f}")

        return aligned_results


    def confidence_by_matches(self, aligned_results, sum_matches):
        """
        Calculates how confident the algorithm is in the correctness of the match.

        Args:
            aligned_results (dict): A dictionary of aligned match results for each song.
            sum_matches (int): Sum of all the aligned matches.
        Returns:
            confidence (float): Percentage of confidence in the match, which is the ratio of song matches to total matches.
        """

        for sid, info in aligned_results.items():
            most_common_offset = info["offset"]
            count = info["count"]
            info["confidence"] = count / sum_matches
            confidence = info["confidence"]

            logging.info(f"Song ID: {sid}, "
                         f"Most Common Offset: {most_common_offset} "
                         f"({self.audio_processor.offset_to_seconds(most_common_offset)}s, "
                         f"Matches: {count}, "
                         f"Confidence: {confidence:.2f}")

        return aligned_results


    def find_top_n_matches(self, aligned_results, n):
        """
        Find the top matches (max top n) from aligned results based on the highest count.

        Args:
            aligned_results (dict): A dictionary of aligned match results for each song.
            n (int): Number of top matches to be returned.
        Returns:
            top_matches (list): A list of tuples of the best matching song IDs and their match details.
        """

        nb_song_matches = len(aligned_results)
        logging.info(f"{nb_song_matches} songs found that match.")

        if nb_song_matches >= n:
            top = n
        else:
            top = nb_song_matches

        # Sort and add top matches to a list
        sorted_matches = sorted(aligned_results.items(), key=lambda x: x[1]['count'], reverse=True)
        top_matches = sorted_matches[:top]

        return top_matches


    def find_best_match(self, top_matches):
        """
        Returns the best match from the top matches.

        Args:
            top_matches (list): A list of tuples with the top matches.
        Returns:
            A tuple of the best matching song ID and its match details
        """

        return top_matches[0]
