# app/models/edge_health.py

from typing import Optional
from pydantic import BaseModel, Field


class VeloEdge(BaseModel):
    """
    Basic metadata about an Edge device as returned by the VCO.

    We keep JSON field names via aliases but use snake_case internally.
    """

    logical_id: str = Field(..., alias="logicalId")
    name: str
    alerts_enabled: Optional[bool] = Field(None, alias="alertsEnabled")


class VeloEdgeHealthTunnelCount(BaseModel):
    min: int
    max: int
    average: float


class VeloEdgeHealthMemoryPercentage(BaseModel):
    min: float
    max: float
    average: float


class VeloEdgeHealthFlowCount(BaseModel):
    min: int
    max: int
    average: float


class VeloEdgeHealthCPUPercentage(BaseModel):
    min: float
    max: float
    average: float


class VeloEdgeHealthCPUCore(BaseModel):
    min: float
    max: float
    average: float


class VeloEdgeHealthHandoffQueueDrop(BaseModel):
    min: int
    max: int
    average: float


class VeloEdgeHealth(BaseModel):
    """
    Raw health metrics grouped similarly to the VCO's stats/metrics APIs.
    """

    tunnel_count: VeloEdgeHealthTunnelCount = Field(..., alias="tunnelCount")
    memory_pct: VeloEdgeHealthMemoryPercentage = Field(..., alias="memoryPct")
    flow_count: VeloEdgeHealthFlowCount = Field(..., alias="flowCount")
    cpu_pct: VeloEdgeHealthCPUPercentage = Field(..., alias="cpuPct")
    cpu_core_temp: VeloEdgeHealthCPUCore = Field(..., alias="cpuCoreTemp")
    handoff_queue_drops: VeloEdgeHealthHandoffQueueDrop = Field(
        ..., alias="handoffQueueDrops"
    )


class EdgeHealthSummary(BaseModel):
    """
    A higher-level summary model we will return from our API / MCP tools.

    This is what the chatbot is most likely to consume:
      - Edge identity
      - Overall status
      - A few key metrics pre-aggregated / simplified
    """

    logical_id: str
    name: str
    # Future: status could be derived (e.g. UP/DOWN/DEGRADED)
    status: str

    # Key metrics for quick at-a-glance view:
    avg_tunnel_count: Optional[float] = None
    avg_memory_pct: Optional[float] = None
    avg_cpu_pct: Optional[float] = None
    avg_flow_count: Optional[float] = None
    avg_cpu_core_temp: Optional[float] = None
    avg_handoff_queue_drops: Optional[float] = None
