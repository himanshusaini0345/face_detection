# controller/folder_controller.py
#
# Two endpoints:
#
#   GET /browse              → root level (folders + files)
#   GET /browse/{folder_id} → contents of a specific folder
#   GET /photos?userId=123  → face-matched photos with their folder context

from fastapi import APIRouter, HTTPException


def folder_router(folder_repo, photo_service, embedding_generator) -> APIRouter:
    r = APIRouter()

    @r.get("/browse")
    def browse_root():
        """Returns root-level folders and files."""
        return folder_repo.get_children(folder_id=None)

    @r.get("/browse/{folder_id}")
    def browse_folder(folder_id: str):
        """Returns folders and files inside the given folder."""
        name = folder_repo.get_folder_name(folder_id)
        if name is None:
            raise HTTPException(status_code=404, detail="Folder not found")

        children = folder_repo.get_children(folder_id)
        return {
            "current_folder": {"id": folder_id, "name": name},
            **children,  # folders + files keys
        }

    @r.get("/photos")
    def get_photos(userId: str):
        """
        Face search — returns matched files AND the folders they live in
        so the client can reconstruct navigation context.
        """
        if not userId:
            raise HTTPException(status_code=400, detail="userId is required")

        webviewlinks = photo_service.find_user_photos(userId)

        if not webviewlinks:
            return {"folders": [], "files": []}

        # return matched files with their folder context
        return folder_repo.get_matched_folders_and_files(webviewlinks)

    return r
