import os

from Models.photo import Photo
from Services.employee_image_downloader import EmployeeImageDownloader
from Services.face_extractor import FaceExtractor
from Services.face_matcher import FaceMatcher
from Services.image_fetcher import GoogleDriveImageFetcher


def main():
    # Download employee images
    # downloader = EmployeeImageDownloader()
    # downloader.download_all_images()

    # Build fetcher
    fetcher = GoogleDriveImageFetcher(
        service_account_file="drive-image-access-488104-dfeb01003fac.json",
        delegated_user="ai@subharti.org"
    )

    photos_raw = fetcher.get_images_from_folder("1l8LTsN1zag-iKhTCH7SAckZRTyuT8o9R")

    photos = [
        Photo(
            photo_id=p["photo_id"],
            photo_link=p["photo_link"],
            folder_name=p["folder_name"],
        )
        for p in photos_raw
    ]

    # Build extractor
    extractor = FaceExtractor(fetcher.service)
    faces = []
    # Process single photo
    for photo in photos:
        faces.extend(extractor.extract_from_photo(photo))

    matcher = FaceMatcher()

    print("\n========== MATCH RESULTS ==========\n")

    for face in faces:
        match_path = matcher.match(face.saved_path)

        face_id = face.face_id  # e.g., photoId_0

        if match_path:
            # Extract employee ID from matched filename
            matched_filename = os.path.basename(match_path)
            employee_id = os.path.splitext(matched_filename)[0]

            print(f"[MATCH] Face {face_id}  --->  Employee {employee_id}")
        else:
            # print(f"[NO MATCH] Face {face_id}  --->  UNKNOWN")
            pass

    print("\n===================================\n")

if __name__ == "__main__":
    main()
