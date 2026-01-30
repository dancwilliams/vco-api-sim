from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from .base import MinMaxAverage, HrefMixin


class EdgeHealthStats(BaseModel, HrefMixin):
    """Edge health statistics aggregate."""

    total: int = 1
    tunnel_count: MinMaxAverage = Field(default_factory=MinMaxAverage, alias="tunnelCount")
    tunnel_count_v6: MinMaxAverage = Field(default_factory=MinMaxAverage, alias="tunnelCountV6")
    memory_pct: MinMaxAverage = Field(default_factory=MinMaxAverage, alias="memoryPct")
    flow_count: MinMaxAverage = Field(default_factory=MinMaxAverage, alias="flowCount")
    cpu_pct: MinMaxAverage = Field(default_factory=MinMaxAverage, alias="cpuPct")
    cpu_core_temp: MinMaxAverage = Field(default_factory=MinMaxAverage, alias="cpuCoreTemp")
    handoff_queue_drops: MinMaxAverage = Field(
        default_factory=MinMaxAverage, alias="handoffQueueDrops"
    )


class TimeSeriesPoint(BaseModel):
    """Single point in a time series."""

    time: int  # Unix timestamp
    cpu_pct: Optional[float] = Field(default=None, alias="cpuPct")
    memory_pct: Optional[float] = Field(default=None, alias="memoryPct")
    tunnel_count: Optional[int] = Field(default=None, alias="tunnelCount")
    flow_count: Optional[int] = Field(default=None, alias="flowCount")
    tx_bytes: Optional[int] = Field(default=None, alias="txBytes")
    rx_bytes: Optional[int] = Field(default=None, alias="rxBytes")
    latency_ms: Optional[float] = Field(default=None, alias="latencyMs")
    jitter_ms: Optional[float] = Field(default=None, alias="jitterMs")
    loss_pct: Optional[float] = Field(default=None, alias="lossPct")


class LinkStats(BaseModel, HrefMixin):
    """Link statistics aggregate."""

    total: int = 1
    link: str = "link-1"
    tx_bytes: int = Field(default=0, alias="txBytes")
    rx_bytes: int = Field(default=0, alias="rxBytes")
    latency_ms: float = Field(default=0.0, alias="latencyMs")
    jitter_ms: float = Field(default=0.0, alias="jitterMs")
    loss_pct: float = Field(default=0.0, alias="lossPct")


class FlowStats(BaseModel, HrefMixin):
    """Flow statistics."""

    total: int = 1
    application: str = "Unknown"
    bytes_tx: int = Field(default=0, alias="bytesTx")
    bytes_rx: int = Field(default=0, alias="bytesRx")
    packets_tx: int = Field(default=0, alias="packetsTx")
    packets_rx: int = Field(default=0, alias="packetsRx")
