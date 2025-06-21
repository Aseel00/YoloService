import boto3
import json
import os
import io
import uuid
import time
import requests
from PIL import Image
from ultralytics import YOLO


# === ENV CONFIG ===
REGION = os.environ["REGION"]
BUCKET = os.environ["BUCKET_NAME"]
SQS_URL = os.environ["SQS_URL"]
STORAGE_TYPE = os.getenv("STORAGE_TYPE", "sqlite")
TABLE_NAME = os.environ["DDB_TABLE_NAME"]
POLYBOT_URL = os.environ["POLYBOT_URL"]


UPLOAD_DIR = "uploads/original"
PREDICTED_DIR = "uploads/predicted"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PREDICTED_DIR, exist_ok=True)

# === MODEL ===
model = YOLO("yolov8n.pt")

# === AWS CLIENTS ===
sqs = boto3.client("sqs", region_name=REGION)
s3 = boto3.client("s3", region_name=REGION)

# === STORAGE SETUP ===
from storage.sqlite import SQLiteStorage
from storage.dynamodb import DynamoDBStorage

if STORAGE_TYPE == "dynamodb":
    print("🔁 Using DynamoDBStorage")
    storage = DynamoDBStorage(table_name=TABLE_NAME, region=REGION)
else:
    print("🔁 Using SQLiteStorage")
    storage = SQLiteStorage(db_path="predictions.db")

# === START WORKER ===
print("🚀 YOLO SQS Worker is running...")

while True:
    response = sqs.receive_message(
        QueueUrl=SQS_URL,
        MaxNumberOfMessages=5,
        WaitTimeSeconds=20
    )
    messages = response.get("Messages", [])
    if not messages:
        continue

    for msg in messages:
        try:
            body = json.loads(msg["Body"])

            image_name = body["image_name"]
            chat_id = body["chat_id"]
            prediction_id = body["prediction_id"] # prediction_id = str(uuid.uuid4())
            callback_url = f"{POLYBOT_URL}/predictions/{prediction_id}"

            print(f"🧠 Processing prediction: {prediction_id}")

            # Download image from S3
            s3_object = s3.get_object(Bucket=BUCKET, Key=image_name)
            image_bytes = s3_object["Body"].read()
            image = Image.open(io.BytesIO(image_bytes))

            # Local paths
            input_path = os.path.join(UPLOAD_DIR, f"{prediction_id}.jpg")
            output_path = os.path.join(PREDICTED_DIR, f"{prediction_id}.jpg")

            image.save(input_path)

            # Run YOLO
            try:
                print("🔍 Running YOLO model...", flush=True)
                results = model(input_path, device="cpu")
                print("✅ YOLO model finished.", flush=True)
            except Exception as e:
                print(f"❌ YOLO model failed: {e}", flush=True)
                continue  # skip to next message if detection fails

            try:
                annotated_frame = results[0].plot()
                annotated_image = Image.fromarray(annotated_frame)
                annotated_image.save(output_path)
                print("✅ Annotated image saved.")
                image_saved = True
            except Exception as e:

                print(f"⚠️ Failed to generate/save annotated image: {e}")
                image_saved = False

            if image_saved and os.path.exists(output_path):
                print("📤 Uploading annotated image to S3...")
                s3.upload_file(output_path, BUCKET, f"predicted/{prediction_id}.jpg")
                print("✅ Annotated image uploaded.")
            else:
                print("⚠️ Skipped upload: annotated image missing.")

            # Collect labels and boxes

            # Callback Polybot
            try:
                print("🔽 Postprocessing started...", flush=True)

                labels = []
                for i, box in enumerate(results[0].boxes):
                    label = model.names[int(box.cls[0])]
                    score = float(box.conf[0])
                    bbox = list(map(float, box.xyxy[0].tolist()))

                    labels.append(label)
                    storage.save_detection_object(prediction_id, label, score, bbox, i)

                print("🧾 Saved all detections.", flush=True )

                storage.save_prediction_session(prediction_id, image_name, f"predicted/{prediction_id}.jpg")
                print("🗃️ Saved prediction metadata.", flush=True)

                print(f"📡 Sending callback to: {callback_url}")
                response = requests.post(callback_url, json={
                    "chat_id": chat_id,
                    "prediction_id": prediction_id
                }, timeout=5)

                print(f"📬 Callback response: {response.status_code} {response.text}",flush=True )
                print(f"✅ Done: {prediction_id}", flush=True)

            except Exception as e:
                print(f"❌ Postprocessing failed: {e}", flush=True)


        except Exception as e:
            print(f"❌ Error: {e}")

        # Always delete message
        sqs.delete_message(
            QueueUrl=SQS_URL,
            ReceiptHandle=msg["ReceiptHandle"]
        )

