import numpy as np

from haas.zones import Zone, ZoneLevel, ZoneMap, ZONE_SPEED_LIMITS


def test_zone_contains():
    z = Zone("Z1", ZoneLevel.GREEN, np.array([0.0, 0.0]), np.array([10.0, 10.0]))
    assert z.contains(np.array([5.0, 5.0]))
    assert z.contains(np.array([0.0, 0.0]))   # edge
    assert z.contains(np.array([10.0, 10.0]))  # edge
    assert not z.contains(np.array([11.0, 5.0]))
    assert not z.contains(np.array([-1.0, 5.0]))


def test_zone_center():
    z = Zone("Z1", ZoneLevel.RED, np.array([2.0, 4.0]), np.array([6.0, 8.0]))
    np.testing.assert_array_equal(z.center, [5.0, 8.0])


def test_zonemap_classify_single():
    zones = [Zone("Z1", ZoneLevel.YELLOW, np.array([0.0, 0.0]), np.array([5.0, 5.0]))]
    zm = ZoneMap(zones)
    assert zm.classify(np.array([2.0, 2.0])) == ZoneLevel.YELLOW
    assert zm.classify(np.array([6.0, 6.0])) == ZoneLevel.GREEN  # outside = default


def test_zonemap_most_restrictive_wins():
    zones = [
        Zone("Z1", ZoneLevel.GREEN, np.array([0.0, 0.0]), np.array([10.0, 10.0])),
        Zone("Z2", ZoneLevel.RED, np.array([3.0, 3.0]), np.array([2.0, 2.0])),
    ]
    zm = ZoneMap(zones)
    assert zm.classify(np.array([4.0, 4.0])) == ZoneLevel.RED
    assert zm.classify(np.array([1.0, 1.0])) == ZoneLevel.GREEN


def test_zonemap_speed_limit():
    zones = [Zone("Z1", ZoneLevel.YELLOW, np.array([0.0, 0.0]), np.array([5.0, 5.0]))]
    zm = ZoneMap(zones)
    assert zm.speed_limit(np.array([2.0, 2.0])) == ZONE_SPEED_LIMITS[ZoneLevel.YELLOW]
    assert zm.speed_limit(np.array([6.0, 6.0])) == ZONE_SPEED_LIMITS[ZoneLevel.GREEN]


def test_zonemap_red_speed_is_zero():
    assert ZONE_SPEED_LIMITS[ZoneLevel.RED] == 0.0


def test_zones_containing():
    zones = [
        Zone("Z1", ZoneLevel.GREEN, np.array([0.0, 0.0]), np.array([10.0, 10.0])),
        Zone("Z2", ZoneLevel.RED, np.array([3.0, 3.0]), np.array([2.0, 2.0])),
    ]
    zm = ZoneMap(zones)
    result = zm.zones_containing(np.array([4.0, 4.0]))
    assert len(result) == 2
    result_outside = zm.zones_containing(np.array([1.0, 1.0]))
    assert len(result_outside) == 1
