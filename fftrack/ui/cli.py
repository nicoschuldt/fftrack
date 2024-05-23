from rich.console import Console
from rich.table import Table
import typer

from fftrack.database.db_manager import DatabaseManager

console = Console()


def display_best_match(best_match, db_manager):
    """
    Display song metadata of the best match to the user.

    Args:
        best_match (tuple): a tuple with the best match in the following format :(song_ID,{matching_details}).
    """
    song_id = best_match[0]
    song = db_manager.get_song_by_id(song_id)
    if song:
        print(
            f"The song you were looking for... {song.title} by {song.artist}")
        if song.release_date:
            print(f"release date: {song.release_date}")
        if song.album:
            print(f"album: {song.album}")
        # if song.youtube_link:
        # print(f"link: {song.youtube_link}")
    else:
        print("Failed to retrieve song.")


def display_top_matches(top_matches, db_manager):
    """
    Display song info of the best matches to the user.

    Args:
        top_matches (list): A list of the top matches, with their song_id and match details.
    """
    table = Table("Top", "ID", "Title", "Artist", "release date", "Album", "link")
    cpt = 1
    for song_id, info in top_matches:
        song = db_manager.get_song_by_id(song_id)
        if song:
            table.add_row(str(cpt), str(song_id), song.title, song.artist,
                          str(song.release_date), song.album, song.youtube_link)
        else:
            print("Failed to retrieve song.")
        cpt += 1
    console.print("--------------------------")
    console.print(table)


def input_listen_time():
    time = input("For how many seconds would you like to record (3-10)? ")
    if time == "" or time is None:
        return None
    if 3 <= int(time) <= 10:
        return time
    return None


if __name__ == "__main__":
    pass
