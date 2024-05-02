import os
import typer
from rich.console import Console
from rich.table import Table
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fftrack.database.db_manager import DatabaseManager

db_manager=DatabaseManager()
# Create the engine
#database_path=???
#engine = create_engine(f'sqlite:///{database_path}')

# Create a sessionmaker bound to the engine
#Session = sessionmaker(bind=engine)
#session = Session()




def get_audio_path(file_name):
    """
    Receive the audio input from the user and returns the file path.

    Args:
        file_name (str): the file of the audio input.

        Returns:
            str: Audio_path.
        """
    #Demander si c pas mieux de mettre le path dans audio reader directement
    # if the file is present in current directory,
    return os.path.abspath(file_name)

    #if the file isn't present in current directory
    #for root, dirs, files in os.walk(r'C:\Example\path_of_given_file'):
    #for name in files:
        #if name == file_name:  
            #return os.path.abspath(os.path.join(root, name))


def display_best_match(best_matches):
    """
    Display song info of the best match to the user.

    Args:
        song_matches (tuple): a tuple with the best match in the following format :(song_ID,{matching_details}).

    Returns:
        None
    """
    song_id=best_matches[0]
    song = db_manager.get_song_by_id(song_id)
    if song:
        print(f"The song you were looking for... {song.title} by {song.artist}, {song.release_date}")
        if song.album:
            print(f"album :{song.album}")
        if song.youtube_link:
            print(f"link :{song.youtube_link}")
    else:
        print("Failed to retrieve song.")


console = Console()
def display_best_top_matches(best_matches):
    """
    Display song info of the best matches to the user.

    Args:
        best_matches (dict): A dictionary of aligned match results for each song in the following format : {'song_id': matching_details} 

    Returns:
        None
    """
    table = Table("Top","Title", "Artist","release date", "Album","link")
    cpt=1
    for song_id in best_matches:
        song = db_manager.get_song_by_id(song_id)
        if song:
            table.add_row(cpt,song.title,song.artist,song.release_date,song.album,song.youtube_link)
        else:
            print("Failed to retrieve song.")
        cpt+=1
    

if __name__=="__main__":
    pass