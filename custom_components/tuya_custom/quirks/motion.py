"""Tuya TS0601 Motion Sensor (_TZE204_b8vxct9l) Custom Quirk for ZHA."""
import math

from zigpy.profiles import zha
from zigpy.quirks import CustomDevice
from zhaquirks.tuya.mcu import TuyaMCUCluster
from zigpy.zcl.clusters.general import Basic, Groups, Ota, Scenes, Time
from zigpy.zcl.clusters.measurement import IlluminanceMeasurement
from zigpy.zcl.clusters.security import IasZone


def illuminance_converter(lux_val: int) -> int:
    """Convert raw Tuya Lux value to Zigbee ZCL Illuminance scale."""
    if lux_val is None or lux_val <= 0:
        return 0
    return int(10000 * math.log10(lux_val) + 1)


class TuyaMotionCluster(TuyaMCUCluster):
    """Custom Tuya MCU cluster for Motion Sensor DP mapping."""

    dp_to_attribute = {
        # DP 1: Motion State (0 = Clear, 1 = Detected)
        1: (
            IasZone.attributes_by_name["zone_status"].id,
            lambda x: IasZone.ZoneStatus.Alarm_1 if x else 0,
        ),
        # DP 12: Illuminance / Lux
        12: (
            IlluminanceMeasurement.attributes_by_name["measured_value"].id,
            illuminance_converter,
        ),
    }


class TuyaMotionSensorB8vxct9l(CustomDevice):
    """Tuya TS0601 Motion Sensor _TZE204_b8vxct9l."""

    signature = {
        "models_info": [
            ("_TZE204_b8vxct9l", "TS0601"),
            ("_TZE204_b8vxct9l", ""),
        ],
        "endpoints": {
            1: {
                "profile_id": zha.PROFILE_ID,
                "device_type": zha.DeviceType.IAS_ZONE,
                "input_clusters": [
                    Basic.cluster_id,
                    Groups.cluster_id,
                    Scenes.cluster_id,
                    TuyaMCUCluster.cluster_id,  # 0xEF00 (บังคับแมตช์ Signature)
                ],
                "output_clusters": [Time.cluster_id, Ota.cluster_id],
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
                "output_clusters": [Time.cluster_id, Ota.cluster_id],
            }
        },
    }

# End of Tuya TS0601 Motion Sensor (_TZE204_b8vxct9l) Custom Quirk for ZHA.