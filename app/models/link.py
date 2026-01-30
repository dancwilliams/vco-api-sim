from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import Field

from .base import VCOBaseModel


class LinkState(str, Enum):
    STABLE = "STABLE"
    UNSTABLE = "UNSTABLE"
    STANDBY = "STANDBY"
    DEAD = "DEAD"
    UNKNOWN = "UNKNOWN"


class LinkType(str, Enum):
    WIRED = "WIRED"
    WIRELESS = "WIRELESS"


class Link(VCOBaseModel):
    """WAN Link entity."""

    edge_id: int = Field(alias="edgeId")
    edge_logical_id: str = Field(alias="edgeLogicalId")
    enterprise_logical_id: str = Field(alias="enterpriseLogicalId")

    name: str = Field(default="WAN Link", alias="displayName")
    interface: str = Field(default="GE1")
    link_state: LinkState = Field(default=LinkState.STABLE, alias="linkState")
    link_type: LinkType = Field(default=LinkType.WIRED, alias="networkType")

    # Network info
    ip_address: Optional[str] = Field(default=None, alias="ipAddress")
    isp: Optional[str] = Field(default=None)

    # Bandwidth
    upstream_mbps: float = Field(default=100.0, alias="upstreamMbps")
    downstream_mbps: float = Field(default=100.0, alias="downstreamMbps")

    # Metrics
    latency_ms: float = Field(default=15.0, alias="latencyMs")
    jitter_ms: float = Field(default=2.0, alias="jitterMs")
    loss_pct: float = Field(default=0.0, alias="lossPct")
