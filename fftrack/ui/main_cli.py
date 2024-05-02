import os
import typer
from rich.console import Console
from rich.table import Table
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fftrack.database.db_manager import DatabaseManager
from fftrack.database.models import create_database

# Initialise database and add songs and their fingerprints to it for testing
def database():
    # 1. Initialize the database
    print("Initializing the database...")
    create_database()

    # 2. Add new song to the database and their fingerprint
    db_manager = DatabaseManager()

    print("Adding a new song...")
    song_id = db_manager.add_song("Bohemian Rhapsody", "Queen",
                                  "A Night at the Opera", "1975-10-31")
    if song_id:
        print(f"Added song with ID: {song_id}")
    else:
        print("Failed to add song.")
        return
    """
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


if __name__=="__main__":
    db=database()