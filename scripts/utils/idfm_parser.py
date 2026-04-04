from __future__ import annotations

from typing import Any


def safe_get(data: dict[str, Any], path: list[str], default: Any = None) -> Any:
    current: Any = data
    for key in path:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
        if current is None:
            return default
    return current


def normalize_stop_visits(raw_payload: dict[str, Any], monitoring_ref: str, stop_label: str) -> list[dict[str, Any]]:
    delivery = safe_get(
        raw_payload,
        [
            "Siri",
            "ServiceDelivery",
            "StopMonitoringDelivery"
        ],
        []
    )

    if not isinstance(delivery, list) or not delivery:
        return []

    first_delivery = delivery[0]
    monitored_visits = first_delivery.get("MonitoredStopVisit", [])

    normalized: list[dict[str, Any]] = []

    for visit in monitored_visits:
        monitored_journey = visit.get("MonitoredVehicleJourney", {})

        line_ref = monitored_journey.get("LineRef")
        destination_name = monitored_journey.get("DestinationName")

        monitored_call = monitored_journey.get("MonitoredCall", {})
        aimed_arrival_time = monitored_call.get("AimedArrivalTime")
        expected_arrival_time = monitored_call.get("ExpectedArrivalTime")
        aimed_departure_time = monitored_call.get("AimedDepartureTime")
        expected_departure_time = monitored_call.get("ExpectedDepartureTime")

        normalized.append(
            {
                "monitoring_ref": monitoring_ref,
                "stop_label": stop_label,
                "line_ref": line_ref,
                "destination_name": destination_name,
                "aimed_arrival_time": aimed_arrival_time,
                "expected_arrival_time": expected_arrival_time,
                "aimed_departure_time": aimed_departure_time,
                "expected_departure_time": expected_departure_time,
                "raw_visit": visit,
            }
        )

    return normalized