import os

from Models.photo import Photo
from Services.employee_image_downloader import EmployeeImageDownloader
from Services.face_extractor import FaceExtractor
from Services.face_matcher import FaceMatcher
from Services.image_fetcher import GoogleDriveImageFetcher
from Repositories.photo_repository import PhotoRepository
from Repositories.extracted_face_repository import ExtractedFaceRepository
from Repositories.user_extracted_face_repository import UserExtractedFaceRepository
from Repositories.db import get_connection


FOLDER_ID = "1C7x4a0-4d84Z6gWxuMQeCHs8VajVxZzE"
SERVICE_ACCOUNT_FILE = "drive-image-access-488104-dfeb01003fac.json"
DELEGATED_USER = "ai@subharti.org"
FACE_EXTRACTOR_OUTPUT_BASE = "extracted_faces"

def process_folder(fetcher:GoogleDriveImageFetcher,folder_id: str):
    print(f"\n🚀 Processing folder: {folder_id}")

    # DB connection
    conn = get_connection()

    photo_repo = PhotoRepository(conn)
    face_repo = ExtractedFaceRepository(conn)
    match_repo = UserExtractedFaceRepository(conn)

    # 1️⃣ Fetch photos
    photos = fetcher.get_images_from_folder(folder_id)
    print(f"📁 Found {len(photos)} photos")

    if not photos:
        return

    extractor = FaceExtractor(fetcher.service, FACE_EXTRACTOR_OUTPUT_BASE)
    matcher = FaceMatcher()

    for photo in photos:

        print(f"\n📝 Processing photo: {photo.id}")

        if photo_repo.is_processed(photo.id):
            print("   → Already processed. Skipping.")
            continue

        # Insert photo record (acts like tracking)
        photo_repo.insert_photo(photo)

        faces = extractor.extract_from_photo(photo)
        if faces is None:
            print("   → Extraction failed. Skipping mark_processed.")
            continue

        print(f"   → Extracted {len(faces)} faces")

        for face in faces:

            # Insert extracted face
            face_repo.insert(face)

            matches = matcher.match(f"{FACE_EXTRACTOR_OUTPUT_BASE}/{face.photo_id}/face_{face.face_id}")

            if matches:
                print(f"   → {face.face_id} matched {len(matches)} candidates")

                match_repo.insert_matches(face.face_id, matches)

            else:
                print(f"   → {face.face_id} no matches")

        # Mark photo as processed
        photo_repo.mark_processed(photo.id)

    print("\n✅ Folder processing completed\n")

def download_employee_images():
    downloader = EmployeeImageDownloader()
    downloader.download_all_images()


def get_user_images(user_id):
    conn = get_connection()
    match_repo = UserExtractedFaceRepository(conn)

    print(f"\n📊 Matches for User: {user_id}\n")

    photos = match_repo.get_by_user_id(user_id)
    conn.close()
    return photos


def main():
    # fetcher = GoogleDriveImageFetcher(
    #     service_account_file=SERVICE_ACCOUNT_FILE,
    #     delegated_user=DELEGATED_USER,
    # )
    photos = get_user_images("2330")
    for photo in photos:
        print(photo.webview_link)


if __name__ == "__main__":
    main()

    # photos = fetcher.get_images_from_folder(FOLDER_ID, 1)
    # for photo in photos:
    #     print(photo)

    # folders = fetcher.get_folder_by_name("DESIGN CASTLE 2025")
    # for folder in folders:
    #     print(folder)

    # process_folder(fetcher,FOLDER_ID)
    # print(fetcher.count_images_in_folder(FOLDER_ID))
    # get_images_all()

    # conn = get_connection()
    # matched_repo = UserExtractedFaceRepository(conn)
    # result = matched_repo.get_by_user_id(1008)
    # print(result)
