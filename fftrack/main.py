import typer
import os
import json
import time

from .config import *
from .database.db_manager import DatabaseManager
from .audio.audio_processing import AudioProcessing
from .audio.audio_reader import AudioReader
from .matching.matcher import Matcher
from .scripts.populate_database import download_song

app = typer.Typer()
audio_reader = AudioReader()
audio_processor = AudioProcessing(plot=False)
db = DatabaseManager()
matcher = Matcher(db)


# config
config = load_config()
LISTEN_TIME = int(config["listen_time"])


# Commands
@app.command(help="Interactive menu for navigating the application.")
def menu():
    """
    Interactive menu for navigating the application features.
    """
    typer.echo("Welcome to the FFTrack Audio Recognition System!")
    typer.echo("Please choose an option:")
    typer.echo("[1] Listen for a song using the microphone and identify it")
    typer.echo("[2] Identify a song from an audio file")
    typer.echo("[3] Add a song to the database")
    typer.echo("[4] Display all songs in the database")
    typer.echo("[5] Delete a song from the database")
    typer.echo("[0] Exit")

    choice = typer.prompt("Enter your choice", type=int)

    if choice == 1:
        listen()
    elif choice == 2:
        file_path = typer.prompt("Enter the path to the audio file")
        identify(file_path)
    elif choice == 3:
        add_song()
    elif choice == 4:
        list_songs()
    elif choice == 5:
        song_id = typer.prompt("Enter the ID of the song to delete", type=int)
        delete_song(song_id)
    elif choice == 0:
        typer.echo("Exiting the application.")
        raise typer.Exit()
    else:
        typer.echo("Invalid choice, please try again.")
        menu()



@app.command(help="Listen for a song using the microphone and identify it.")
def listen():
    """
    Listen for a song using the microphone and identify it.

    Returns:
        None
    """
    try:
        typer.echo(f"Listening for {LISTEN_TIME}s...")
        audio_reader.start_recording()
        time.sleep(LISTEN_TIME)
        audio_reader.stop_recording()
        typer.echo("Audio recording complete.")
    except Exception as e:
        typer.echo(f"Error recording audio: {e}")

        return

    # Process the audio file
    try:
        typer.echo("Processing audio...")
        fingerprints = audio_processor.generate_fingerprints_from_file(audio_reader.output_filename)
        typer.echo(f"Generated {len(fingerprints)} fingerprints successfully.")
    except Exception as e:
        typer.echo(f"Error processing audio: {e}")
        return

    try:
        # Match the audio file against the database
        typer.echo("Matching audio...")
        top_matches, best_match = matcher.get_best_match(fingerprints)
        if best_match:
            song_id, match_details = best_match
            typer.echo(f"Best match: Song ID {song_id}, Match details: {match_details}")
        else:
            typer.echo("No match found.")
    except Exception as e:
        typer.echo(f"Error matching audio: {e}")
        return


@app.command(help="Identifies a song from an audio file.")
def identify(file_path: str):
    """
    Identify a song from an audio file.

    Args:
        file_path (str): Path to the audio file.

    Returns:
        None
    """

    try:
        typer.echo("Loading audio file...")
        audio_reader.audio_to_wav(file_path)
    except Exception as e:
        typer.echo(f"Error loading audio file: {e}")
        return

    # Process the audio file
    try:
        typer.echo("Processing audio...")
        fingerprints = audio_processor.generate_fingerprints_from_file(audio_reader.output_filename)
        typer.echo(f"Generated {len(fingerprints)} fingerprints successfully.")
    except Exception as e:
        typer.echo(f"Error processing audio: {e}")
        return

    try:
        # Match the audio file against the database
        typer.echo("Matching audio...")
        best_match = matcher.get_best_match(fingerprints)
        if best_match:
            song_id, match_details = best_match
            typer.echo(f"Best match: Song ID {song_id}, Match details: {match_details}")
            # get song details
            song = db.get_song_by_id(song_id)
            typer.echo(f"Song details: {song}")
        else:
            typer.echo("No match found.")
    except Exception as e:
        typer.echo(f"Error matching audio: {e}")
        return


