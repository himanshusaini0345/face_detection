import cv2
import numpy as np
from imgbeddings import imgbeddings
from PIL import Image
import psycopg2
import os
import urllib.request

GROUP_IMAGE = "0E2A0063.jpg"
STORED_DIR = "stored-faces"
DB_URI = "postgresql://postgres:postgres@127.0.0.1:5432/facedb"

os.makedirs(STORED_DIR, exist_ok=True)

PROTOTXT = "deploy.prototxt"
CAFFEMODEL = "res10_300x300_ssd_iter_140000.caffemodel"

if not os.path.exists(PROTOTXT):
    urllib.request.urlretrieve(
        "https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt",
        PROTOTXT,
    )
if not os.path.exists(CAFFEMODEL):
    urllib.request.urlretrieve(
        "https://github.com/opencv/opencv_3rdparty/raw/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel",
        CAFFEMODEL,
    )

net = cv2.dnn.readNetFromCaffe(PROTOTXT, CAFFEMODEL)


def detect_faces_tiled(img, tile_size=1500, overlap=200, confidence_threshold=0.5):
    """
    Splits a large image into overlapping tiles and runs DNN on each.
    Merges results and removes duplicates with NMS.
    """
    img_h, img_w = img.shape[:2]
    step = tile_size - overlap
    all_boxes = []  # (x1, y1, x2, y2)
    all_confs = []

    for y in range(0, img_h, step):
        for x in range(0, img_w, step):
            x2 = min(x + tile_size, img_w)
            y2 = min(y + tile_size, img_h)
            tile = img[y:y2, x:x2]
            t_h, t_w = tile.shape[:2]

            blob = cv2.dnn.blobFromImage(
                cv2.resize(tile, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0)
            )
            net.setInput(blob)
            dets = net.forward()

            for i in range(dets.shape[2]):
                conf = dets[0, 0, i, 2]
                if conf < confidence_threshold:
                    continue
                box = dets[0, 0, i, 3:7] * np.array([t_w, t_h, t_w, t_h])
                bx1, by1, bx2, by2 = box.astype(int)
                # translate back to full image coordinates
                gx1 = x + bx1
                gy1 = y + by1
                gx2 = x + bx2
                gy2 = y + by2
                # clamp
                gx1, gy1 = max(0, gx1), max(0, gy1)
                gx2, gy2 = min(img_w, gx2), min(img_h, gy2)
                all_boxes.append([gx1, gy1, gx2, gy2])
                all_confs.append(float(conf))

    if not all_boxes:
        return []

    # Non-Maximum Suppression — removes duplicate detections from overlapping tiles
    boxes_np = np.array(all_boxes, dtype=np.float32)
    confs_np = np.array(all_confs, dtype=np.float32)
    indices = cv2.dnn.NMSBoxes(
        [[b[0], b[1], b[2] - b[0], b[3] - b[1]] for b in all_boxes],  # (x,y,w,h) format
        all_confs,
        score_threshold=confidence_threshold,
        nms_threshold=0.3,
    )

    results = []
    for i in indices:
        idx = i[0] if isinstance(i, (list, np.ndarray)) else i
        x1, y1, x2, y2 = all_boxes[idx]
        results.append((x1, y1, x2 - x1, y2 - y1))
        print(
            f"  face: conf={all_confs[idx]:.2f}  pos=({x1},{y1})  size={x2-x1}x{y2-y1}"
        )

    return results


# ── detect ───────────────────────────────────────────────────
img = cv2.imread(GROUP_IMAGE)
if img is None:
    print(f"ERROR: could not read {GROUP_IMAGE}")
    exit(1)

print(f"image size: {img.shape[1]}x{img.shape[0]}")
print("detecting faces (tiled)...")

faces = detect_faces_tiled(img, tile_size=1500, overlap=200, confidence_threshold=0.5)
print(f"\ndetected {len(faces)} faces total")

if len(faces) == 0:
    print("still no faces — check the image has clear frontal faces")
    exit(1)

# ── clear old data ───────────────────────────────────────────
conn = psycopg2.connect(DB_URI)
cur = conn.cursor()
cur.execute("DELETE FROM pictures")
conn.commit()
for f in os.listdir(STORED_DIR):
    os.remove(os.path.join(STORED_DIR, f))
print("cleared old data")

# ── save + embed + insert ────────────────────────────────────
ibed = imgbeddings()

for i, (x, y, w, h) in enumerate(faces):
    cropped = img[y : y + h, x : x + w]
    path = os.path.join(STORED_DIR, f"{i}.jpg")
    cv2.imwrite(path, cropped)

    pil_img = Image.open(path)
    pil_img.show(title=f"face_{i}")  # DEBUG
    embedding = ibed.to_embeddings(pil_img)

    cur.execute(
        "INSERT INTO pictures (file_id, webviewlink, embedding) VALUES (%s, %s, %s)",
        (f"{i}.jpg", "", embedding[0].tolist()),
    )
    print(f"saved + inserted: {path}")

conn.commit()
conn.close()
print(f"\ndone — indexed {len(faces)} faces")
