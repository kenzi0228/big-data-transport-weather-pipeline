from __future__ import annotations

from typing import Any


def extract_estimated_timetable_delivery(payload: dict[str, Any]) -> list[dict[str, Any]]:
    siri = payload.get("Siri", {})
    service_delivery = siri.get("ServiceDelivery", {})
    deliveries = service_delivery.get("EstimatedTimetableDelivery", [])
    if isinstance(deliveries, list):
        return deliveries
    return []


def normalize_text(value: str | None) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def extract_estimated_journeys(payload: dict[str, Any]) -> list[dict[str, Any]]:
    deliveries = extract_estimated_timetable_delivery(payload)
    all_journeys: list[dict[str, Any]] = []

    for delivery in deliveries:
        journeys = delivery.get("EstimatedJourneyVersionFrame", [])
        if not isinstance(journeys, list):
            continue

        for frame in journeys:
            vehicle_journeys = frame.get("EstimatedVehicleJourney", [])
            if isinstance(vehicle_journeys, list):
                all_journeys.extend(vehicle_journeys)

    return all_journeys


def get_stop_ref_from_estimated_call(call: dict[str, Any]) -> str:
    stop_ref = call.get("StopPointRef")
    if isinstance(stop_ref, dict):
        return str(stop_ref.get("value", "")).strip()
    if isinstance(stop_ref, str):
        return stop_ref.strip()
    return ""


def filter_journeys_by_stop_refs(
    journeys: list[dict[str, Any]],
    target_stop_refs: list[str]
) -> list[dict[str, Any]]:
    target_set = {normalize_text(ref) for ref in target_stop_refs}
    filtered: list[dict[str, Any]] = []

    for journey in journeys:
        estimated_calls = journey.get("EstimatedCalls", {})
        estimated_call_list = estimated_calls.get("EstimatedCall", [])

        if not isinstance(estimated_call_list, list):
            continue

        matched_calls = []
        for call in estimated_call_list:
            stop_ref = get_stop_ref_from_estimated_call(call)
            if normalize_text(stop_ref) in target_set:
                matched_calls.append(call)

        if matched_calls:
            filtered.append(
                {
                    "journey": journey,
                    "matched_calls": matched_calls
                }
            )

    return filtered