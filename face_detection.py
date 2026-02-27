print("inside face_detection.py")
from typing import List
import os
from deepface import DeepFace
import pandas as pd
import cv2
import shutil

# # Face Verification

# result_cosine = DeepFace.verify(
#     img1_path="user_images/JatinKumar_SU202100393.jpg",
#     img2_path="images/jatin1.JPG",
#     model_name="Facenet512",
#     detector_backend="retinaface",
#     distance_metric="cosine",
# )
# print(f"Cosine Distance: {result_cosine['distance']}")

# result_euclidean = DeepFace.verify(
#     img1_path="user_images/JatinKumar_SU202100393.jpg",
#     img2_path="images/jatin1.JPG",
#     model_name="Facenet512",
#     detector_backend="retinaface",
#     distance_metric="euclidean",
# )
# print(f"Euclidean Distance: {result_euclidean['distance']}")


# # Face Recognition

# # 1. Run the search with a more inclusive threshold
# dfs = DeepFace.find(
#     img_path="user_images/JatinKumar_SU202100393.jpg",
#     db_path="images",
#     enforce_detection=False,
#     model_name="Facenet512",
#     detector_backend="retinaface",
#     distance_metric="cosine",
#     threshold=0.5,  # Increased to catch jatin2.JPG and others
# )

# # 2. Extract the results
# if dfs and not dfs[0].empty:
#     all_matches = dfs[0]

#     print(f"🎉 Found {len(all_matches)} total matches in the database:")

#     # This will print all file paths and their distances
#     print(all_matches[["identity", "distance"]])

#     # If you want just a list of the filenames:
#     file_list = all_matches["identity"].tolist()
#     print(f"\nList of files: {file_list}")
# else:
#     print("No matches found.")


# Face extraction
output_dir="extracted_faces"
os.makedirs(output_dir,exist_ok=True)

face_objs = DeepFace.extract_faces(
    img_path="group_images/0E2A5743.jpg",
    detector_backend="retinaface",
    align=True,
    enforce_detection=False,
)

print(f"Detected {len(face_objs)} faces.")

for i, face_obj in enumerate(face_objs):
    # 'face' is a numpy array, but normalized (0 to 1).
    # We need to convert it back to 0-255 pixels for OpenCV to save it.
    face_img=face_obj["face"] * 255
    face_img=face_img.astype("uint8")

    # DeepFace uses RGB, but OpenCV uses BGR. We must swap colors!
    face_img=cv2.cvtColor(face_img,cv2.COLOR_RGB2BGR)

    # Save the face
    filename=f"face_{i}.jpg"
    path=os.path.join(output_dir,filename)
    cv2.imwrite(path,face_img)
    print(f"Saved: {path}(Confidence: {face_obj ['confidence']:2f})")


# # This will detect EVERY face in the group photo
# # and try to match each one against your 'images' folder.
# results = DeepFace.find(
#     img_path="group_images/0E2A0120.jpg",
#     db_path="images",
#     detector_backend="retinaface",
#     model_name="Facenet512",
#     distance_metric="cosine",
#     enforce_detection=False,
# )

# # 'results' will now be a LIST of DataFrames (one for each person in the group)
# for i, person_df in enumerate(results):
#     if not person_df.empty:
#         print(f"Face {i} in the group photo matches: {person_df.iloc[0]['identity']}")

# # 1. Setup and Clean Temp Folder
# TEMP_DIR = "temp"
# if os.path.exists(TEMP_DIR):
#     shutil.rmtree(TEMP_DIR)  # Wipe folder
# os.makedirs(TEMP_DIR)

# GROUP_IMG_PATH = "group_images/0E2A0120.jpg"
# DB_PATH = "images"

# print(f"🚀 Processing: {GROUP_IMG_PATH}")

# # 2. Find all matches in the group photo
# # DeepFace.find returns a list of DataFrames (one per face detected)
# results = DeepFace.find(
#     img_path=GROUP_IMG_PATH,
#     db_path=DB_PATH,
#     detector_backend="retinaface",
#     model_name="Facenet512",
#     distance_metric="cosine",
#     threshold=0.4,
#     enforce_detection=False,
# )

# # 3. Load image for drawing
# img = cv2.imread(GROUP_IMG_PATH)

# print("\n--- Detection Results ---")

# # 4. Iterate through every face found
# for i, df in enumerate(results):
#     face_num = i + 1

