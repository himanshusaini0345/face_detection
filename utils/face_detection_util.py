import cv2
import numpy as np
import urllib.request
import os


PROTOTXT = "deploy.prototxt"
CAFFEMODEL = "res10_300x300_ssd_iter_140000.caffemodel"


def _ensure_models():
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


class FaceDetector:
    def __init__(self, confidence_threshold=0.5, tile_size=1500, overlap=200):
        _ensure_models()
        self.net = cv2.dnn.readNetFromCaffe(PROTOTXT, CAFFEMODEL)
        self.confidence_threshold = confidence_threshold
        self.tile_size = tile_size
        self.overlap = overlap

    def extract_faces(self, img):
        """
        Accepts a BGR numpy array (cv2.imread output).
        Returns list of (x, y, w, h) in full-image coordinates.
        Uses tiled detection so large high-res images work correctly.
        """
        img_h, img_w = img.shape[:2]
        step = self.tile_size - self.overlap
        all_boxes = []
        all_confs = []

        for ty in range(0, img_h, step):
            for tx in range(0, img_w, step):
                tx2 = min(tx + self.tile_size, img_w)
                ty2 = min(ty + self.tile_size, img_h)
                tile = img[ty:ty2, tx:tx2]
                t_h, t_w = tile.shape[:2]

                blob = cv2.dnn.blobFromImage(
                    cv2.resize(tile, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0)
                )
                self.net.setInput(blob)
                dets = self.net.forward()

                for i in range(dets.shape[2]):
                    conf = dets[0, 0, i, 2]
                    if conf < self.confidence_threshold:
                        continue
                    box = dets[0, 0, i, 3:7] * np.array([t_w, t_h, t_w, t_h])
                    bx1, by1, bx2, by2 = box.astype(int)
                    gx1 = max(0, tx + bx1)
                    gy1 = max(0, ty + by1)
                    gx2 = min(img_w, tx + bx2)
                    gy2 = min(img_h, ty + by2)
                    all_boxes.append([gx1, gy1, gx2, gy2])
                    all_confs.append(float(conf))

        if not all_boxes:
            return []

        indices = cv2.dnn.NMSBoxes(
            [[b[0], b[1], b[2] - b[0], b[3] - b[1]] for b in all_boxes],
            all_confs,
            score_threshold=self.confidence_threshold,
            nms_threshold=0.3,
        )

        results = []
        for i in indices:
            idx = i[0] if isinstance(i, (list, np.ndarray)) else i
            x1, y1, x2, y2 = all_boxes[idx]
            results.append((x1, y1, x2 - x1, y2 - y1))

        return results

    def extract_best_face(self, img):
        """
        For a solo/portrait image — returns the single highest-confidence
        face crop as a BGR numpy array, or None if no face found.
        """
        img_h, img_w = img.shape[:2]
        blob = cv2.dnn.blobFromImage(
            cv2.resize(img, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0)
        )
        self.net.setInput(blob)
        dets = self.net.forward()

        best_conf, best_box = 0, None
        for i in range(dets.shape[2]):
            conf = dets[0, 0, i, 2]
            if conf > best_conf:
                best_conf = conf
                best_box = dets[0, 0, i, 3:7]

        if best_conf < self.confidence_threshold or best_box is None:
            return None

        box = best_box * np.array([img_w, img_h, img_w, img_h])
        x1, y1, x2, y2 = box.astype(int)
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(img_w, x2), min(img_h, y2)
        return img[y1:y2, x1:x2]
