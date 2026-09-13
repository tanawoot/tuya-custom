"""Tuya TS0601 Motion Sensor (_TZE204_b8vxct9l) Custom Quirk for ZHA."""

import math
from typing import Dict

from zigpy.profiles import zha
from zigpy.quirks import CustomDevice
from zhaquirks.tuya.mcu import DPToAttributeMapping, TuyaMCUCluster

from zigpy.zcl.clusters.general import (
    Basic,
    Groups,
    Ota,
    PowerConfiguration,
    Scenes,
    Time,
)
from zigpy.zcl.clusters.measurement import IlluminanceMeasurement
from zigpy.zcl.clusters.security import IasZone


def illuminance_converter(lux_val: int) -> int:
    """Convert Tuya lux value to Zigbee ZCL illuminance scale."""
    if lux_val is None or lux_val <= 0:
        return 0

    return int(10000 * math.log10(lux_val) + 1)


class TuyaMotionCluster(TuyaMCUCluster):
    """Custom Tuya MCU cluster for motion sensor DP mapping."""

    dp_to_attribute: Dict[int, DPToAttributeMapping] = {
        # DP 1:
        # Motion state
        # 0 = clear
        # 1 = detected
        1: DPToAttributeMapping(
            IasZone.ep_attribute,
            "zone_status",
            converter=lambda value: (
                IasZone.ZoneStatus.Alarm_1 if value else 0
            ),
        ),

        # DP 4:
        # Battery percentage
        # Tuya: 0-100
        # Zigbee: 0-200 (0.5% per unit)
        4: DPToAttributeMapping(
            PowerConfiguration.ep_attribute,
            "battery_percentage_remaining",
            converter=lambda value: int(value * 2),
        ),

        # DP 12:
        # Illuminance / Lux
        12: DPToAttributeMapping(
            IlluminanceMeasurement.ep_attribute,
            "measured_value",
            converter=illuminance_converter,
        ),
    }

    data_point_handlers = {
        1: "_dp_2_attr_update",
        4: "_dp_2_attr_update",
        12: "_dp_2_attr_update",
    }


class TuyaMotionSensorB8vxct9l(CustomDevice):
    """Tuya TS0601 Motion Sensor _TZE204_b8vxct9l."""

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
                    PowerConfiguration.cluster_id,
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