#     # Get coordinates of this face (source_x/y/w/h are the same for all rows in one df)
#     # We take coordinates from the first row if available, else we can't draw
#     if not df.empty:
#         # Match Found
#         best_match = df.iloc[0]
#         identity = os.path.basename(best_match["identity"])
#         label = f"{face_num}: {identity}"
#         color = (0, 255, 0)  # Green for matches
#     else:
#         # No Match in DB - We need to get coordinates from the internal detector
#         # If df is empty, find() doesn't easily give back coords of the unmatched face.
#         # To keep it simple, we focus on the matches found in 'results'.
#         continue

#     # Extract coordinates
#     x = int(best_match["source_x"])
#     y = int(best_match["source_y"])
#     w = int(best_match["source_w"])
#     h = int(best_match["source_h"])

#     # 5. Draw on Image (Circle/Ellipse)
#     center = (x + w // 2, y + h // 2)
#     axes = (w // 2, h // 2)
#     cv2.ellipse(img, center, axes, 0, 0, 360, color, 3)

#     # Draw Label Text
#     cv2.putText(img, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

#     # Console Output
#     print(
#         f"Photo {face_num} matched with {identity} (Dist: {best_match['distance']:.3f})"
#     )

# # 6. Save final image
# save_path = os.path.join(TEMP_DIR, "identified_group.jpg")
# cv2.imwrite(save_path, img)

# print(f"\n✅ Done! Check the '{TEMP_DIR}' folder for identified_group.jpg")

import os
import shutil
import cv2
from deepface import DeepFace

# 1. Setup and Clean Temp Folder
TEMP_DIR = "temp"
if os.path.exists(TEMP_DIR):
    shutil.rmtree(TEMP_DIR)
os.makedirs(TEMP_DIR)

GROUP_IMG_PATH = "group_images/0E2A5753.jpg"
DB_PATH = "images"

# 2. Extract ALL faces first to ensure we see everyone
# This ensures we get coordinates even for people who don't match
all_faces = DeepFace.extract_faces(
    img_path=GROUP_IMG_PATH, detector_backend="retinaface", enforce_detection=False
)

# 3. Find matches
results = DeepFace.find(
    img_path=GROUP_IMG_PATH,
    db_path=DB_PATH,
    detector_backend="retinaface",
    model_name="Facenet512",
    distance_metric="cosine",
    threshold=0.3,  # Tightened from 0.4 to 0.3 to avoid blurry false positives
    enforce_detection=False,
)

img = cv2.imread(GROUP_IMG_PATH)
print("\n--- Detection Results ---")

# 4. Iterate through the results
for i, df in enumerate(results):
    face_num = i + 1

    # Get coordinates from the search result
    # (DeepFace.find provides these in the first row even if empty)
    # Note: In some versions, if empty, we pull from extract_faces instead
    face_data = all_faces[i]
    area = face_data["facial_area"]
    x, y, w, h = area["x"], area["y"], area["w"], area["h"]

    if not df.empty:
        best_match = df.iloc[0]
        identity = os.path.basename(best_match["identity"])
        dist = best_match["distance"]
        label = f"P{face_num}: {identity} ({dist:.2f})"
        color = (0, 255, 0)  # Green for Match
        print(f"Photo {face_num} MATCHED: {identity} (Dist: {dist:.3f})")
    else:
        label = f"P{face_num}: UNKNOWN"
        color = (0, 0, 255)  # Red for Unknown
        print(f"Photo {face_num}: No Match Found")

    # Dynamic scaling: 1.0 scale for a 200px wide face
    font_scale = max(0.8, w / 150)
    thickness = max(2, int(font_scale * 2))

    # 5. Draw Ellipse
    center = (x + w // 2, y + h // 2)
    cv2.ellipse(img, center, (w // 2, h // 2), 0, 0, 360, color, thickness)
    # We add a slight black background/shadow to the text for better contrast
    cv2.putText(
        img,
        label,
        (x, y - 15),
        cv2.FONT_HERSHEY_SIMPLEX,
        font_scale,
        (0, 0, 0),
        thickness + 2,
    )  # Shadow
    cv2.putText(
        img, label, (x, y - 15), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness
    )  # Main Text

# 6. Save
save_path = os.path.join(TEMP_DIR, "final_analysis.jpg")
cv2.imwrite(save_path, img)
print(f"\n✅ Saved to {save_path}")
