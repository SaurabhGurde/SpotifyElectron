from fastapi.testclient import TestClient
from main import app as app

client = TestClient(app)


def get_playlist_dto(name: str, headers: dict):
    response = client.get(f"/playlists/dto/{name}", headers=headers)
    return response


def get_song_dto(name: str, headers: dict):
    response = client.get(f"/canciones/dto/{name}", headers=headers)
    return response