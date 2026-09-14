"""Tuya mmWave Radar Custom Quirk for ZHA."""
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
# CONFIGURATION & USER-FRIENDLY DEFAULTS
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

# Sensitivity (1-9, Default 7)
SENSITIVITY_MIN = 1
SENSITIVITY_MAX = 9
SENSITIVITY_RES = 1
SENSITIVITY_DEF = 7

# Min Range (0.0m - 5.0m, Default 0.1m)
MIN_RANGE_MIN_M = 0.0
MIN_RANGE_MAX_M = 5.0
MIN_RANGE_RES_M = 0.1
MIN_RANGE_DEF_M = 0.1

# Max Range (0.5m - 9.5m, Default 5.0m)
MAX_RANGE_MIN_M = 0.5
MAX_RANGE_MAX_M = 9.5
MAX_RANGE_RES_M = 0.1
MAX_RANGE_DEF_M = 5.0

# Detection Delay (0.0s - 10.0s, Default 0.1s)
DET_DELAY_MIN_S = 0.0
DET_DELAY_MAX_S = 10.0
DET_DELAY_RES_S = 0.1
DET_DELAY_DEF_S = 0.1

# Occupancy Hold Time / Fading Time (5s - 300s, Default 30s)
FADING_MIN_S = 5
FADING_MAX_S = 300
FADING_RES_S = 1
FADING_DEF_S = 30

# ZCL Engineering Units
UNIT_METERS = 31
UNIT_SECONDS = 159
UNIT_NONE = 62
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

    icon = "mdi:radar"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._update_attribute(self.attributes_by_name["description"].id, "Radar Sensitivity")
        self._update_attribute(self.attributes_by_name["min_present_value"].id, SENSITIVITY_MIN)
        self._update_attribute(self.attributes_by_name["max_present_value"].id, SENSITIVITY_MAX)
        self._update_attribute(self.attributes_by_name["resolution"].id, SENSITIVITY_RES)
        self._update_attribute(self.attributes_by_name["present_value"].id, SENSITIVITY_DEF)
        self._update_attribute(self.attributes_by_name["engineering_units"].id, UNIT_NONE)


class TuyaMmwRadarMinRange(TuyaAttributesCluster, AnalogOutput):
    """AnalogOutput cluster for minimum detection distance (in Meters)."""

    icon = "mdi:map-marker-distance"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._update_attribute(self.attributes_by_name["description"].id, "Minimum Distance")
        self._update_attribute(self.attributes_by_name["min_present_value"].id, MIN_RANGE_MIN_M)
        self._update_attribute(self.attributes_by_name["max_present_value"].id, MIN_RANGE_MAX_M)
        self._update_attribute(self.attributes_by_name["resolution"].id, MIN_RANGE_RES_M)
        self._update_attribute(self.attributes_by_name["present_value"].id, MIN_RANGE_DEF_M)
        self._update_attribute(self.attributes_by_name["engineering_units"].id, UNIT_METERS)


class TuyaMmwRadarMaxRange(TuyaAttributesCluster, AnalogOutput):
    """AnalogOutput cluster for maximum detection distance (in Meters)."""

    icon = "mdi:arrow-expand-horizontal"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._update_attribute(self.attributes_by_name["description"].id, "Maximum Distance")
        self._update_attribute(self.attributes_by_name["min_present_value"].id, MAX_RANGE_MIN_M)
        self._update_attribute(self.attributes_by_name["max_present_value"].id, MAX_RANGE_MAX_M)
        self._update_attribute(self.attributes_by_name["resolution"].id, MAX_RANGE_RES_M)
        self._update_attribute(self.attributes_by_name["present_value"].id, MAX_RANGE_DEF_M)
        self._update_attribute(self.attributes_by_name["engineering_units"].id, UNIT_METERS)


