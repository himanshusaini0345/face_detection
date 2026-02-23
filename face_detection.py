# No dlib/face_recognition needed — uses OpenCV DNN detector (deep learning, no compilation)
# uv add opencv-contrib-python

import cv2
import numpy as np
from imgbeddings import imgbeddings
from PIL import Image
import psycopg2
import os
import urllib.request

# ── config ───────────────────────────────────────────────────
GROUP_IMAGE = "0E2A0063.jpg"
SOLO_IMAGE = "0E2A0095.jpg"
STORED_DIR = "stored-faces"
DB_URI = "postgresql://postgres:postgres@127.0.0.1:5432/facedb"
THRESHOLD = 1.0

os.makedirs(STORED_DIR, exist_ok=True)

# ── load OpenCV DNN face detector ────────────────────────────
PROTOTXT = "deploy.prototxt"
CAFFEMODEL = "res10_300x300_ssd_iter_140000.caffemodel"

if not os.path.exists(PROTOTXT):
    print("downloading deploy.prototxt...")
    urllib.request.urlretrieve(
        "https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt",
        PROTOTXT,
    )

if not os.path.exists(CAFFEMODEL):
    print("downloading caffemodel...")
    urllib.request.urlretrieve(
        "https://github.com/opencv/opencv_3rdparty/raw/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel",
        CAFFEMODEL,
    )

net = cv2.dnn.readNetFromCaffe(PROTOTXT, CAFFEMODEL)


def detect_faces(image_path, confidence_threshold=0.5):
    img = cv2.imread(image_path)
    h, w = img.shape[:2]
    blob = cv2.dnn.blobFromImage(
        cv2.resize(img, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0)
    )
    net.setInput(blob)
    detections = net.forward()

    faces = []
    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence < confidence_threshold:
            continue
        box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
        x1, y1, x2, y2 = box.astype(int)
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        faces.append((x1, y1, x2 - x1, y2 - y1))
        print(f"  face confidence: {confidence:.2f}  size: {x2-x1}x{y2-y1}")

    return faces, img


# ── 1. detect & crop faces from group photo ──────────────────
print(f"\ndetecting faces in {GROUP_IMAGE}...")
faces, group_img = detect_faces(GROUP_IMAGE, confidence_threshold=0.5)
print(f"detected {len(faces)} faces")

face_files = []
for i, (x, y, w, h) in enumerate(faces):
    cropped = group_img[y : y + h, x : x + w]
    # convert BGR → RGB so saved JPEGs have correct colours
    cropped_rgb = cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB)
    path = os.path.join(STORED_DIR, f"{i}.jpg")
    cv2.imwrite(path, cv2.cvtColor(cropped_rgb, cv2.COLOR_RGB2BGR))  # imwrite needs BGR
    # DEBUG — show each saved face
    Image.fromarray(cropped_rgb).show(title=f"stored_face_{i}")
    face_files.append(path)
    print(f"saved face {i}: {path}")

# ── 2. embed & insert ────────────────────────────────────────
conn = psycopg2.connect(DB_URI)
ibed = imgbeddings()

for path in face_files:
    img_pil = Image.open(path)
    embedding = ibed.to_embeddings(img_pil)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO pictures (file_id, webviewlink, embedding) VALUES (%s, %s, %s)",
        (os.path.basename(path), "", embedding[0].tolist()),
    )
    print(f"inserted: {path}")

conn.commit()

# ── 3. detect face in solo image & query ─────────────────────
print(f"\ndetecting face in {SOLO_IMAGE}...")
solo_faces, solo_img = detect_faces(SOLO_IMAGE, confidence_threshold=0.5)

if len(solo_faces) == 0:
    print("no face detected in solo image — using full image as fallback")
    query_img = Image.open(SOLO_IMAGE)
else:
    x, y, w, h = solo_faces[0]
    cropped_solo = solo_img[y : y + h, x : x + w]
    cropped_solo_rgb = cv2.cvtColor(cropped_solo, cv2.COLOR_BGR2RGB)
    query_img = Image.fromarray(cropped_solo_rgb)
    query_img.show(title="query_face")  # DEBUG
    print(f"query face: {w}x{h}px")

# ── 4. embed & search ────────────────────────────────────────
embedding = ibed.to_embeddings(query_img)
string_rep = "[" + ",".join(str(x) for x in embedding[0].tolist()) + "]"

cur = conn.cursor()
cur.execute(
    """
    SELECT file_id, embedding <-> %s AS distance
    FROM pictures
    WHERE embedding <-> %s < %s
    ORDER BY distance
    LIMIT 1
    """,
    (string_rep, string_rep, THRESHOLD),
)
rows = cur.fetchall()

if not rows:
    print(f"no match within threshold {THRESHOLD} — try increasing it")
else:
    for file_id, distance in rows:
        print(f"match: {file_id}  distance: {distance:.4f}")
        result = Image.open(os.path.join(STORED_DIR, file_id))
        result.show()

cur.close()
conn.close()
