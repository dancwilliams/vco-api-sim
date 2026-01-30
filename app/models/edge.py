from __future__ import annotations

from enum import Enum
from typing import Optional, List

from pydantic import Field

from .base import VCOBaseModel, HrefMixin


class EdgeState(str, Enum):
    NEVER_ACTIVATED = "NEVER_ACTIVATED"
    CONNECTED = "CONNECTED"
    DEGRADED = "DEGRADED"
    OFFLINE = "OFFLINE"


class EdgeHAState(str, Enum):
    UNCONFIGURED = "UNCONFIGURED"
    PENDING_INIT = "PENDING_INIT"
    PENDING_CONFIRMATION = "PENDING_CONFIRMATION"
    PENDING_CONFIRMED = "PENDING_CONFIRMED"
    PENDING_DISSOCIATION = "PENDING_DISSOCIATION"
    READY = "READY"
    FAILED = "FAILED"


class Edge(VCOBaseModel, HrefMixin):
    """Edge device entity."""

    name: str = "Edge Device"
    enterprise_id: int = Field(alias="enterpriseId")
    enterprise_logical_id: str = Field(alias="enterpriseLogicalId")

    # State
    edge_state: EdgeState = Field(default=EdgeState.CONNECTED, alias="edgeState")
    service_state: str = Field(default="IN_SERVICE", alias="serviceState")
    ha_state: EdgeHAState = Field(default=EdgeHAState.UNCONFIGURED, alias="haState")
    activation_state: str = Field(default="ACTIVATED", alias="activationState")
    alerts_enabled: bool = Field(default=True, alias="alertsEnabled")

    # Device info
    model_number: str = Field(default="edge510", alias="modelNumber")
    device_family: str = Field(default="EDGE5X0", alias="deviceFamily")
    software_version: str = Field(default="6.4.0", alias="softwareVersion")
    build_number: str = Field(default="R640-20240101-GA", alias="buildNumber")
    serial_number: Optional[str] = Field(default=None, alias="serialNumber")

    # Location
    site_id: Optional[int] = Field(default=None, alias="siteId")
    site_name: Optional[str] = Field(default=None, alias="siteName")
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = Field(default=None, alias="postalCode")
    latitude: Optional[float] = Field(default=None, alias="lat")
    longitude: Optional[float] = Field(default=None, alias="lon")

    # Relationships
    link_ids: List[str] = Field(default_factory=list, exclude=True)

    def to_v1_dict(self) -> dict:
        """Convert to V1 API format."""
        return {
            "id": self.id,
            "created": self.created.isoformat(),
            "enterpriseId": self.enterprise_id,
            "logicalId": self.logical_id,
            "name": self.name,
            "edgeState": self.edge_state.value if isinstance(self.edge_state, EdgeState) else self.edge_state,
            "serviceState": self.service_state,
            "haState": self.ha_state.value if isinstance(self.ha_state, EdgeHAState) else self.ha_state,
            "activationState": self.activation_state,
            "alertsEnabled": self.alerts_enabled,
            "modelNumber": self.model_number,
            "deviceFamily": self.device_family,
            "softwareVersion": self.software_version,
            "buildNumber": self.build_number,
            "serialNumber": self.serial_number,
        }

    def to_v2_dict(self, base_url: str = "/api/sdwan/v2") -> dict:
        """Convert to V2 API format."""
        ent_id = self.enterprise_logical_id
        return {
            "_href": f"{base_url}/enterprises/{ent_id}/edges/{self.logical_id}/",
            "logicalId": self.logical_id,
            "name": self.name,
            "edgeState": self.edge_state.value if isinstance(self.edge_state, EdgeState) else self.edge_state,
            "alertsEnabled": self.alerts_enabled,
            "modelNumber": self.model_number,
            "softwareVersion": self.software_version,
            "site": {
                "name": self.site_name,
                "city": self.city,
                "state": self.state,
                "country": self.country,
                "lat": self.latitude,
                "lon": self.longitude,
            } if self.site_name else None,
        }
