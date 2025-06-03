import os
import sys
from fastapi.testclient import TestClient
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app

client = TestClient(app)
IMAGE_PATH = "tests/image/test.jpg"

import pytest

@pytest.fixture(scope="module")
def prediction_uid():
    with open(IMAGE_PATH, "rb") as f:
        response = client.post("/predict", files={"file": f})
    assert response.status_code == 200
    return response.json()["prediction_uid"]

def test_predict_success():
    with open(IMAGE_PATH, "rb") as f:
        response = client.post("/predict", files={"file": f})
    assert response.status_code == 200
    assert "prediction_uid" in response.json()


def test_predict_failure():
    response = client.post("/predict", data={"file": "not-an-image"})
    assert response.status_code in [400, 422]

def test_get_prediction_by_uid_success():
    response = client.get(f"/prediction/{prediction_uid}")
    assert response.status_code == 200
    assert "detection_objects" in response.json()

def test_get_prediction_by_uid_failure():
    response = client.get("/prediction/invalid-uid")
    assert response.status_code == 404

def test_get_predictions_by_label_success():
    response = client.get("/predictions/label/person")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_predictions_by_score_success():
    response = client.get("/predictions/score/0.3")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_prediction_image_success():
    response = client.get(f"/prediction/{prediction_uid}/image", headers={"accept": "image/png"})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/")

def test_get_prediction_image_failure():
    response = client.get("/prediction/invalid-uid/image", headers={"accept": "image/png"})
    assert response.status_code == 404

def test_get_image_success():
    from app import PREDICTED_DIR
    # Grab an existing predicted image from filesystem (you could use glob to list one)
    filename = os.listdir(PREDICTED_DIR)[0]
    response = client.get(f"/image/predicted/{filename}")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/")

def test_get_image_failure():
    response = client.get("/image/original/nonexistent.png")
    assert response.status_code == 404
