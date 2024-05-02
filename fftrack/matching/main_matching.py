# demo for how to use the matcher
from .matcher import Matcher
from fftrack.database.db_manager import DatabaseManager
from fftrack.database.models import create_database


# Initialise database and add songs and their fingerprints to it for testing
def database():
    # 1. Initialize the database
    print("Initializing the database...")
    create_database()

    # 2. Add new song to the database and their fingerprint
    db_manager = DatabaseManager()
    """
    print("Adding a new song...")
    song_id = db_manager.add_song("Bohemian Rhapsody", "Queen",
                                  "A Night at the Opera", "1975-10-31")
    if song_id:
        print(f"Added song with ID: {song_id}")
    else:
        print("Failed to add song.")
        return

    print("Adding a fingerprint to the song...")
    fingerprint_hash = '8e6e5474fac838a5a78c'
    if db_manager.add_fingerprint(song_id, fingerprint_hash, 7):
        print("Fingerprint added successfully.")
    else:
        print("Failed to add fingerprint.")

    print("Adding a fingerprint to the song...")
    fingerprint_hash = 'a72ca2ae44f9ee58d5aa'
    if db_manager.add_fingerprint(song_id, fingerprint_hash, 12):
        print("Fingerprint added successfully.")
    else:
        print("Failed to add fingerprint.")

    print("Adding a fingerprint to the song...")
    fingerprint_hash = 'be3e08e64b5e1442168d'
    if db_manager.add_fingerprint(song_id, fingerprint_hash, 55):
        print("Fingerprint added successfully.")
    else:
        print("Failed to add fingerprint.")

    print("Adding a fingerprint to the song...")
    fingerprint_hash = 'be3e08e64b5e1442168d'
    if db_manager.add_fingerprint(song_id, fingerprint_hash, 43):
        print("Fingerprint added successfully.")
    else:
        print("Failed to add fingerprint.")

    print("Adding a fingerprint to the song...")
    fingerprint_hash = 'be3e08e64b5e1442168d'
    if db_manager.add_fingerprint(song_id, fingerprint_hash, 65):
        print("Fingerprint added successfully.")
    else:
        print("Failed to add fingerprint.")


    print("Adding a new song...")
    song_id = db_manager.add_song("Daechwita", "Agust D",
                                  "D-2", "2022-03-22")
    if song_id:
        print(f"Added song with ID: {song_id}")
    else:
        print("Failed to add song.")
        return

    print("Adding a fingerprint to the song...")
    fingerprint_hash = '8e6e5474fac838a5a78c'
    if db_manager.add_fingerprint(song_id, fingerprint_hash, 45):
        print("Fingerprint added successfully.")
    else:
        print("Failed to add fingerprint.")

    print("Adding a fingerprint to the song...")
    fingerprint_hash = '060e923715797a050c3b'
    if db_manager.add_fingerprint(song_id, fingerprint_hash, 79):
        print("Fingerprint added successfully.")
    else:
        print("Failed to add fingerprint.")

    print("Adding a fingerprint to the song...")
    fingerprint_hash = 'be3e08e64b5e1442168d'
    if db_manager.add_fingerprint(song_id, fingerprint_hash, 77):
        print("Fingerprint added successfully.")
    else:
        print("Failed to add fingerprint.")


    print("Adding a new song...")
    song_id = db_manager.add_song("I wish", "One Direction",
                                  "Up All Night")
    if song_id:
        print(f"Added song with ID: {song_id}")
    else:
        print("Failed to add song.")
        return

    print("Adding a fingerprint to the song...")
    fingerprint_hash = 'be3e08e64b5e1442168d'
    if db_manager.add_fingerprint(song_id, fingerprint_hash, 77):
        print("Fingerprint added successfully.")
    else:
        print("Failed to add fingerprint.")

    print("Adding a fingerprint to the song...")
    fingerprint_hash = '8e6e5474fac838a5a78c'
    if db_manager.add_fingerprint(song_id, fingerprint_hash, 45):
        print("Fingerprint added successfully.")
    else:
        print("Failed to add fingerprint.")

    print("Adding a fingerprint to the song...")
    fingerprint_hash = '2d74c8e3210102e7b2cf'
    if db_manager.add_fingerprint(song_id, fingerprint_hash, 45):
        print("Fingerprint added successfully.")
    else:
        print("Failed to add fingerprint.")
    """
    return db_manager


def main():
    # 0. Setting up database and database manager to have an input
    print("Setting up database for testing...")
    db_manager = database()
    if db_manager:
        print("Database successfully set up.")
    else:
        print("Setting up database failed.")
        return

    # 1. Initialise the matcher
    print("Initialising matcher...")
    match = Matcher(db_manager)
    if match:
        print("Matcher successfully initialised.")
    else:
        print("Matcher initialisation failed.")
        return

    # 2. Find matches for the sample match
    print("Creating list of possible matches according to hashes...")
    possible_matches, matches_per_song = match.find_matches([('be3e08e64b5e1442168d', 77),
            ('060e923715797a050c3b', 79),
            ('8e6e5474fac838a5a78c', 45),
            ('be3e08e64b5e1442168d', 43),
            ('228f2e4fe7d02b97790d', 12)])

    if possible_matches:
        print("Possible matches successfully retracted.")
        print(f"Matches per song: {matches_per_song}")
        print(f"List of possible matches: {possible_matches}")
    else:
        print("Matching hashes failed.")
        return

    # 3. Align the offset of matches
    print("Aligning matches...")
    results = match.align_matches(possible_matches)
    if results:
        print("Aligning matches was successful.")
        print("Aligned matches:")
        for song, matches in results.items():
            print(f"{song}: {matches}")
    else:
        print("Aligning matches failed.")
        return

    # 4. Find best match
    print("Retracting information of best match...")
    best_match = match.find_best_match(results)
    if best_match:
        print(f"Best match: {best_match}.")
    else:
        print("Finding best match failed.")
        return

    # Clean up
    db_manager.close_session()

if __name__ == "__main__":
    main()