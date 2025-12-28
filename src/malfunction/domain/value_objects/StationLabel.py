from dataclasses import dataclass


class InvalidStationLabel(Exception):
    pass


@dataclass(frozen=True)
class StationLabel:
    value: str

    def __post_init__(self):
        text = self.value.strip()
        if "berlin" not in text.lower():
            raise InvalidStationLabel("Station must be located in Berlin")
        if "," not in text:
            raise InvalidStationLabel("Station label must look like full address")
        object.__setattr__(self, "value", text)
