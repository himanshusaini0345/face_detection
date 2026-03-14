import os

from Models.extracted_face import ExtractedFace
from Models.photo import Photo
from Repositories.folder_repository import FolderRepository
from Services.employee_image_downloader import EmployeeImageDownloader
from Services.face_extractor import FaceExtractor
from Services.face_matcher import FaceMatcher
from Services.image_fetcher import GoogleDriveImageFetcher
from Repositories.photo_repository import PhotoRepository
from Repositories.extracted_face_repository import ExtractedFaceRepository
from Repositories.user_extracted_face_repository import UserExtractedFaceRepository
from Repositories.db import get_connection
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

FOLDER_ID = "1C7x4a0-4d84Z6gWxuMQeCHs8VajVxZzE"
SERVICE_ACCOUNT_FILE = "drive-image-access-488104-dfeb01003fac.json"
DELEGATED_USER = "ai@subharti.org"
FACE_EXTRACTOR_OUTPUT_BASE = "extracted_faces"


def detect_faces_for_photo(
    photo_repo: PhotoRepository,
    face_repo: ExtractedFaceRepository,
    extractor: FaceExtractor,
    photo: Photo,
) -> list[ExtractedFace]:

    if photo_repo.is_detection_done(photo.id):
        print("   → Detection already done. Skipping.")
        return []

    faces = extractor.extract_from_photo(photo)

    if not faces:
        print("   → No faces extracted.")
        photo_repo.mark_detection_done(photo.id)
        return []

    print(f"   → Extracted {len(faces)} faces")

    for face in faces:
        face_repo.insert(face)

    photo_repo.mark_detection_done(photo.id)

    return faces


def recognize_faces_for_photo(
    photo_repo: PhotoRepository,
    match_repo: UserExtractedFaceRepository,
    matcher: FaceMatcher,
    photo: Photo,
    faces: list[ExtractedFace],
):

    if photo_repo.is_recognition_done(photo.id):
        print("   → Recognition already done. Skipping.")
        return

    for face in faces:

        matches = matcher.match(
            f"{FACE_EXTRACTOR_OUTPUT_BASE}/{face.photo_id}/face_{face.face_id}"
        )

        if matches:
            print(f"   → {face.face_id} matched {len(matches)} candidates")
            match_repo.insert_matches(face.face_id, matches)
        else:
            print(f"   → {face.face_id} no matches")

    photo_repo.mark_recognition_done(photo.id)


def process_folder(fetcher: GoogleDriveImageFetcher, folder_id: str):

    print(f"\n🚀 Processing folder: {folder_id}")

    conn = get_connection()

    folder_repo = FolderRepository(conn)
    photo_repo = PhotoRepository(conn)
    face_repo = ExtractedFaceRepository(conn)
    match_repo = UserExtractedFaceRepository(conn)

    photos = fetcher.get_images_from_folder(folder_id)

    print(f"📁 Found {len(photos)} photos")

    if not photos:
        return

    extractor = FaceExtractor(fetcher.service, FACE_EXTRACTOR_OUTPUT_BASE)
    matcher = FaceMatcher()

    for photo in photos:

        print(f"\n📝 Processing photo: {photo.id}")

        photo_repo.insert_photo(photo)

        faces = detect_faces_for_photo(
            photo_repo,
            face_repo,
            extractor,
            photo,
        )

        recognize_faces_for_photo(
            photo_repo,
            match_repo,
            matcher,
            photo,
            faces,
        )

    folder_repo.mark_face_detected(folder_id)
    folder_repo.mark_face_recognized(folder_id)

    print("\n✅ Folder processing completed\n")


def process_unprocessed_folders(fetcher: GoogleDriveImageFetcher):

    conn = get_connection()
    folder_repo = FolderRepository(conn)

    folders = folder_repo.get_unprocessed_folders()

    print(f"📂 {len(folders)} folders pending processing")

    for folder_id in folders:
        process_folder(fetcher, folder_id)


def main():

    fetcher = GoogleDriveImageFetcher(
        service_account_file=SERVICE_ACCOUNT_FILE,
        delegated_user=DELEGATED_USER,
    )
    process_folder(fetcher,FOLDER_ID)
    # conn = get_connection()
    # folder_repo = FolderRepository(conn)

    # # discover folders in Drive
    # folders = fetcher.get_leaf_folders_with_images()
    # folder_repo.insert(folders)

    # # process pending folders
    # process_unprocessed_folders(fetcher)


if __name__ == "__main__":
    main()
