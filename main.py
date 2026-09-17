from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from hospitals import get_best_hospital
from routing import run_emergency_routing

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
  return {
      "system": "AI-Based Dynamic Emergency Response System",
      "status": "Operational",
  }


@app.get("/optimize")
def optimize(
    ambulance_lat: float = 28.6139,
    ambulance_lon: float = 77.2090,
    incident_lat: float = 28.6280,
    incident_lon: float = 77.2200,
):
  # 1. Run graph routing
  routing_result = run_emergency_routing(
      ambulance_lat, ambulance_lon, incident_lat, incident_lon
  )

  if "error" in routing_result:
    return routing_result

  # 2. Get optimal hospital dynamically based on live incident proximity and bed load
  assigned_hospital = get_best_hospital(incident_lat, incident_lon)

  return {
      "status": "Success",
      "input_coordinates": {
          "ambulance": {"lat": ambulance_lat, "lon": ambulance_lon},
          "incident": {"lat": incident_lat, "lon": incident_lon},
      },
      "routing_details": routing_result,
      "assigned_hospital": assigned_hospital,
      "recommended_action": (
          f"Ambulance dispatched! Assigned to {assigned_hospital['name']}"
          f" ({assigned_hospital['distance_km']} km away) with"
          f" {assigned_hospital['available_beds']} beds available."
      ),
  }