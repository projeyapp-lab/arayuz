from typing import Protocol, List, Dict


class SerialPortReader(Protocol):
    """Port abstraction for reading parsed values from a serial source."""

    def read_available(self) -> List[Dict]:
        """Return parsed value dictionaries for all available serial lines."""
        ...

