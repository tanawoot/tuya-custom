"""Tuya mmWave Radar Custom Quirk for ZHA."""
import math
from typing import Dict

from zigpy.profiles import zgp, zha
from zigpy.quirks import CustomDevice
import zigpy.types as t
from zigpy.zcl.clusters.general import (
    AnalogInput,
    AnalogOutput,
    Basic,
    GreenPowerProxy,
    Groups,
    Ota,
    Scenes,
    Time,
)
from zigpy.zcl.clusters.measurement import IlluminanceMeasurement, OccupancySensing
from zhaquirks.const import (
    DEVICE_TYPE,
    ENDPOINTS,
    INPUT_CLUSTERS,
    OUTPUT_CLUSTERS,
    PROFILE_ID,
)
from zhaquirks.tuya import NoManufacturerCluster, TuyaLocalCluster, TuyaNewManufCluster
from zhaquirks.tuya.mcu import DPToAttributeMapping, TuyaAttributesCluster, TuyaMCUCluster

# ==============================================================================
# CONFIGURATION VARIABLES
# ==============================================================================
MODELS_INFO = [
    ("_TZE204_b8vxct9l", "TS0601"),
    ("_TZE200_ar0slwnd", "TS0601"),
    ("_TZE200_sfiy5tfs", "TS0601"),
    ("_TZE200_mrf6vtua", "TS0601"),
    ("_TZE200_ztc6ggyl", "TS0601"),
    ("_TZE204_ztc6ggyl", "TS0601"),
    ("_TZE204_laokfqwu", "TS0601"),
]

# Config range & resolution
SENSITIVITY_MIN = 1
SENSITIVITY_MAX = 9
SENSITIVITY_RES = 1

RANGE_MIN = 0
RANGE_MAX = 950
RANGE_RES = 10

DETECTION_DELAY_MIN = 0
DETECTION_DELAY_MAX = 20000
DETECTION_DELAY_RES = 100

FADING_TIME_MIN = 0
FADING_TIME_MAX = 200000
FADING_TIME_RES = 1000

# Engineering units (31: Meters, 159: Seconds)
UNIT_METERS = 31
UNIT_SECONDS = 159
# ==============================================================================


class TuyaMmwRadarSelfTest(t.enum8):
    """Mmw radar self test values."""
    TESTING = 0
    TEST_SUCCESS = 1
    TEST_FAILURE = 2
    OTHER = 3
    COMM_FAULT = 4
    RADAR_FAULT = 5


class TuyaOccupancySensing(OccupancySensing, TuyaLocalCluster):
    """Tuya local OccupancySensing cluster."""


class TuyaIlluminanceMeasurement(IlluminanceMeasurement, TuyaLocalCluster):
    """Tuya local IlluminanceMeasurement cluster."""


class TuyaMmwRadarSensitivity(TuyaAttributesCluster, AnalogOutput):
    """AnalogOutput cluster for radar sensitivity."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._update_attribute(self.attributes_by_name["description"].id, "Radar Sensitivity")
        self._update_attribute(self.attributes_by_name["min_present_value"].id, SENSITIVITY_MIN)
        self._update_attribute(self.attributes_by_name["max_present_value"].id, SENSITIVITY_MAX)
        self._update_attribute(self.attributes_by_name["resolution"].id, SENSITIVITY_RES)


class TuyaMmwRadarMinRange(TuyaAttributesCluster, AnalogOutput):
    """AnalogOutput cluster for minimum detection distance."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._update_attribute(self.attributes_by_name["description"].id, "Minimum Detection Distance")
        self._update_attribute(self.attributes_by_name["min_present_value"].id, RANGE_MIN)
        self._update_attribute(self.attributes_by_name["max_present_value"].id, RANGE_MAX)
        self._update_attribute(self.attributes_by_name["resolution"].id, RANGE_RES)
        self._update_attribute(self.attributes_by_name["engineering_units"].id, UNIT_METERS)


class TuyaMmwRadarMaxRange(TuyaAttributesCluster, AnalogOutput):
    """AnalogOutput cluster for maximum detection distance."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._update_attribute(self.attributes_by_name["description"].id, "Maximum Detection Distance")
        self._update_attribute(self.attributes_by_name["min_present_value"].id, RANGE_MIN)
        self._update_attribute(self.attributes_by_name["max_present_value"].id, RANGE_MAX)
        self._update_attribute(self.attributes_by_name["resolution"].id, RANGE_RES)
        self._update_attribute(self.attributes_by_name["engineering_units"].id, UNIT_METERS)


class TuyaMmwRadarDetectionDelay(TuyaAttributesCluster, AnalogOutput):
    """AnalogOutput cluster for motion detection delay."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._update_attribute(self.attributes_by_name["description"].id, "Detection Delay")
        self._update_attribute(self.attributes_by_name["min_present_value"].id, DETECTION_DELAY_MIN)
        self._update_attribute(self.attributes_by_name["max_present_value"].id, DETECTION_DELAY_MAX)
        self._update_attribute(self.attributes_by_name["resolution"].id, DETECTION_DELAY_RES)
        self._update_attribute(self.attributes_by_name["engineering_units"].id, UNIT_SECONDS)


class TuyaMmwRadarFadingTime(TuyaAttributesCluster, AnalogOutput):
    """AnalogOutput cluster for occupancy hold time (fading time)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._update_attribute(self.attributes_by_name["description"].id, "Occupancy Hold Time")
        self._update_attribute(self.attributes_by_name["min_present_value"].id, FADING_TIME_MIN)
        self._update_attribute(self.attributes_by_name["max_present_value"].id, FADING_TIME_MAX)
        self._update_attribute(self.attributes_by_name["resolution"].id, FADING_TIME_RES)
        self._update_attribute(self.attributes_by_name["engineering_units"].id, UNIT_SECONDS)


class TuyaMmwRadarTargetDistance(TuyaAttributesCluster, AnalogInput):
    """AnalogInput cluster for target distance."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._update_attribute(self.attributes_by_name["description"].id, "Target Distance")
        self._update_attribute(self.attributes_by_name["engineering_units"].id, UNIT_METERS)


