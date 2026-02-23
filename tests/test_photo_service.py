import numpy as np
import pytest
from unittest.mock import MagicMock, patch
from PIL import Image

from service.photo_service import PhotoService


# ---------- fixtures ----------


@pytest.fixture
def dummy_embedding():
    return np.random.rand(768).astype(np.float32)


@pytest.fixture
def photo_service(dummy_embedding):
    drive_svc = MagicMock()
    repo = MagicMock()
    face_det = MagicMock()
    emb_gen = MagicMock(return_value=dummy_embedding)
    emb_gen.generate = MagicMock(return_value=dummy_embedding)
    http = MagicMock()

    svc = PhotoService(drive_svc, repo, face_det, emb_gen, http)
    return svc, drive_svc, repo, face_det, emb_gen, http


# ---------- find_user_photos ----------


def test_find_user_photos_returns_links(photo_service, dummy_embedding):
    svc, _, repo, _, emb_gen, http = photo_service

    http.fetch_user_image.return_value = Image.new("RGB", (100, 100))
    emb_gen.generate.return_value = dummy_embedding
    repo.find_similar.return_value = ["https://drive.google.com/file/abc"]

    result = svc.find_user_photos("user123")

    http.fetch_user_image.assert_called_once_with("user123")
    emb_gen.generate.assert_called_once()
    repo.find_similar.assert_called_once_with(dummy_embedding)
    assert result == ["https://drive.google.com/file/abc"]


def test_find_user_photos_empty_when_no_match(photo_service, dummy_embedding):
    svc, _, repo, _, _, _ = photo_service
    repo.find_similar.return_value = []
    result = svc.find_user_photos("user_no_photos")
    assert result == []


# ---------- index_last_24_hours ----------


def _make_fake_drive_file():
    return {
        "id": "file123",
        "webViewLink": "https://drive.google.com/file/file123",
    }


def test_index_skips_image_with_no_face(photo_service):
    svc, drive_svc, repo, face_det, emb_gen, _ = photo_service

    drive_svc.get_recent_images.return_value = [_make_fake_drive_file()]
    drive_svc.download_file.return_value = (
        open("tests/fixtures/blank.jpg", "rb").read() if False else b""
    )  # will be intercepted below

    # Patch cv2.imdecode so we control what comes back
    import numpy as np

    fake_img = np.zeros((200, 200), dtype=np.uint8)

    with patch("cv2.imdecode", return_value=fake_img):
        face_det.extract_faces.return_value = []  # no faces
        svc.index_last_24_hours()

    repo.save_embedding.assert_not_called()


def test_index_saves_embedding_when_face_found(photo_service, dummy_embedding):
    svc, drive_svc, repo, face_det, emb_gen, _ = photo_service

    drive_svc.get_recent_images.return_value = [_make_fake_drive_file()]
    drive_svc.download_file.return_value = b"fakebytes"

    fake_img = np.zeros((200, 200), dtype=np.uint8)

    with patch("cv2.imdecode", return_value=fake_img):
        face_det.extract_faces.return_value = [(10, 10, 80, 80)]  # one face
        emb_gen.generate.return_value = dummy_embedding
        svc.index_last_24_hours()

    repo.save_embedding.assert_called_once_with(
        file_id="file123",
        webviewlink="https://drive.google.com/file/file123",
        embedding=dummy_embedding,
    )


def test_index_continues_on_bad_file(photo_service):
    """One broken file must not abort the entire batch."""
    svc, drive_svc, repo, face_det, _, _ = photo_service

    drive_svc.get_recent_images.return_value = [
        {"id": "bad", "webViewLink": "https://x"},
        {"id": "good", "webViewLink": "https://y"},
    ]
    drive_svc.download_file.side_effect = [Exception("network error"), b"fakebytes"]

    fake_img = np.zeros((200, 200), dtype=np.uint8)

    with patch("cv2.imdecode", return_value=fake_img):
        face_det.extract_faces.return_value = [(0, 0, 50, 50)]
        svc.index_last_24_hours()

    # Only the good file should reach save_embedding
    assert repo.save_embedding.call_count == 1


# ---------- repo unit test ----------


def test_photo_repository_find_similar():
    from repository.photo_repository import PhotoRepository

    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    mock_cur.fetchall.return_value = [("https://link1",), ("https://link2",)]

    repo = PhotoRepository(mock_conn)
    embedding = np.random.rand(768).astype(np.float32)
    result = repo.find_similar(embedding, limit=2)

    assert result == ["https://link1", "https://link2"]
    mock_cur.execute.assert_called_once()


# ---------- http_client unit test ----------


def test_http_client_fetches_image():
    from utils.http_client import HttpClient

    client = HttpClient("https://example.com/users/{user_id}/photo")

    fake_img = Image.new("RGB", (100, 100))
    buf = __import__("io").BytesIO()
    fake_img.save(buf, format="JPEG")
    fake_bytes = buf.getvalue()

    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.content = fake_bytes
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        img = client.fetch_user_image("user42")

    mock_get.assert_called_once_with(
        "https://example.com/users/user42/photo", timeout=10
    )
    assert isinstance(img, Image.Image)
