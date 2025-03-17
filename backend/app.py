# filepath: c:\Users\sardo\OneDrive\Desktop\Classes\dsc148\House-Evaluation\backend\app.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
from dotenv import load_dotenv
import numpy as np
from typing import Dict, Any

load_dotenv()

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# House Input Model
class HouseInput(BaseModel):
    price: float | None = None
    square_footage: float
    bedrooms: int
    bathrooms: int
    age: int
    address: str

# ML Model for House Prediction
class HousePredictor:
    def __init__(self):
        self.base_price = 200000

    def _calculate_base_adjustments(self, features: Dict[str, Any]) -> float:
        adjustments = 0
        if 'square_footage' in features:
            adjustments += features['square_footage'] * 100
        if 'bedrooms' in features:
            adjustments += features['bedrooms'] * 15000
        if 'bathrooms' in features:
            adjustments += features['bathrooms'] * 10000
        if 'age' in features:
            adjustments -= features['age'] * 1000
        return adjustments

    def _calculate_location_multiplier(self, features: Dict[str, Any]) -> float:
        return 1.0

    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        base_adjustments = self._calculate_base_adjustments(features)
        location_multiplier = self._calculate_location_multiplier(features)
        predicted_price = (self.base_price + base_adjustments) * location_multiplier

        is_undervalued = True
        if 'price' in features and features['price'] is not None:
            is_undervalued = predicted_price > features['price']

        star_rating = 5 if is_undervalued else 3

        regression_plot = {
            "x": [i for i in range(5)],
            "y": [
                predicted_price * 0.9,
                predicted_price * 0.95,
                predicted_price,
                predicted_price * 1.05,
                predicted_price * 1.1
            ]
        }

        roc_data = {
            "fpr": [0, 0.2, 0.4, 0.6, 0.8, 1],
            "tpr": [0, 0.4, 0.6, 0.8, 0.9, 1]
        }

        return {
            "predicted_price": predicted_price,
            "valuation": "undervalued" if is_undervalued else "overvalued",
            "star_rating": star_rating,
            "confidence": 0.85,
            "regression_plot": regression_plot,
            "roc_data": roc_data
        }

# Create predictor instance
predictor = HousePredictor()

# API Endpoints
@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "API is running"}

@app.get("/api/geocode")
async def geocode(address: str):
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"

    try:
        response = requests.get(f"{base_url}?address={address}&key={api_key}")
        data = response.json()

        if data["status"] == "OK":
            result = {
                "status": "OK",
                "results": [{
                    "geometry": {
                        "location": data["results"][0]["geometry"]["location"]
                    },
                    "address_components": data["results"][0]["address_components"]
                }]
            }
            return result
        else:
            return {"status": "ERROR", "error": "Location not found"}

    except Exception as e:
        return {"status": "ERROR", "error": str(e)}

@app.get("/api/nearby-places")
async def nearby_places(latitude: float, longitude: float, type: str, radius: int = 3000):
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    base_url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.location,places.formattedAddress,places.types"
    }

    data = {
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": latitude,
                    "longitude": longitude
                },
                "radius": radius
            }
        },
        "includedTypes": [type]
    }

    try:
        response = requests.post(base_url, headers=headers, json=data)
        places_data = response.json()

        if "places" in places_data:
            return {
                "status": "OK",
                "results": places_data["places"]
            }
        else:
            return {
                "status": "OK",
                "results": []
            }

    except Exception as e:
        return {"status": "ERROR", "error": str(e)}

@app.post("/api/predict-house-value")
async def predict_house_value(house_input: HouseInput):
    try:
        # First, get the geocoding data for the address
        geocode_result = await geocode(house_input.address)

        if geocode_result["status"] != "OK":
            raise HTTPException(status_code=400, detail="Could not geocode address")

        # Extract location data
        location = geocode_result["results"][0]["geometry"]["location"]

        # Prepare features for prediction
        features = {
            "price": house_input.price,
            "square_footage": house_input.square_footage,
            "bedrooms": house_input.bedrooms,
            "bathrooms": house_input.bathrooms,
            "age": house_input.age,
            "latitude": location["lat"],
            "longitude": location["lng"]
        }

        # Get prediction
        prediction_result = predictor.predict(features)

        return {
            "status": "OK",
            "prediction": prediction_result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)