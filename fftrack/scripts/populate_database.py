import argparse
import logging
import os

import pandas as pd
from pkg_resources import resource_filename
from pydub import AudioSegment
from pytube import YouTube
from sqlalchemy.orm import sessionmaker

from fftrack.audio.audio_processing import AudioProcessing
from fftrack.database import DatabaseManager
from fftrack.database.models import create_database, engine

# Constant values
DATABASE_URL = "sqlite:///fftrack.db"
csv_file_path = resource_filename(__name__, "songs_to_download.csv")
download_dir = resource_filename(__name__, "downloaded_songs")
delete_existing = False
delete_downloaded = True

# logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def download_song(youtube_url, download_path):
    """
    Download an audio file from YouTube and convert it to MP3.

    Args:
        youtube_url (str): The URL of the YouTube video.
        download_path (str): The directory where the downloaded file will be saved.
    """
    try:
        yt = YouTube(youtube_url)
        stream = yt.streams.filter(only_audio=True).first()

        # Ensure download directory exists
        if not os.path.exists(download_path):
            os.makedirs(download_path, exist_ok=True)

        # Download the file
        out_file = stream.download(output_path=download_path)

        # Log the selected stream details
        logging.info(
            f"Selected stream: {stream.mime_type}, {stream.default_filename}")

        # Load audio file
        audio_clip = AudioSegment.from_file(out_file, format="mp4")

        # Convert to MP3
        out_file_mp3 = out_file.replace(".mp4", ".mp3")
        audio_clip.export(out_file_mp3, format="mp3")

        logging.info(
            f"Downloaded and converted {youtube_url} to {out_file_mp3}")
        return out_file_mp3

    except Exception as e:
        logging.error(f"Error downloading and converting {youtube_url}: {e}")
        return None


def populate_database(db, csv_path, delete_existing=delete_existing, delete_downloaded=delete_downloaded):
    """
    Populate the database with songs from a CSV file.

    Args:
        csv_path (str): The path to the CSV file containing song information.
            CSV file should have columns: 'song_name', 'artist', 'album', 'release_date', 'youtube_link'.
        db (db_manager object): The database manager object.
        delete_existing (bool): If True, delete songs from the database.
        delete_downloaded (bool): If True, delete the downloaded song file.
    Returns:
        None
    """

    if not csv_path:
        csv_path = csv_file_path

    if not os.path.exists(csv_path):
        logging.error(f"File not found: {csv_path}")
        return

    ap = AudioProcessing(plot=False)
    # If delete_existing, delete all existing songs in the database
    if delete_existing:
        db.reset_database()

    df = pd.read_csv(csv_path)
    for _, row in df.iterrows():
        if db.get_song_by_title_artist(row['song_name'], row['artist']) is None:
            song_path = download_song(row['youtube_link'], download_dir)
            if song_path:
                # All rows are filled up
                if type(row['album']) is not float and type(row['release_date']) is not float:
                    song_id = db.add_song(
                        row['song_name'], row['artist'], album=row['album'],
                        release_date=row['release_date'], youtube_link=row['youtube_link'])

                # Without an album with release date
                elif type(row['album']) is float and type(row['release_date']) is not float:
                    song_id = db.add_song(
                        row['song_name'], row['artist'], release_date=row['release_date'], youtube_link=row['youtube_link'])

                # Without a release date with album
                elif type(row['release_date']) is float and type(row['album']) is not float:
                    song_id = db.add_song(
                        row['song_name'], row['artist'], release_date=row['album'], youtube_link=row['youtube_link'])

                # If there is no album/release date information, then add without it
                else:
                    song_id = db.add_song(
                        row['song_name'], row['artist'], youtube_link=row['youtube_link'])

                logging.info(
                    f"Added song to database: ID {song_id}, {row['song_name']} by {row['artist']}")

                # generate fingerprints
                fingerprints = ap.generate_fingerprints_from_file_threads(song_path)
                logging.info(
                    f"Generated {len(fingerprints)} fingerprints for song: {row['song_name']}")
                # Add fingerprints to the database
                logging.info(
                    f"Adding fingerprints to the database for song: {row['song_name']}")
                if db.add_fingerprints_bulk(song_id, fingerprints):
                    logging.info(
                        f"Fingerprints added to the database for song: {row['song_name']}")
                else:
                    logging.error(
                        f"Failed to add fingerprints to the database for song: {row['song_name']}")

                if delete_downloaded:
                    os.remove(song_path)
                    logging.info(
                        f"Deleted downloaded song from folder: {song_path}")

        else:
            logging.info(
                f"Song {row['song_name']} by {row['artist']} already in the database.")


def main():
    parser = argparse.ArgumentParser(
        description="Populate the database with songs from a CSV file.")
    parser.add_argument("--csv-path", type=str, help="Path to the CSV file containing song information.",
                        default=csv_file_path)
    parser.add_argument("--download-dir", type=str, help="Directory where to save the downloaded songs.",
                        default=download_dir)
    parser.add_argument("--delete-existing", action="store_true",
                        help="Delete existing songs in the database.")
    parser.add_argument("--delete-downloaded", action="store_true",
                        help="Delete downloaded songs after adding to the database.")
    args = parser.parse_args()

    # Ensure download directory exists
    os.makedirs(args.download_dir, exist_ok=True)

    # Database initialization
    # verify that the database is created
    create_database()

    Session = sessionmaker(bind=engine)
    session = Session()
    db_manager = DatabaseManager(session)

    if args.delete_existing:
        # Assume reset_database() is a method to delete all entries; implement accordingly
        logging.info("Deleting existing records from the database.")
        db_manager.reset_database()

    populate_database(db_manager, args.csv_path,
                      args.delete_existing, True)
    session.close()
    logging.info("Database population complete.")


if __name__ == "__main__":
    main()
