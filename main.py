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


FOLDER_ID = "1l8LTsN1zag-iKhTCH7SAckZRTyuT8o9R"


def process_folder(folder_id: str):
    print(f"\n🚀 Processing folder: {folder_id}")

    # DB connection
    conn = get_connection()

    photo_repo = PhotoRepository(conn)
    face_repo = ExtractedFaceRepository(conn)
    match_repo = UserExtractedFaceRepository(conn)

    # 1️⃣ Fetch photos
    fetcher = GoogleDriveImageFetcher(
        service_account_file="drive-image-access-488104-dfeb01003fac.json",
        delegated_user="ai@subharti.org",
    )

    photos_raw = fetcher.get_images_from_folder(folder_id)

    photos = [
        Photo(
            photo_id=p["photo_id"],
            photo_link=p["photo_link"],
            folder_name=p["folder_name"],
        )
        for p in photos_raw
    ]

    print(f"📁 Found {len(photos)} photos")

    if not photos:
        return

    extractor = FaceExtractor(fetcher.service)
    matcher = FaceMatcher()

    for photo in photos:

        print(f"\n📝 Processing photo: {photo.photo_id}")

        # Insert photo record (acts like tracking)
        photo_repo.insert_photo(photo)

        # Skip if already processed (optional future improvement)
        # if photo_repo.is_processed(photo.photo_id):
        #     continue

        faces = extractor.extract_from_photo(photo)
        print(f"   → Extracted {len(faces)} faces")

        for face in faces:

            # Insert extracted face
            face_repo.insert(face)

            matches = matcher.match(face.saved_path)

            if matches:
                print(f"   → {face.face_id} matched {len(matches)} candidates")

                match_repo.insert_matches(face.face_id, matches)

            else:
                print(f"   → {face.face_id} no matches")

        # Mark photo as processed
        photo_repo.mark_processed(photo.photo_id)

    print("\n✅ Folder processing completed\n")

def download_employee_images():
    downloader = EmployeeImageDownloader()
    downloader.download_all_images()

def main():
    download_employee_images()
    process_folder(FOLDER_ID)

if __name__ == "__main__":
    main()