class TuyaMmwRadarCluster(NoManufacturerCluster, TuyaMCUCluster):
    """Mmw radar cluster."""

    attributes = TuyaMCUCluster.attributes.copy()
    attributes.update(
        {
            0xEF01: ("occupancy", t.uint32_t, True),
            0xEF02: ("sensitivity", t.uint32_t, True),
            0xEF03: ("min_range", t.uint32_t, True),
            0xEF04: ("max_range", t.uint32_t, True),
            0xEF06: ("self_test", TuyaMmwRadarSelfTest, True),
            0xEF09: ("target_distance", t.uint32_t, True),
            0xEF65: ("detection_delay", t.uint32_t, True),
            0xEF66: ("fading_time", t.uint32_t, True),
            0xEF67: ("cli", t.CharacterString, True),
            0xEF68: ("illuminance", t.uint32_t, True),
        }
    )

    dp_to_attribute: Dict[int, DPToAttributeMapping] = {
        1: DPToAttributeMapping(
            TuyaOccupancySensing.ep_attribute,
            "occupancy",
        ),
        2: DPToAttributeMapping(
            TuyaMmwRadarSensitivity.ep_attribute,
            "present_value",
        ),
        3: DPToAttributeMapping(
            TuyaMmwRadarMinRange.ep_attribute,
            "present_value",
            endpoint_id=2,
        ),
        4: DPToAttributeMapping(
            TuyaMmwRadarMaxRange.ep_attribute,
            "present_value",
            endpoint_id=3,
        ),
        6: DPToAttributeMapping(
            TuyaMCUCluster.ep_attribute,
            "self_test",
        ),
        9: DPToAttributeMapping(
            TuyaMmwRadarTargetDistance.ep_attribute,
            "present_value",
            converter=lambda x: float(x) / 100.0,
            endpoint_id=6,
        ),
        101: DPToAttributeMapping(
            TuyaMmwRadarDetectionDelay.ep_attribute,
            "present_value",
            converter=lambda x: x * 100,
            dp_converter=lambda x: x // 100,
            endpoint_id=4,
        ),
        102: DPToAttributeMapping(
            TuyaMmwRadarFadingTime.ep_attribute,
            "present_value",
            converter=lambda x: x * 100,
            dp_converter=lambda x: x // 100,
            endpoint_id=5,
        ),
        103: DPToAttributeMapping(
            TuyaIlluminanceMeasurement.ep_attribute,
            "measured_value",
            converter=lambda x: int(10000 * math.log10(x) + 1) if x and x > 1 else (0 if x == 0 else 1),
        ),
    }

    data_point_handlers = {
        1: "_dp_2_attr_update",
        2: "_dp_2_attr_update",
        3: "_dp_2_attr_update",
        4: "_dp_2_attr_update",
        6: "_dp_2_attr_update",
        9: "_dp_2_attr_update",
        101: "_dp_2_attr_update",
        102: "_dp_2_attr_update",
        103: "_dp_2_attr_update",
    }


class TuyaMmwRadarOccupancy(CustomDevice):
    """Millimeter wave occupancy sensor."""

    signature = {
        "models_info": MODELS_INFO,
        ENDPOINTS: {
            1: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.SMART_PLUG,
                INPUT_CLUSTERS: [
                    Basic.cluster_id,
                    Groups.cluster_id,
                    Scenes.cluster_id,
                    TuyaNewManufCluster.cluster_id,
                ],
                OUTPUT_CLUSTERS: [Time.cluster_id, Ota.cluster_id],
            },
            242: {
                PROFILE_ID: zgp.PROFILE_ID,
                DEVICE_TYPE: zgp.DeviceType.PROXY_BASIC,
                INPUT_CLUSTERS: [],
                OUTPUT_CLUSTERS: [GreenPowerProxy.cluster_id],
            },
        },
    }

    replacement = {
        ENDPOINTS: {
            1: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.OCCUPANCY_SENSOR,
                INPUT_CLUSTERS: [
                    Basic.cluster_id,
                    Groups.cluster_id,
                    Scenes.cluster_id,
                    TuyaMmwRadarCluster,
                    TuyaIlluminanceMeasurement,
                    TuyaOccupancySensing,
                    TuyaMmwRadarSensitivity,
                ],
                OUTPUT_CLUSTERS: [Time.cluster_id, Ota.cluster_id],
            },
            2: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.COMBINED_INTERFACE,
                INPUT_CLUSTERS: [
                    TuyaMmwRadarMinRange,
                ],
                OUTPUT_CLUSTERS: [],
            },
            3: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.COMBINED_INTERFACE,
                INPUT_CLUSTERS: [
                    TuyaMmwRadarMaxRange,
                ],
                OUTPUT_CLUSTERS: [],
            },
            4: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.COMBINED_INTERFACE,
                INPUT_CLUSTERS: [
                    TuyaMmwRadarDetectionDelay,
                ],
                OUTPUT_CLUSTERS: [],
            },
            5: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.COMBINED_INTERFACE,
                INPUT_CLUSTERS: [
                    TuyaMmwRadarFadingTime,
                ],
                OUTPUT_CLUSTERS: [],
            },
            6: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.COMBINED_INTERFACE,
                INPUT_CLUSTERS: [
                    TuyaMmwRadarTargetDistance,
                ],
                OUTPUT_CLUSTERS: [],
            },
        }
    }

# update