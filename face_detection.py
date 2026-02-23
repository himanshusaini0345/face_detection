# importing the cv2 library
import cv2

# loading the haar case algorithm file into alg variable
alg = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
# passing the algorithm to OpenCV
haar_cascade = cv2.CascadeClassifier(alg)
# loading the image path into file_name variable
file_name = "0E2A0063.jpg"
# reading the image
img = cv2.imread(file_name, 0)
gray_img = img
# detecting the faces
faces = haar_cascade.detectMultiScale(
    gray_img, scaleFactor=1.05, minNeighbors=6, minSize=(100, 100)
)

i = 0
for x, y, w, h in faces:
    cropped_image = img[y : y + h, x : x + w]
    target_file_name = "stored-faces/" + str(i) + ".jpg"
    cv2.imwrite(target_file_name, cropped_image)
    i = i + 1

print(f"indexed {i} faces from group photo")

# importing the required libraries
import numpy as np
from imgbeddings import imgbeddings
from PIL import Image
import psycopg2
import os

conn = psycopg2.connect("postgresql://postgres:postgres@127.0.0.1:5432/facedb")

for filename in os.listdir("stored-faces"):
    img = Image.open("stored-faces/" + filename)
    ibed = imgbeddings()
    embedding = ibed.to_embeddings(img)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO pictures (file_id, webviewlink, embedding) VALUES (%s, %s, %s)",
        (filename, "", embedding[0].tolist()),
    )
    print(f"inserted: {filename}")
conn.commit()

# ── query — MUST crop face from solo image first ─────────────
file_name = "0E2A0095.jpg"

# Step 1 — detect face in the solo image (same pipeline as indexing)
solo_cv = cv2.imread(file_name, 0)
solo_faces = haar_cascade.detectMultiScale(
    solo_cv, scaleFactor=1.05, minNeighbors=6, minSize=(80, 80)
)

if len(solo_faces) == 0:
    print("No face detected in solo image — trying with full image instead")
    query_img = Image.open(file_name)
else:
    # crop the first (and likely only) face
    x, y, w, h = solo_faces[0]
    cropped_solo = solo_cv[y : y + h, x : x + w]
    query_img = Image.fromarray(cropped_solo)
    query_img.show(title="query_face")  # DEBUG — confirm correct crop
    print(f"detected face in solo image: {w}x{h}px")

# Step 2 — embed the cropped face
ibed = imgbeddings()
embedding = ibed.to_embeddings(query_img)

# Step 3 — query with threshold
# Start at 1.0 (loose) to confirm matches exist, tighten once working
THRESHOLD = 1.0

cur = conn.cursor()
string_representation = "[" + ",".join(str(x) for x in embedding[0].tolist()) + "]"
cur.execute(
    """
    SELECT file_id, embedding <-> %s AS distance
    FROM pictures
    WHERE embedding <-> %s < %s
    ORDER BY distance
    LIMIT 1
    """,
    (string_representation, string_representation, THRESHOLD),
)
rows = cur.fetchall()

if not rows:
    print(f"No match found within threshold {THRESHOLD} — try increasing it")
else:
    for file_id, distance in rows:
        print(f"match: {file_id}  distance: {distance:.4f}")
        from PIL import Image as PILImage

        result = PILImage.open("stored-faces/" + file_id)
        result.show()

cur.close()
