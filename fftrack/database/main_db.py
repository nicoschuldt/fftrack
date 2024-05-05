# demo for how to use the db manager

from .models import create_database
from .db_manager import DatabaseManager


def main():
    # 1. Initialize the database
    print("Initializing the database...")
    create_database()


    # 2. Add new song to the database
    db_manager = DatabaseManager()
    print("Adding a new song...")
    song_id = db_manager.add_song("Bohemian Rhapsody", "Queen",
                                  "A Night at the Opera", "1975-10-31")
    if song_id:
        print(f"Added song with ID: {song_id}")
    else:
        print("Failed to add song.")
        return


    # 3 Add fingerprint to the song
    print("Adding a fingerprint to the song...")
    fingerprint_hash = '1234567890abcdefghij'
    if db_manager.add_fingerprint(song_id, fingerprint_hash, 42):
        print("Fingerprint added successfully.")
    else:
        print("Failed to add fingerprint.")


    # 4 Retrieve and display the song information based on the fingerprint
    print("Retrieving song information based on the id...")
    song = db_manager.get_song_by_id(song_id)
    if song:
        print(f"Retrieved song: {song.title} by {song.artist}")
    else:
        print("Failed to retrieve song.")


    # 5 Retrieve and display the fingerprint information based on the hash
    print("Retrieving fingerprint information based on the hash...")
    fingerprints = db_manager.get_fingerprint_by_hash(fingerprint_hash)
    if fingerprints:
        print(f"Fingerprint found in the database: {fingerprints}")
    else:
        print("Fingerprint not found.")


    # Clean up
    # db_manager.close_session()


if __name__ == "__main__":
    main()