class TuyaMmwRadarDetectionDelay(TuyaAttributesCluster, AnalogOutput):
    """AnalogOutput cluster for motion detection delay (in Seconds)."""

    icon = "mdi:timer-sand"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._update_attribute(self.attributes_by_name["description"].id, "Detection Delay")
        self._update_attribute(self.attributes_by_name["min_present_value"].id, DET_DELAY_MIN_S)
        self._update_attribute(self.attributes_by_name["max_present_value"].id, DET_DELAY_MAX_S)
        self._update_attribute(self.attributes_by_name["resolution"].id, DET_DELAY_RES_S)
        self._update_attribute(self.attributes_by_name["present_value"].id, DET_DELAY_DEF_S)
        self._update_attribute(self.attributes_by_name["engineering_units"].id, UNIT_SECONDS)


class TuyaMmwRadarFadingTime(TuyaAttributesCluster, AnalogOutput):
    """AnalogOutput cluster for occupancy hold time / fading time (in Seconds)."""

    icon = "mdi:clock-end"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._update_attribute(self.attributes_by_name["description"].id, "Occupancy Hold Time")
        self._update_attribute(self.attributes_by_name["min_present_value"].id, FADING_MIN_S)
        self._update_attribute(self.attributes_by_name["max_present_value"].id, FADING_MAX_S)
        self._update_attribute(self.attributes_by_name["resolution"].id, FADING_RES_S)
        self._update_attribute(self.attributes_by_name["present_value"].id, FADING_DEF_S)
        self._update_attribute(self.attributes_by_name["engineering_units"].id, UNIT_SECONDS)


class TuyaMmwRadarTargetDistance(TuyaAttributesCluster, AnalogInput):
    """AnalogInput cluster for target distance (in Meters)."""

    icon = "mdi:human-handsdown"

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
        # Occupancy Inversion (1 -> 0, 0 -> 1)
        1: DPToAttributeMapping(
            TuyaOccupancySensing.ep_attribute,
            "occupancy",
            converter=lambda x: 0 if x == 1 else 1,
        ),
        # Sensitivity (1-9)
        2: DPToAttributeMapping(
            TuyaMmwRadarSensitivity.ep_attribute,
            "present_value",
            converter=lambda x: int(x) if x is not None else SENSITIVITY_DEF,
            dp_converter=lambda x: int(x),
        ),
        # Min Range (cm -> m)
        3: DPToAttributeMapping(
            TuyaMmwRadarMinRange.ep_attribute,
            "present_value",
            converter=lambda x: round(float(x) / 100.0, 2) if x is not None else MIN_RANGE_DEF_M,
            dp_converter=lambda x: int(round(x * 100)),
            endpoint_id=2,
        ),
        # Max Range (cm -> m)
        4: DPToAttributeMapping(
            TuyaMmwRadarMaxRange.ep_attribute,
            "present_value",
            converter=lambda x: round(float(x) / 100.0, 2) if x is not None else MAX_RANGE_DEF_M,
            dp_converter=lambda x: int(round(x * 100)),
            endpoint_id=3,
        ),
        # Self Test
        6: DPToAttributeMapping(
            TuyaMCUCluster.ep_attribute,
            "self_test",
        ),
        # Target Distance (cm -> m)
        9: DPToAttributeMapping(
            TuyaMmwRadarTargetDistance.ep_attribute,
            "present_value",
            converter=lambda x: round(float(x) / 100.0, 2) if x is not None else 0.0,
        ),
        # Detection Delay (1/10s -> s)
        101: DPToAttributeMapping(
            TuyaMmwRadarDetectionDelay.ep_attribute,
            "present_value",
            converter=lambda x: round(float(x) / 10.0, 1) if x is not None else DET_DELAY_DEF_S,
            dp_converter=lambda x: int(round(x * 10)),
            endpoint_id=4,
        ),
        # Occupancy Hold Time / Fading Time (Direct Seconds)
        102: DPToAttributeMapping(
            TuyaMmwRadarFadingTime.ep_attribute,
            "present_value",
            converter=lambda x: int(x) if x is not None else FADING_DEF_S,
            dp_converter=lambda x: int(x),
            endpoint_id=5,
        ),
        # Illuminance
        103: DPToAttributeMapping(
            TuyaIlluminanceMeasurement.ep_attribute,
            "measured_value",
            converter=lambda x: int(x) if x is not None else 0,
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
                    TuyaMmwRadarTargetDistance,
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
        }
    }