from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from .models import engine, Song, Fingerprint

# Create a Session class bound to the engine (for database interactions with
# the models defined in models.py)
Session = sessionmaker(bind=engine)


class DatabaseManager:
    """
    Handles interactions with the database, including adding and retrieving
    songs and fingerprints.
    """

    def __init__(self, session=None):
        """
        Initializes DatabaseManager with a session.
        If no session is provided, a new session is created.
        """
        self.session = session if session else Session()


    def add_song(self, title, artist, album=None, release_date=None, youtube_link=None):
        """
        Adds a new song to the database.

        Parameters:
            title (str): The title of the song.
            artist (str): The artist of the song.
            album (str, optional): The album of the song. Defaults to None.
            release_date (str, optional): The release date of the song in
                                        'YYYY-MM-DD' format. Defaults to None.

        Returns:
            song_id (int): The ID of the newly added song,
            or None if an error occurred.
        """
        try:
            # Convert release_date from string to date object if release_date
            # is not None
            if release_date:
                release_date = datetime.strptime(release_date,
                                                 "%Y-%m-%d").date()

            new_song = Song(title=title, artist=artist, album=album,
                            release_date=release_date, youtube_link=youtube_link)
            self.session.add(new_song)
            self.session.commit()
            return new_song.song_id
        except SQLAlchemyError as e:
            self.session.rollback()  # Roll back the transaction on error
            print(f"Error adding song to database: {e}")
            return None


    def get_song_by_id(self, song_id):
        """
        Gets a song by its ID.

        Parameters:
            song_id (int): The ID of the song to retrieve.

        Returns:
            Song: The Song object if found, None otherwise.
        """
        try:
            song = self.session.query(Song).filter(Song.song_id == song_id).first()
            return song
        except SQLAlchemyError as e:
            print(f"Error retrieving song from database: {e}")
            return None

    def add_fingerprint(self, song_id, hex_fingerprint, offset):
        """
        Adds a new fingerprint to the database associated with a song.

        Parameters:
            song_id (int): The ID of the song the fingerprint belongs to.
            hex_fingerprint (str): The fingerprint data as a 20-character hexadecimal string.
            offset (int): The offset of the fingerprint within the song.

        Returns:
            bool: True if the fingerprint was added successfully, False otherwise.
        """
        try:
            new_fingerprint = Fingerprint(song_id=song_id, hash=hex_fingerprint, offset=offset)
            self.session.add(new_fingerprint)
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"Error adding fingerprint to database: {e}")
            return False

    def get_fingerprint_by_hash(self, hex_fingerprint):
        """
        Fetches fingerprints by their hash, returning offsets and song IDs.

        Parameters:
            hex_fingerprint (str): The 20-character hexadecimal hash of the fingerprint to search for.

        Returns:
            list of tuples: A list where each tuple contains (song_id, offset)
            for each matching fingerprint.
        """
        try:
            fingerprints = self.session.query(Fingerprint.song_id, Fingerprint.offset).filter(
                Fingerprint.hash == hex_fingerprint).all()
            return fingerprints
        except SQLAlchemyError as e:
            print(f"Error retrieving fingerprints by hash from database: {e}")
            return []

    # Reset the database
    def reset_database(self):
        """
        Resets the database by dropping all tables and recreating them.
        """
        try:
            Song.__table__.drop(engine)
            Fingerprint.__table__.drop(engine)
            Song.__table__.create(engine)
            Fingerprint.__table__.create(engine)
            print("Database reset successfully.")
        except SQLAlchemyError as e:
            print(f"Error resetting database: {e}")

    # Close session
    def close_session(self):
        """
        Closes the database session.
        """
        self.session.close()
