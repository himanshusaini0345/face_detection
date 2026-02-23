import cv2
import numpy as np
from imgbeddings import imgbeddings
from PIL import Image
import psycopg2
import os
import urllib.request

SOLO_IMAGE = "0E2A0095.jpg"
STORED_DIR = "stored-faces"
DB_URI = "postgresql://postgres:postgres@127.0.0.1:5432/facedb"

# --- relative threshold ---
# If best match is X and second best is Y,
# accept the match only if it's less than GAP_RATIO of the way to the second best.
# 0.7 means: best must be at least 30% closer than second best.
GAP_RATIO = 0.8

PROTOTXT = "deploy.prototxt"
CAFFEMODEL = "res10_300x300_ssd_iter_140000.caffemodel"

net = cv2.dnn.readNetFromCaffe(PROTOTXT, CAFFEMODEL)

# ── detect face in solo image ────────────────────────────────
img = cv2.imread(SOLO_IMAGE)
h, w = img.shape[:2]
blob = cv2.dnn.blobFromImage(
    cv2.resize(img, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0)
)
net.setInput(blob)
detections = net.forward()

best_i, best_conf = 0, 0
for i in range(detections.shape[2]):
    conf = detections[0, 0, i, 2]
    if conf > best_conf:
        best_conf = conf
        best_i = i

if best_conf < 0.5:
    print("no confident face in solo image — using full image")
    query_img = Image.open(SOLO_IMAGE)
else:
    box = detections[0, 0, best_i, 3:7] * np.array([w, h, w, h])
    x1, y1, x2, y2 = box.astype(int)
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)
    cropped = img[y1:y2, x1:x2]
    query_img = Image.fromarray(cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB))
    query_img.show(title="query_face")
    print(f"query face: {x2-x1}x{y2-y1}px  confidence={best_conf:.2f}")

# ── embed ────────────────────────────────────────────────────
ibed = imgbeddings()
embedding = ibed.to_embeddings(query_img)
string_rep = "[" + ",".join(str(x) for x in embedding[0].tolist()) + "]"

# ── fetch top 5 ──────────────────────────────────────────────
conn = psycopg2.connect(DB_URI)
cur = conn.cursor()
cur.execute(
    """
    SELECT file_id, embedding <-> %s AS distance
    FROM pictures
    ORDER BY distance
    LIMIT 5
    """,
    (string_rep,),
)
rows = cur.fetchall()
cur.close()
conn.close()

if not rows:
    print("DB is empty — run 1_index.py first")
    exit(1)

print("\nTop 5 distances:")
for file_id, dist in rows:
    print(f"  {file_id}  distance={dist:.4f}")

best_file, best_dist = rows[0]

# ── relative gap check ───────────────────────────────────────
if len(rows) == 1:
    # only one entry in DB — accept it
    print(f"\nmatch: {best_file}  distance={best_dist:.4f}")
    Image.open(os.path.join(STORED_DIR, best_file)).show(title=f"match")
else:
    second_dist = rows[1][1]
    gap_ratio = best_dist / second_dist

    print(
        f"\nbest={best_dist:.4f}  second={second_dist:.4f}  ratio={gap_ratio:.2f}  (accept if < {GAP_RATIO})"
    )

    if gap_ratio < GAP_RATIO:
        print(f"match: {best_file}  distance={best_dist:.4f}")
        Image.open(os.path.join(STORED_DIR, best_file)).show(title=f"match_{best_file}")
    else:
        print(f"no confident match — best is not clearly closer than second best")
        print(f"hint: lower GAP_RATIO (currently {GAP_RATIO}) to be more permissive")
