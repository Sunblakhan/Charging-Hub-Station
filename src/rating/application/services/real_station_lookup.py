from src.rating.application.services.station_lookup import StationLookupInterface

class RealStationLookup(StationLookupInterface):
    def is_station_in_berlin(self, station_label: str) -> bool:
        # Simple rule: treat station as Berlin if label ends with 'Berlin'
        if station_label is None:
            return False
        return station_label.strip().endswith("Berlin")
