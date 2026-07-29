# MARTIQ hybrid vision pipeline

MARTIQ does not claim that a generic YOLO model detects every retail event, and it makes no 100% accuracy claim. Camera results are operational signals that require configured ROIs, persistence and human review. Product-loss risk is not labelled as theft detection.

## Engines

| Rule | Engine | What the score means |
|---|---|---|
| `FLOOR_HAZARD` | `OPENCV_HSV_SEGMENTATION` | Controlled blue hazard-mask coverage in the ROI. This is a rule-based demo, not YOLO spill detection. |
| `PROMO_DEPLETION` | `OPENCV_COVERAGE_RULE` | Dark/empty-looking pixel coverage in a controlled promo ROI. |
| `BLOCKED_AISLE` | `OPENCV_CONTOUR_SUPPORT` | Large bright contour coverage in a controlled aisle demo. A production deployment may replace/support this with applicable YOLO object classes. |
| `QUEUE` | `YOLO_PERSON_DETECTION` | Count of pretrained YOLO person detections inside the ROI. It runs only when real local weights are configured. |

No custom spill/hazard model is included because this repository has no labelled spill dataset and no trained custom weights. The application therefore identifies the spill demo as OpenCV rule-based segmentation. Queue processing requires `pip install -r requirements-vision.txt` and `MARTIQ_YOLO_WEIGHTS` pointing to a real local weights file; the application does not download or invent weights and returns a clear processing error when either dependency is absent.

## Lifecycle and evidence

A single positive frame never creates an incident. A rule must remain positive for `trigger_frames`. Opening creates a unified `CAMERA_EVENT` incident in `IN_PROGRESS` and stores the source clip, evidence frame number, source timestamp, ROI, score and engine. A negative signal must remain clear for `clear_frames`; the lifecycle then records `RESOLUTION_CANDIDATE` followed by `AUTO_RESOLVED`, both with an automatic actor. An administrator can reopen the incident or mark the camera event as a false alert, which records a reason and `REJECTED` history entry.

Every camera rule API response exposes engine, ROI, threshold, trigger/clear persistence, current state, last frame time, last event, processing error and approximate FPS. Controlled MP4 processing is not called RTSP. Production RTSP/NVR ingestion, model calibration, drift monitoring and site-specific validation remain separate deployment work.

Generate the reproducible demo inputs with:

```powershell
cd backend
python -m scripts.generate_vision_videos
```

Automated tests generate equivalent temporary videos and independently cover normal, spill/hazard, blocked-aisle, promo-depletion and missing-YOLO-weights queue behaviour.
