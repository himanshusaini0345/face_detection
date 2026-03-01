from Repositories.db import get_connection
from Repositories.user_extracted_face_repository import UserExtractedFaceRepository
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
conn = get_connection()
matched_repo = UserExtractedFaceRepository(conn)

@app.get("/")
def read_root():
    return {"message": "Image Service running"}

@app.get("/images/{id}")
def get_images_by_user_id(id: int):
    print('inside images/')
    return matched_repo.get_by_user_id(id)