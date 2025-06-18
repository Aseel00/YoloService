import boto3
import json
from decimal import Decimal
from boto3.dynamodb.conditions import Key
from .base import PredictionStorage

class DynamoDBStorage(PredictionStorage):
    def __init__(self, table_name="yolo_predictions", region="eu-north-1"):
        self.table = boto3.resource("dynamodb", region_name=region).Table(table_name)

    def save_prediction_session(self, uid, original_image, predicted_image):
        self.table.put_item(Item={
            "PK": f"PRED#{uid}",
            "SK": "METADATA",
            "original_image": original_image,
            "predicted_image": predicted_image
        })

    def save_detection_object(self, prediction_uid, label, score, box):
        self.table.put_item(Item={
            "PK": f"PRED#{prediction_uid}",
            "SK": f"OBJECT#{label}",
            "label": label,
            "score": Decimal(str(score)),
            "box": json.dumps(box)
        })

    def get_prediction_by_uid(self, uid):
        res = self.table.query(
            KeyConditionExpression=Key("PK").eq(f"PRED#{uid}")
        )
        metadata = {}
        objects = []
        for item in res["Items"]:
            if item["SK"] == "METADATA":
                metadata = item
            else:
                objects.append(item)

        return {
            "uid": uid,
            "original_image": metadata.get("original_image"),
            "predicted_image": metadata.get("predicted_image"),
            "detection_objects": objects
        }

    def get_predictions_by_label(self, label):
        # This requires a GSI on 'label' to work
        raise NotImplementedError("DynamoDB get_predictions_by_label requires a GSI on label")

    def get_predictions_by_score(self, min_score):
        # This would require a scan or GSI on score
        raise NotImplementedError("DynamoDB get_predictions_by_score requires a GSI on score")
