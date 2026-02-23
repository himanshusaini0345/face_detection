import cv2


class FaceDetector:
    def __init__(self):
        alg = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.cascade = cv2.CascadeClassifier(alg)

    def extract_faces(self, image_array):
        faces = self.cascade.detectMultiScale(
            image_array,
            scaleFactor=1.05,
            minNeighbors=6,
            minSize=(80, 80),
        )
        return faces
