class StationLookupInterface:
    def is_station_in_berlin(self, station_label: str) -> bool:
        """
        Return True if the given station label represents a Berlin station.
        Concrete implementations (real or fake) must override this.
        """
        raise NotImplementedError
