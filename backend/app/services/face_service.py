"""Face recognition service using InsightFace."""
import json
import logging
import os
from pathlib import Path
from typing import Any

import cv2
import numpy as np

logger = logging.getLogger(__name__)

_face_app: Any = None


def _get_face_app() -> Any:
    """Lazy-load InsightFace application (downloads model on first call)."""
    global _face_app
    if _face_app is None:
        try:
            import insightface
            from insightface.app import FaceAnalysis

            backend_dir = Path(__file__).resolve().parents[2]
            model_root = backend_dir / ".insightface"
            model_root.mkdir(parents=True, exist_ok=True)
            os.environ["INSIGHTFACE_HOME"] = str(model_root)
            logger.info("Using InsightFace model cache at %s", model_root)

            _face_app = FaceAnalysis(
                name="buffalo_l",
                root=str(model_root),
                providers=["CPUExecutionProvider"],
            )
            _face_app.prepare(ctx_id=0, det_size=(640, 640))
            logger.info("InsightFace buffalo_l model loaded successfully")
        except Exception as exc:
            logger.error("Failed to load InsightFace model: %s", exc)
            raise RuntimeError(f"Face model load failed: {exc}") from exc
    return _face_app


def bytes_to_bgr(image_bytes: bytes) -> np.ndarray:
    """Convert raw image bytes to OpenCV BGR ndarray."""
    arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image bytes")
    return img


def extract_embedding(image_bgr: np.ndarray) -> np.ndarray:
    """
    Detect exactly one face and return its 512-dim embedding.
    Raises ValueError if 0 or more than 1 face detected.
    """
    app = _get_face_app()
    faces = app.get(image_bgr)

    if len(faces) == 0:
        raise ValueError("No face detected in the image. Please retake the photo.")
    if len(faces) > 1:
        raise ValueError(
            f"{len(faces)} faces detected. Please ensure only one person is in frame."
        )

    embedding = faces[0].embedding  # shape: (512,)
    # Normalize to unit vector for cosine similarity
    norm = np.linalg.norm(embedding)
    if norm > 0:
        embedding = embedding / norm
    return embedding


def embedding_to_str(embedding: np.ndarray) -> str:
    """Serialize embedding to JSON string for DB storage."""
    return json.dumps(embedding.tolist())


def str_to_embedding(s: str) -> np.ndarray:
    """Deserialize embedding from JSON string."""
    return np.array(json.loads(s), dtype=np.float32)


def compare_embeddings(e1: np.ndarray, e2: np.ndarray) -> float:
    """Cosine similarity between two unit-normalized embeddings. Range: [-1, 1]."""
    return float(np.dot(e1, e2))


def identify_student(
    query_embedding: np.ndarray,
    students: list,  # list of Student ORM objects with face_embedding attribute
    threshold: float = 0.60,
) -> dict | None:
    """
    Compare query embedding against all stored embeddings.
    Returns best match dict or None if below threshold.
    """
    best_sim = -1.0
    best_student = None

    for student in students:
        if not student.face_embedding:
            continue
        try:
            stored_emb = str_to_embedding(student.face_embedding)
            sim = compare_embeddings(query_embedding, stored_emb)
            if sim > best_sim:
                best_sim = sim
                best_student = student
        except Exception as exc:
            logger.warning("Could not compare embedding for student %s: %s", student.id, exc)
            continue

    if best_student is None or best_sim < threshold:
        return None

    return {
        "student_id": best_student.id,
        "student_name": best_student.name,
        "roll_no": best_student.roll_no,
        "confidence": round(best_sim, 4),
    }