@app.command("add-song", help="Add a song to the database.")
def add_song(song_path: str = typer.Option(None, help="Path to the local audio file"),
             yt_link: str = typer.Option(None, "--yt", help="YouTube link to download the song from")):
    """
    Add a song to the database, either from a local file or by downloading it from YouTube.

    Args:
        song_path (str): Path to the audio file.
        yt_link (str): YouTube link to download the song.

    Returns:
        None
    """
    if yt_link:
        # Download the song from YouTube
        typer.echo("Downloading song from YouTube...")
        song_path = download_song(yt_link, 'downloaded_songs')
        if song_path is None:
            typer.echo("Failed to download song.")
            raise typer.Exit()

    if song_path is None:
        typer.echo("No song provided.")
        raise typer.Exit()

    # Ask for song details
    song_name = typer.prompt("Enter the song name")
    artist = typer.prompt("Enter the artist name")
    album = typer.prompt("Enter the album name", default="")
    release_date = typer.prompt("Enter the release date", default="")
    if not release_date:
        release_date = None

    # Add song to database
    song_id = db.add_song(song_name, artist, album, release_date)
    if song_id is None:
        typer.echo("Failed to add song to the database.")
        return
    typer.echo(f"Song added to the database with ID: {song_id}")

    # Generate fingerprints
    typer.echo("Processing audio and generating fingerprints...")
    fingerprints = audio_processor.generate_fingerprints_from_file(song_path)
    typer.echo(f"Generated {len(fingerprints)} fingerprints.")

    # Add fingerprints to the database
    for hash, offset in fingerprints:
        db.add_fingerprint(song_id, hash, offset)

    typer.echo(f"Song and fingerprints added to the database.")


@app.command("delete-song", help="Delete a song from the database.")
def delete_song(song_id: int = typer.Option(..., help="ID of the song to delete")):
    """
    Delete a song from the database.

    Args:
        song_id (int): ID of the song to delete.

    Returns:
        None
    """
    try:
        song = db.get_song_by_id(song_id)
        if not song:
            typer.echo(f"Song with ID {song_id} not found in the database.")
            return

        typer.echo(f"Deleting song: {song.title} by {song.artist}...")
        db.delete_song(song_id)
        typer.echo("Song deleted from the database.")
    except Exception as e:
        typer.echo(f"Failed to delete song: {e}")


@app.command("list-songs", help="Display all songs in the database.")
def list_songs():
    """
    Display all songs in the database.
    """
    try:
        songs = db.get_all_songs()
        if not songs:
            typer.echo("No songs found in the database.")
            return

        typer.echo("Songs in the database:")
        for song in songs:
            typer.echo(f"ID: {song.song_id}, Title: '{song.title}', Artist: '{song.artist}', Album: '{song.album}', Release Date: '{song.release_date}'")
    except Exception as e:
        typer.echo(f"Failed to retrieve songs: {e}")


# config
@app.command(help="Displays the current configuration.")
def get_config():
    """
    Display the current configuration.

    Returns:
        None
    """
    typer.echo("Current configuration:")
    typer.echo(config)


@app.command(help="Updates a single configuration setting.")
def get_setting(setting: str):
    """
    Get the value of a single configuration setting.

    Args:
        setting (str): The name of the setting to display.

    Returns:
        None
    """
    typer.echo(f"Current value of {setting}: {config[setting]}")


@app.command(help="Creates a new configuration file with default values.")
def new_config():
    """
    Create a new configuration file with default values.

    Returns:
        None
    """
    user_config_file_path = typer.prompt(
        "Enter the path for the new configuration file, e.g., /path/to/new_config.json:")

    create_user_config_file(user_config_file_path)
    typer.echo(f"New configuration file created at {user_config_file_path}.")


@app.command(help="Replaces the current configuration with a new configuration file.")
def replace_config(config_file_path: str):
    """
    Replace the current configuration with a new configuration file.

    Args:
        config_file_path (str): Path to the new configuration file.

    Returns:
        None
    """
    with open(config_file_path, 'r') as f:
        new_config = json.load(f)
    save_config(new_config)
    typer.echo(f"Configuration file replaced with {config_file_path}.")


if __name__ == "__main__":
    app()
