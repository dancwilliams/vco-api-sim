from __future__ import annotations

from typing import Optional, List

from pydantic import Field

from .base import VCOBaseModel, HrefMixin


class Enterprise(VCOBaseModel, HrefMixin):
    """Enterprise (Customer) entity."""

    name: str = "Default Enterprise"
    network_id: int = Field(default=1, alias="networkId")
    gateway_pool_id: Optional[int] = Field(default=None, alias="gatewayPoolId")
    alerts_enabled: bool = Field(default=True, alias="alertsEnabled")
    operator_alerts_enabled: bool = Field(default=True, alias="operatorAlertsEnabled")
    endpoint_pki_mode: str = Field(default="CERTIFICATE_DISABLED", alias="endpointPkiMode")

    # Relationships (stored as IDs)
    edge_ids: List[str] = Field(default_factory=list, exclude=True)

    def to_v1_dict(self) -> dict:
        """Convert to V1 API format."""
        return {
            "id": self.id,
            "created": self.created.isoformat(),
            "networkId": self.network_id,
            "gatewayPoolId": self.gateway_pool_id,
            "alertsEnabled": self.alerts_enabled,
            "name": self.name,
            "logicalId": self.logical_id,
        }

    def to_v2_dict(self, base_url: str = "/api/sdwan/v2") -> dict:
        """Convert to V2 API format."""
        return {
            "_href": f"{base_url}/enterprises/{self.logical_id}/",
            "created": self.created.isoformat(),
            "alertsEnabled": self.alerts_enabled,
            "operatorAlertsEnabled": self.operator_alerts_enabled,
            "endpointPkiMode": self.endpoint_pki_mode,
            "name": self.name,
            "logicalId": self.logical_id,
        }
