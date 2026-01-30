from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    # Spec paths
    v1_spec_path: Optional[Path] = Field(
        default=None,
        alias="VCO_V1_SPEC_PATH",
        description="Path to V1 (Swagger 2.0) OpenAPI spec"
    )
    v2_spec_path: Optional[Path] = Field(
        default=None,
        alias="VCO_V2_SPEC_PATH",
        description="Path to V2 (OpenAPI 3.0) spec"
    )

    # Legacy single-spec support
    spec_path: Optional[Path] = Field(
        default=None,
        alias="VCO_SPEC_PATH",
        description="Legacy: single spec path (auto-detected version)"
    )

    # Seeding configuration
    seed_enterprises: int = Field(
        default=2,
        alias="VCO_SEED_ENTERPRISES",
        description="Number of enterprises to seed"
    )
    seed_edges_per_enterprise: int = Field(
        default=5,
        alias="VCO_SEED_EDGES",
        description="Number of edges per enterprise to seed"
    )
    seed_links_per_edge: int = Field(
        default=2,
        alias="VCO_SEED_LINKS",
        description="Number of links per edge to seed"
    )

    # State persistence
    state_file_path: Path = Field(
        default=Path("state.json"),
        alias="VCO_STATE_FILE",
        description="Path to state file for persisting enterprise IDs"
    )

    # Server settings
    host: str = Field(default="0.0.0.0", alias="VCO_HOST")
    port: int = Field(default=8000, alias="VCO_PORT")
    debug: bool = Field(default=False, alias="VCO_DEBUG")

    class Config:
        env_file = ".env"
        extra = "ignore"

    def resolve_specs(self) -> tuple[Optional[Path], Optional[Path]]:
        """Resolve spec paths with fallbacks."""
        v1 = self.v1_spec_path
        v2 = self.v2_spec_path

        # Try to find specs in common locations
        repo_root = Path(__file__).resolve().parents[1]

        if v1 is None:
            candidates = [
                repo_root / "VC-SD-WAN-6.4-v1.json",
                repo_root / "vco-api-json" / "vco_api_v1.json",
            ]
            for c in candidates:
                if c.exists():
                    v1 = c
                    break

        if v2 is None:
            candidates = [
                repo_root / "VC-SD-WAN-6.4-v2.json",
                repo_root / "vco-api-json" / "vco_api_v2.json",
            ]
            for c in candidates:
                if c.exists():
                    v2 = c
                    break

        return v1, v2


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
