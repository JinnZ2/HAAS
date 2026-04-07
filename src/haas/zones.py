"""Zone-based geofencing — green/yellow/red safety zones."""

from dataclasses import dataclass
from enum import Enum

import numpy as np


class ZoneLevel(Enum):
    GREEN = "green"    # Normal operation
    YELLOW = "yellow"  # Reduced speed + elevated monitoring
    RED = "red"        # Full stop / human priority


# Speed multipliers per zone level
ZONE_SPEED_LIMITS: dict[ZoneLevel, float] = {
    ZoneLevel.GREEN: 1.0,
    ZoneLevel.YELLOW: 0.5,
    ZoneLevel.RED: 0.0,
}


@dataclass
class Zone:
    """An axis-aligned rectangular safety zone."""

    id: str
    level: ZoneLevel
    origin: np.ndarray   # bottom-left corner (x, y)
    size: np.ndarray     # (width, height)

    @property
    def center(self) -> np.ndarray:
        return self.origin + self.size / 2

    def contains(self, position: np.ndarray) -> bool:
        """Check whether a 2D position falls inside this zone."""
        return bool(
            np.all(position >= self.origin)
            and np.all(position <= self.origin + self.size)
        )


@dataclass
class ZoneMap:
    """A collection of zones defining the facility layout.

    Zones are evaluated in priority order: RED > YELLOW > GREEN.
    If a position falls in multiple zones, the most restrictive wins.
    """

    zones: list[Zone]

    _PRIORITY = {ZoneLevel.RED: 2, ZoneLevel.YELLOW: 1, ZoneLevel.GREEN: 0}

    def classify(self, position: np.ndarray) -> ZoneLevel:
        """Return the most restrictive zone level for a given position."""
        best = ZoneLevel.GREEN
        for zone in self.zones:
            if zone.contains(position) and self._PRIORITY[zone.level] > self._PRIORITY[best]:
                best = zone.level
        return best

    def speed_limit(self, position: np.ndarray) -> float:
        """Return the speed multiplier [0.0 – 1.0] for a position."""
        return ZONE_SPEED_LIMITS[self.classify(position)]

    def zones_containing(self, position: np.ndarray) -> list[Zone]:
        """Return all zones that contain the given position."""
        return [z for z in self.zones if z.contains(position)]
