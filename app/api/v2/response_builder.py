"""Build API responses that conform strictly to the OpenAPI spec."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

log = logging.getLogger("vco-sim.v2.response")


class SpecResponseBuilder:
    """Build responses that conform to OpenAPI schema definitions."""

    def __init__(self, spec: Dict[str, Any], resolver) -> None:
        self.spec = spec
        self.resolver = resolver
        self._schemas = spec.get("components", {}).get("schemas", {})

    def get_schema(self, schema_name: str) -> Optional[Dict[str, Any]]:
        """Get a schema definition by name."""
        return self._schemas.get(schema_name)

    def resolve_ref(self, ref: str) -> Dict[str, Any]:
        """Resolve a $ref to its schema definition."""
        # ref format: "#/components/schemas/SchemaName"
        if ref.startswith("#/components/schemas/"):
            schema_name = ref.split("/")[-1]
            return self._schemas.get(schema_name, {})
        return self.resolver.resolve(ref)

    def build_link_stats_response(self, links_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build linkStats response - returns array directly per spec."""
        # Schema: linkStats -> type: array, items: EdgeLinkStatsRecord
        # EdgeLinkStatsRecord has: link (LinkResource), bytesTx, bytesRx, packetsTx, packetsRx, etc.
        return [self._build_edge_link_stats_record(link) for link in links_data]

    def _build_edge_link_stats_record(self, link_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build a single EdgeLinkStatsRecord."""
        tx_bytes = link_data.get("txBytes", 0)
        rx_bytes = link_data.get("rxBytes", 0)
        return {
            "link": self._build_link_resource(link_data),
            "bytesTx": float(tx_bytes),
            "bytesRx": float(rx_bytes),
            "packetsTx": float(tx_bytes / 1000) if tx_bytes else 0.0,
            "packetsRx": float(rx_bytes / 1000) if rx_bytes else 0.0,
            "totalBytes": float(tx_bytes + rx_bytes),
            "totalPackets": float((tx_bytes + rx_bytes) / 1000) if (tx_bytes + rx_bytes) else 0.0,
            "p1BytesRx": 0.0,
            "p1BytesTx": 0.0,
            "p1PacketsRx": 0.0,
            "p1PacketsTx": 0.0,
            "p2BytesRx": 0.0,
            "p2BytesTx": 0.0,
            "p2PacketsRx": 0.0,
            "p2PacketsTx": 0.0,
            "p3BytesRx": 0.0,
            "p3BytesTx": 0.0,
            "p3PacketsRx": 0.0,
            "p3PacketsTx": 0.0,
            "controlBytesRx": 0.0,
            "controlBytesTx": 0.0,
            "controlPacketsRx": 0.0,
            "controlPacketsTx": 0.0,
        }

    def _build_link_resource(self, link_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build a LinkResource object."""
        link_state = link_data.get("linkState", "STABLE")
        return {
            "logicalId": link_data.get("logicalId", ""),
            "internalId": link_data.get("logicalId", ""),
            "interface": link_data.get("interface", "GE1"),
            "ipAddress": link_data.get("ipAddress"),
            "displayName": link_data.get("name", ""),
            "isp": link_data.get("isp"),
            "networkSide": "WAN",
            "networkType": self._map_network_type(link_data.get("networkType", "WIRED")),
            "state": link_state,
            "linkMode": "ACTIVE" if link_state == "STABLE" else "BACKUP",
            "backupState": "UNCONFIGURED",
            "userOverride": False,
            "lat": 0.0,
            "lon": 0.0,
        }

    def _map_network_type(self, link_type: str) -> str:
        """Map internal link type to spec enum value."""
        # Spec enum: UNKNOWN, WIRELESS, ETHERNET, WIFI
        mapping = {
            "WIRED": "ETHERNET",
            "WIRELESS": "WIRELESS",
            "WIFI": "WIFI",
            "LTE": "WIRELESS",
        }
        return mapping.get(link_type, "ETHERNET")

    def build_flow_stats_response(self, flows_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build flowStats response - returns array directly per spec."""
        # Schema: FlowStats -> type: array, items: FlowStatsResource
        return [self._build_flow_stats_resource(flow) for flow in flows_data]

    def _build_flow_stats_resource(self, flow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build a single FlowStatsResource."""
        bytes_rx = flow_data.get("bytesRx", 0)
        bytes_tx = flow_data.get("bytesTx", 0)
        packets_rx = flow_data.get("packetsRx", 0)
        packets_tx = flow_data.get("packetsTx", 0)

        result: Dict[str, Any] = {
            "bytesRx": float(bytes_rx),
            "bytesTx": float(bytes_tx),
            "totalBytes": float(flow_data.get("totalBytes", bytes_rx + bytes_tx)),
            "packetsRx": float(packets_rx),
            "packetsTx": float(packets_tx),
            "totalPackets": float(packets_rx + packets_tx),
            "flowCount": float(flow_data.get("flowCount", 0)),
        }

        # Add optional grouping fields based on what's present
        if "destFQDN" in flow_data:
            result["destFQDN"] = flow_data["destFQDN"]
        if "application" in flow_data:
            result["application"] = {
                "name": flow_data["application"],
                "displayName": flow_data["application"],
            }
        if "sourceIP" in flow_data:
            result["sourceIp"] = flow_data["sourceIP"]
        if "destIP" in flow_data:
            result["destIp"] = flow_data["destIP"]

        return result

    def build_health_stats_response(self, health_data: Dict[str, Any], href: str) -> Dict[str, Any]:
        """Build EdgeHealthStatsMetricsSchema response."""
        return {
            "_href": href,
            "total": health_data.get("total", 1),
            "tunnelCount": self._ensure_basic_metric_summary(health_data.get("tunnelCount", {})),
            "tunnelCountV6": self._ensure_basic_metric_summary(health_data.get("tunnelCountV6", {})),
            "memoryPct": self._ensure_basic_metric_summary(health_data.get("memoryPct", {})),
            "flowCount": self._ensure_basic_metric_summary(health_data.get("flowCount", {})),
            "cpuPct": self._ensure_basic_metric_summary(health_data.get("cpuPct", {})),
            "cpuCoreTemp": self._ensure_basic_metric_summary(health_data.get("cpuCoreTemp", {})),
            "handoffQueueDrops": self._ensure_basic_metric_summary(health_data.get("handoffQueueDrops", {})),
        }

    def _ensure_basic_metric_summary(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Ensure data matches BasicMetricSummary schema (min, max, average required)."""
        return {
            "min": float(data.get("min", 0)),
            "max": float(data.get("max", 0)),
            "average": float(data.get("average", 0)),
        }

    def build_health_stats_series_response(
        self,
        series_data: List[Dict[str, Any]],
        href: str
    ) -> Dict[str, Any]:
        """Build EdgeHealthStatsSeriesSchema response."""
        # Transform time-point format to metric-series format
        metrics = ["cpuPct", "memoryPct", "tunnelCount", "flowCount"]
        series = []

        for metric in metrics:
            if series_data:
                data_points = [point.get(metric) for point in series_data]
                valid_points = [d for d in data_points if d is not None]
                if valid_points:
                    series.append({
                        "metric": metric,
                        "startTime": None,  # Optional per spec
                        "tickInterval": 300000.0,  # 5 minutes in ms
                        "data": [float(d) if d is not None else None for d in data_points],
                        "min": float(min(valid_points)),
                        "max": float(max(valid_points)),
                        "total": float(sum(valid_points)),
                    })

        return {
            "_href": href,
            "series": series,
        }

    def build_link_stats_series_response(
        self,
        series_data: List[Dict[str, Any]],
        links_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Build linkStatsSeries response - array of LinkStatsSeriesRecord."""
        # One record per link, each with its own series
        result = []
        for link_data in links_data:
            metrics = ["txBytes", "rxBytes", "latencyMs", "jitterMs", "lossPct"]
            series = []

            for metric in metrics:
                data_points = [point.get(metric) for point in series_data]
                valid_points = [d for d in data_points if d is not None]
                if valid_points:
                    series.append({
                        "metric": metric,
                        "tickInterval": 300000.0,
                        "data": [float(d) if d is not None else None for d in data_points],
                    })

            result.append({
                "link": self._build_link_resource(link_data),
                "series": series,
            })

        # Return at least one record if no links
        if not result:
            result.append({
                "link": self._build_link_resource({"logicalId": "default", "name": "link-1", "interface": "GE1"}),
                "series": [],
            })

        return result

    def build_device_settings_response(
        self,
        edge_data: Dict[str, Any],
        links_data: List[Dict[str, Any]],
        href: str
    ) -> Dict[str, Any]:
        """Build BaseDeviceSettings response."""
        # The spec defines a complex structure with optional nested objects
        # We provide the minimal required structure that matches the schema
        result: Dict[str, Any] = {
            "_href": href,
            "lan": {
                "networks": [
                    {
                        "vlanId": 1,
                        "name": "Default-LAN",
                        "segmentId": 0,
                        "disabled": False,
                        "advertise": True,
                        "cost": 0,
                        "cidrIp": "10.0.0.0",
                        "cidrPrefix": 24,
                        "netmask": "255.255.255.0",
                        "dhcp": {
                            "enabled": True,
                        }
                    }
                ],
                "interfaces": []
            },
            "segments": [
                {
                    "segment": {
                        "name": "Global Segment",
                        "type": "REGULAR",
                    }
                }
            ],
        }

        # Add routed interfaces if we have link data
        if links_data:
            result["routedInterfaces"] = [
                self._build_routed_interface(link) for link in links_data
            ]

        return result

    def _build_routed_interface(self, link_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build a DeviceSettingsRoutedInterface."""
        ip_address = link_data.get("ipAddress", "")
        return {
            "name": link_data.get("interface", "GE1"),
            "disabled": False,
            "addressing": {
                "type": "STATIC" if ip_address else "DHCP",
                "cidrIp": ip_address.split("/")[0] if ip_address and "/" in ip_address else ip_address,
                "cidrPrefix": 24,
            },
            "wanOverlay": "AUTO_DISCOVERED",
            "natDirect": True,
            "l2": {
                "autonegotiation": True,
            },
            "ospf": {
                "enabled": False,
            },
        }
