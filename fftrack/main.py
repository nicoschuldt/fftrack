import typer
import os
import json
import time

from .config import *
from .database.db_manager import DatabaseManager
from .audio.audio_processing import AudioProcessing
from .audio.audio_reader import AudioReader
from .matching.matcher import Matcher

app = typer.Typer()
audio_reader = AudioReader()
audio_processor = AudioProcessing(plot=False)
db = DatabaseManager()
matcher = Matcher(db)

# config
config = load_config()
LISTEN_TIME = int(config["listen_time"])


# main
@app.command()
def main():
    typer.echo("Welcome to FFTrack!")
    typer.echo("Use the --help flag to see available commands.")


@app.command()
def listen():
    # Record audio from the microphone
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
        best_match = matcher.get_best_match(fingerprints)
        if best_match:
            song_id, match_details = best_match
            typer.echo(f"Best match: Song ID {song_id}, Match details: {match_details}")
        else:
            typer.echo("No match found.")
    except Exception as e:
        typer.echo(f"Error matching audio: {e}")
        return


@app.command()
def identify(file_path: str):
    # Load an audio file
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


@app.command()
def get_config():
    typer.echo("Current configuration:")
    typer.echo(config)


@app.command()
def get_setting(setting: str):
    typer.echo(f"Current value of {setting}: {config[setting]}")


if __name__ == "__main__":
    app()
