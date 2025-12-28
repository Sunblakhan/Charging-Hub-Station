from dataclasses import dataclass

@dataclass(frozen=True)
class StationLabel:
    value: str

    def __post_init__(self) -> None:
        # further checks (e.g. must contain 'Berlin') are in aggregate/service
        if not self.value or self.value.strip() == "":
            raise ValueError("Station label must not be empty")
