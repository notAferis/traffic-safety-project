import requests
from PIL import Image
# pyrefly: ignore [missing-import]
from transformers import pipeline


def predict_traffic_incident(image_path: str):
    
    pipe = pipeline("object-detection", model="hilmantm/detr-traffic-accident-detection")
    image_url = image_path

    response = requests.get(image_url, stream=True)
    response.raise_for_status()
    image = Image.open(response.raw)

    predictions = pipe(image)

    return predictions
