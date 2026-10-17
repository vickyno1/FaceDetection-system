# Pretrained Computer Vision Models

This directory contains the pretrained ONNX models required by the **Student Attendance Management System**:

1. **YuNet Face Detector** (`face_detection_yunet_2023mar.onnx`)
2. **SFace Face Recognizer** (`face_recognition_sface_2021dec.onnx`)

---

## Model Specifications

| Property | Face Detector (YuNet) | Face Recognizer (SFace) |
| :--- | :--- | :--- |
| **Filename** | `face_detection_yunet_2023mar.onnx` | `face_recognition_sface_2021dec.onnx` |
| **Official Source** | [OpenCV Zoo YuNet](https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet) | [OpenCV Zoo SFace](https://github.com/opencv/opencv_zoo/tree/main/models/face_recognition_sface) |
| **Framework** | ONNX Runtime / OpenCV DNN | ONNX Runtime / OpenCV DNN |
| **Input Format** | BGR Image $(H \times W \times 3)$ | Aligned & Cropped BGR Face $(112 \times 112 \times 3)$ |
| **Output Format** | Bounding box $(x, y, w, h)$, 5 facial landmarks, confidence score | 128-dimensional floating point feature vector |
| **File Size** | $\approx 232.6\text{ KB}$ | $\approx 38.7\text{ MB}$ |
| **SHA-256** | `8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4` | Verified Git LFS Release Asset |

---

## Automated Download

To download or re-verify the models automatically, run:

```bash
python backend/models/download_models.py
```

---

## Direct Download Links (Git LFS)

If downloading manually via `curl` or browser, ensure you download the binary payload rather than the Git LFS text pointer:

- **YuNet**:  
  `https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx`
- **SFace**:  
  `https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx`

---

## Pipeline Integration

- **Detection**: `cv2.FaceDetectorYN.create(model_path, "", input_size=(w, h), score_threshold=0.8, nms_threshold=0.3)`
- **Alignment & Crop**: `recognizer.alignCrop(image, detected_face)`
- **Embedding Extraction**: `recognizer.feature(aligned_face)` produces a 128-D embedding vector.
- **Comparison Metric**: Cosine similarity:
  $$\text{Cosine Similarity}(u, v) = \frac{u \cdot v}{\|u\|_2 \|v\|_2}$$
  The default match threshold is calibrated at $0.380$ (with minimum top-2 candidate margin of $0.080$).
