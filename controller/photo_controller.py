from fastapi import APIRouter, HTTPException

from pydantic import BaseModel

from service.photo_service import PhotoService


class IndexRequest(BaseModel):
    file_id: str


def router(photo_service: "PhotoService") -> APIRouter:
    r = APIRouter()

    @r.get("/photos")
    def get_photos(userId: str):
        if not userId:
            raise HTTPException(status_code=400, detail="userId is required")
        links = photo_service.find_user_photos(userId)
        return {"webViewLinks": links}

    @r.post("/photos/index")
    def index_file(body: IndexRequest):
        """
        Manually index a single Google Drive image.

        Body: { "file_id": "1A2B3C4D5E6F7G8H9I0J" }

        How to find the file_id:
          Open the file in Google Drive in your browser.
          The URL will look like:
            https://drive.google.com/file/d/<FILE_ID>/view
          Copy the part between /d/ and /view — that is the file_id.
        """
        if not body.file_id.strip():
            raise HTTPException(status_code=400, detail="file_id is required")

        result = photo_service.index_single_file(body.file_id.strip())

        if result["status"] == "error":
            raise HTTPException(status_code=422, detail=result["reason"])

        return result  # {"status": "indexed"|"skipped", ...}

    return r
