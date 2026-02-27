from Models.photo import Photo
from Services.employee_image_downloader import EmployeeImageDownloader
from Services.face_extractor import FaceExtractor
from Services.image_fetcher import GoogleDriveImageFetcher


def main():
    # # Build fetcher
    # fetcher = GoogleDriveImageFetcher(
    #     service_account_file="drive-image-access-488104-dfeb01003fac.json",
    #     delegated_user="ai@subharti.org"
    # )

    # photos_raw = fetcher.get_images_from_folder("1Un9v3YuQCQRy5dKz0lDwcWJq4bmpG0tK")

    # photos = [
    #     Photo(
    #         photo_id=p["photo_id"],
    #         photo_link=p["photo_link"],
    #         folder_name=p["folder_name"],
    #     )
    #     for p in photos_raw
    # ]

    # # Build extractor
    # extractor = FaceExtractor(fetcher.service)

    # # Process single photo
    # if photos:
    #     faces = extractor.extract_from_photo(photos[0])

    #     for face in faces:
    #         print(face)

    downloader = EmployeeImageDownloader()
    downloader.download_all_images()


if __name__ == "__main__":
    main()
