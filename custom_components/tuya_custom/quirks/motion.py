
"""ZHA custom quirk for Tuya TS0601 _TZE204_b8vxct9l.

Device:
    GIRIER / Lincukoo TS0601
    24 GHz mmWave presence sensor
    AC / mains powered
    Relay + illuminance sensor

Known Tuya datapoints:

    DP 1   - Presence
    DP 20  - Illuminance
    DP 13  - Installation height
    DP 16  - Radar sensitivity
    DP 103 - Fading time
    DP 102 - Radar switch
    DP 101 - LED indicator
    DP 104 - Relay switch
    DP 106 - Relay mode
    DP 107 - Radar mode

No battery.
"""

from typing import Dict

from zigpy.profiles import zha
from zigpy.zcl.clusters.general import Basic, Groups, Ota, Scenes, Time
from zigpy.zcl.clusters.measurement import IlluminanceMeasurement
from zigpy.zcl.clusters.security import IasZone
from zigpy.quirks import CustomDevice

from zhaquirks.tuya.mcu import DPToAttributeMapping, TuyaMCUCluster


class TuyaMotionCluster(TuyaMCUCluster):
    """Tuya MCU cluster for TS0601 mmWave motion sensor."""

    dp_to_attribute: Dict[int, DPToAttributeMapping] = {
        # ---------------------------------------------------------
        # DP 1 - Presence
        #
        # Device reports:
        #   0 = no presence
        #   1 = presence detected
        # ---------------------------------------------------------
        1: DPToAttributeMapping(
            IasZone.ep_attribute,
            "zone_status",
            converter=lambda value: (
                IasZone.ZoneStatus.Alarm_1
                if value
                else 0
            ),
        ),

        # ---------------------------------------------------------
        # DP 20 - Illuminance
        #
        # Device reports raw lux value.
        #
        # ZCL IlluminanceMeasurement:
        #   measured_value = 10000 * log10(lux + 1)
        #
        # This is the standard Zigbee illuminance representation.
        # ---------------------------------------------------------
        20: DPToAttributeMapping(
            IlluminanceMeasurement.ep_attribute,
            "measured_value",
            converter=lambda value: (
                0
                if value is None or value < 0
                else int(
                    10000 * __import__("math").log10(
                        int(value) + 1
                    )
                )
            ),
        ),
    }

    data_point_handlers = {
        1: "_dp_2_attr_update",
        20: "_dp_2_attr_update",
    }


class TuyaMotionSensorB8vxct9l(CustomDevice):
    """Tuya TS0601 _TZE204_b8vxct9l mmWave motion sensor."""

    signature = {
        "models_info": [
            ("_TZE204_b8vxct9l", "TS0601"),
        ],
        "endpoints": {
            1: {
                "profile_id": zha.PROFILE_ID,
                "device_type": zha.DeviceType.IAS_ZONE,
                "input_clusters": [
                    Basic.cluster_id,
                    Groups.cluster_id,
                    Scenes.cluster_id,
                    IasZone.cluster_id,
                    0xEF00,
                ],
                "output_clusters": [
                    Time.cluster_id,
                    Ota.cluster_id,
                ],
            }
        },
    }

    replacement = {
        "endpoints": {
            1: {
                "profile_id": zha.PROFILE_ID,
                "device_type": zha.DeviceType.IAS_ZONE,
                "input_clusters": [
                    Basic.cluster_id,
                    Groups.cluster_id,
                    Scenes.cluster_id,
                    IasZone.cluster_id,
                    IlluminanceMeasurement.cluster_id,
                    TuyaMotionCluster,
                ],
                "output_clusters": [
                    Time.cluster_id,
                    Ota.cluster_id,
                ],
            }
        },
    }

