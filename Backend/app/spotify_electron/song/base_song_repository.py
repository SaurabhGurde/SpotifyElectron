import app.spotify_electron.song.providers.song_collection_provider as song_collection_provider
from app.logging.logging_constants import (
    LOGGING_BASE_SONG_REPOSITORY,
)
from app.logging.logging_schema import SpotifyElectronLogger
from app.spotify_electron.genre.genre_schema import Genre
from app.spotify_electron.song.base_song_schema import (
    SongDeleteException,
    SongMetadataDAO,
    SongNotFoundException,
    SongRepositoryException,
    get_song_metadata_dao_from_document,
)
from app.spotify_electron.song.providers.song_collection_provider import (
    get_song_collection,
)
from app.spotify_electron.song.validations.base_song_repository_validations import (
    handle_song_delete_count,
    handle_song_exists,
)

song_repository_logger = SpotifyElectronLogger(LOGGING_BASE_SONG_REPOSITORY).getLogger()


def check_song_exists(name: str) -> bool:
    """Check if song exits

    Args:
        name (str): song name

    Raises:
        SongRepositoryException: unexpected error checking if song exists

    Returns:
        bool: if song exists
    """
    try:
        collection = song_collection_provider.get_song_collection()
        song = collection.find_one({"name": name}, {"_id": 1})
    except Exception as exception:
        song_repository_logger.exception(
            f"Error checking if Song {name} exists in database"
        )
        raise SongRepositoryException from exception
    else:
        result = song is not None
        song_repository_logger.debug(f"Song with name {name} exists : {result}")
        return result


def get_song_metadata(name: str) -> SongMetadataDAO:
    """Get song metadata from database

    Args:
        name (str): song name

    Raises:
        SongNotFoundException: song not found
        SongRepositoryException: unexpected error getting song metadata

    Returns:
        SongMetadataDAO: the song
    """
    try:
        collection = song_collection_provider.get_song_collection()
        song = collection.find_one({"name": name})
        handle_song_exists(song)
        song_dao = get_song_metadata_dao_from_document(song)  # type: ignore

    except SongNotFoundException as exception:
        raise SongNotFoundException from exception

    except Exception as exception:
        song_repository_logger.exception(
            f"Error getting Song metadata {name} from database"
        )
        raise SongRepositoryException from exception
    else:
        song_repository_logger.info(f"Get Song metadata by name returned {song_dao}")
        return song_dao


def delete_song(name: str) -> None:
    """Deletes a song

    Args:
    ----
        name (str): song name

    Raises:
    ------
        SongRepositoryException: an error occurred while deleting song from database

    """
    try:
        collection = song_collection_provider.get_song_collection()
        result = collection.delete_one({"name": name})
        handle_song_delete_count(result)
        song_repository_logger.info(f"Song {name} Deleted")
    except SongDeleteException as exception:
        song_repository_logger.exception(f"Error deleting song {name} from database")
        raise SongRepositoryException from exception
    except SongRepositoryException as exception:
        song_repository_logger.exception(
            f"Unexpected error deleting song {name} in database"
        )
        raise SongRepositoryException from exception


def get_artist_from_song(name: str) -> str:
    """Get artist name from song

    Args:
        name (str): song name

    Returns:
        str: the artist name
    """
    try:
        collection = song_collection_provider.get_song_collection()
        return collection.find_one({"name": name}, {"_id": 0, "artist": 1}).get(  # type: ignore
            "artist"
        )
    except SongRepositoryException as exception:
        song_repository_logger.exception(
            f"Unexpected error getting artist from song {name} in database"
        )
        raise SongRepositoryException from exception


def increase_playback_count(name: str) -> None:
    """Increase number of song playbacks

    Args:
        name (str): song name
    """
    try:
        collection = song_collection_provider.get_song_collection()
        collection.update_one({"name": name}, {"$inc": {"number_of_playbacks": 1}})
    except SongRepositoryException as exception:
        song_repository_logger.exception(
            f"Unexpected error increasing playback count for artist {name} in database"
        )
        raise SongRepositoryException from exception


def get_artist_playback_count(artist_name: str) -> int:
    """Get artist total playback count

    Args:
        artist_name (str): artist name

    Returns:
        int: the number of total playback counts of artist songs
    """
    try:
        collection = get_song_collection()
        result_number_playback_count_query = collection.aggregate(
            [
                {"$match": {"artist": artist_name}},
                {"$group": {"_id": None, "total": {"$sum": "$number_of_playbacks"}}},
            ]
        )
        result_number_playback_count_query = next(
            result_number_playback_count_query, None
        )

        if result_number_playback_count_query is None:
            return 0
        return result_number_playback_count_query["total"]
    except SongRepositoryException as exception:
        song_repository_logger.exception(
            f"Unexpected error gettig artist {artist_name} playback count in database"
        )
        raise SongRepositoryException from exception


def get_song_names_search_by_name(song_name: str) -> list[str]:
    """Get song names when searching by name

    Args:
        song_name (str): song name to match

    Returns:
        list[str]: list of song names that matched the song name
    """
    try:
        collection = song_collection_provider.get_song_collection()
        song_names_response = collection.find(
            {"name": {"$regex": song_name, "$options": "i"}}, {"_id": 0, "name": 1}
        )
        return [song["name"] for song in song_names_response]  # type: ignore
    except SongRepositoryException as exception:
        song_repository_logger.exception(
            f"Unexpected error getting song names that matched {song_name} in database"
        )
        raise SongRepositoryException from exception


def get_songs_metadata_by_genre(genre: str) -> list[SongMetadataDAO]:
    """Get songs metadata by genre

    Args:
        genre (str): genre to match

    Raises:
        SongRepositoryException: unexpected error getting song metadatas from genre

    Returns:
        list[SongMetadataDAO]: list of song metadatas with selected genre
    """
    collection = song_collection_provider.get_song_collection()
    result_get_song_by_genre = collection.find({"genre": genre})
    try:
        return [
            SongMetadataDAO(
                name=song_data["name"],
                artist=song_data["artist"],
                photo=song_data["photo"],
                seconds_duration=song_data["duration"],
                genre=Genre(song_data["genre"]),
                number_of_playbacks=song_data["number_of_playbacks"],
            )
            for song_data in result_get_song_by_genre
        ]
    except SongRepositoryException as exception:
        song_repository_logger.exception(
            f"Unexpected error getting songs metadata by genre {genre} in database"
        )
        raise SongRepositoryException from exception