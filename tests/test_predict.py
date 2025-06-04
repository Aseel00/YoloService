import os
import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from app import app

client = TestClient(app)

# --- Helpers ---
def generate_test_image(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img = Image.new("RGB", (100, 100), color="blue")
    img.save(path)

# --- Fixtures ---
@pytest.fixture(scope="module")
def prediction_uid():
    image_path = "tests/image/test.jpg"
    if not os.path.exists(image_path):
        generate_test_image(image_path)

    with open(image_path, "rb") as f:
        response = client.post("/predict", files={"file": f})
    assert response.status_code == 200
    return response.json()["prediction_uid"]

# --- Tests ---
def test_predict_success():
    with open("tests/image/test.jpg", "rb") as f:
        response = client.post("/predict", files={"file": f})
    assert response.status_code == 200
    assert "prediction_uid" in response.json()

def test_predict_failure():
    response = client.post("/predict", data={"file": "not-an-image"})
    assert response.status_code in [400, 422]

def test_get_prediction_by_uid_success(prediction_uid):
    response = client.get(f"/prediction/{prediction_uid}")
    assert response.status_code == 200
    assert "detection_objects" in response.json()

def test_get_prediction_by_uid_failure():
    response = client.get("/prediction/invalid-uid")
    assert response.status_code == 404

def test_get_predictions_by_label_success():
    response = client.get("/predictions/label/person")
    assert response.status_code == 200

def test_get_predictions_by_score_success():
    response = client.get("/predictions/score/0.3")
    assert response.status_code == 200

def test_get_prediction_image_success(prediction_uid):
    response = client.get(f"/prediction/{prediction_uid}/image", headers={"accept": "image/png"})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/")

def test_get_prediction_image_failure():
    response = client.get("/prediction/invalid-uid/image", headers={"accept": "image/png"})
    assert response.status_code == 404

def test_get_image_success(prediction_uid):
    from app import PREDICTED_DIR
    files = os.listdir(PREDICTED_DIR)
    assert files, "No predicted images found"
    filename = files[0]
    response = client.get(f"/image/predicted/{filename}")
    assert response.status_code == 200

def test_get_image_failure():
    response = client.get("/image/original/nonexistent.png")
    assert response.status_code == 404
