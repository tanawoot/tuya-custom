"""Tuya TS0601 Motion Sensor (_TZE204_b8vxct9l) Custom Quirk for ZHA (HA Core 2026+)."""
import math

from zhaquirks.tuya import TuyaQuirkBuilder
from zhaquirks.tuya.mcu import TuyaMCUCluster
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
        1: TuyaMCUCluster.TuyaDPToAttributeMapping(
            IasZone.attributes_by_name["zone_status"].id,
            converter=lambda x: IasZone.ZoneStatus.Alarm_1 if x else 0,
            endpoint_id=1,
            cluster_name=IasZone.name,
        ),
        # DP 12: Illuminance / Lux
        12: TuyaMCUCluster.TuyaDPToAttributeMapping(
            IlluminanceMeasurement.attributes_by_name["measured_value"].id,
            converter=illuminance_converter,
            endpoint_id=1,
            cluster_name=IlluminanceMeasurement.name,
        ),
    }


(
    TuyaQuirkBuilder("_TZE204_b8vxct9l", "TS0601")
    .tuya_dp(
        dp_id=1,
        ep_attribute=IasZone.ep_attribute,
        attribute_name="zone_status",
        converter=lambda x: IasZone.ZoneStatus.Alarm_1 if x else 0,
    )
    .tuya_dp(
        dp_id=12,
        ep_attribute=IlluminanceMeasurement.ep_attribute,
        attribute_name="measured_value",
        converter=illuminance_converter,
    )
    .add_to_registry()
)

# update hass 2026