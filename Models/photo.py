from dataclasses import dataclass


@dataclass
class Photo:
    photo_id: str
    photo_link: str
    folder_name: str