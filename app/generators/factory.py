from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from faker import Faker

fake = Faker()
Faker.seed(42)  # Reproducible fake data


class RealisticGenerator:
    """Generate realistic SD-WAN test data."""

    # Common ISPs
    ISPS = ["AT&T", "Verizon", "Comcast", "Spectrum", "CenturyLink", "Cox", "Frontier"]

    # Edge model numbers
    EDGE_MODELS = ["edge510", "edge520", "edge540", "edge610", "edge620", "edge640",
                   "edge840", "edge1000", "edge2000", "edge3800"]

    # US cities for realistic locations
    US_CITIES = [
        ("Austin", "TX", "US", 30.2672, -97.7431),
        ("Denver", "CO", "US", 39.7392, -104.9903),
        ("Seattle", "WA", "US", 47.6062, -122.3321),
        ("New York", "NY", "US", 40.7128, -74.0060),
        ("Los Angeles", "CA", "US", 34.0522, -118.2437),
        ("Chicago", "IL", "US", 41.8781, -87.6298),
        ("Atlanta", "GA", "US", 33.7490, -84.3880),
        ("Dallas", "TX", "US", 32.7767, -96.7970),
        ("Phoenix", "AZ", "US", 33.4484, -112.0740),
        ("Boston", "MA", "US", 42.3601, -71.0589),
    ]

    @classmethod
    def enterprise_name(cls) -> str:
        """Generate realistic company name."""
        return fake.company()

    @classmethod
    def edge_name(cls, site_name: Optional[str] = None) -> str:
        """Generate edge name based on site."""
        if site_name:
            return f"{site_name}-Edge"
        return f"{fake.city()}-Edge-{random.randint(1, 99):02d}"

    @classmethod
    def location(cls) -> Dict[str, Any]:
        """Generate random US location."""
        city, state, country, lat, lon = random.choice(cls.US_CITIES)
        return {
            "city": city,
            "state": state,
            "country": country,
            "latitude": lat + random.uniform(-0.1, 0.1),
            "longitude": lon + random.uniform(-0.1, 0.1),
            "postal_code": fake.zipcode(),
        }

    @classmethod
    def ip_address(cls, public: bool = True) -> str:
        """Generate IP address."""
        if public:
            return fake.ipv4_public()
        return fake.ipv4_private()

    @classmethod
    def serial_number(cls) -> str:
        """Generate edge serial number."""
        return f"VC{fake.lexify(text='??????').upper()}{fake.numerify(text='######')}"

    @classmethod
    def edge_model(cls) -> str:
        """Generate random edge model."""
        return random.choice(cls.EDGE_MODELS)

    @classmethod
    def isp(cls) -> str:
        """Generate random ISP name."""
        return random.choice(cls.ISPS)

    @classmethod
    def bandwidth_mbps(cls, min_bw: int = 10, max_bw: int = 1000) -> float:
        """Generate realistic bandwidth value."""
        common = [10, 25, 50, 100, 200, 500, 1000]
        filtered = [b for b in common if min_bw <= b <= max_bw]
        return float(random.choice(filtered) if filtered else random.randint(min_bw, max_bw))

    @classmethod
    def latency_ms(cls, healthy: bool = True) -> float:
        """Generate realistic latency value."""
        if healthy:
            return round(random.uniform(5.0, 50.0), 2)
        return round(random.uniform(100.0, 500.0), 2)

    @classmethod
    def jitter_ms(cls, healthy: bool = True) -> float:
        """Generate realistic jitter value."""
        if healthy:
            return round(random.uniform(0.5, 10.0), 2)
        return round(random.uniform(20.0, 100.0), 2)

    @classmethod
    def loss_pct(cls, healthy: bool = True) -> float:
        """Generate realistic packet loss percentage."""
        if healthy:
            return round(random.uniform(0.0, 2.0), 2)
        return round(random.uniform(5.0, 30.0), 2)

    @classmethod
    def cpu_pct(cls, healthy: bool = True) -> float:
        """Generate realistic CPU percentage."""
        if healthy:
            return round(random.uniform(10.0, 60.0), 1)
        return round(random.uniform(80.0, 99.0), 1)

    @classmethod
    def memory_pct(cls, healthy: bool = True) -> float:
        """Generate realistic memory percentage."""
        if healthy:
            return round(random.uniform(30.0, 70.0), 1)
        return round(random.uniform(85.0, 99.0), 1)

    @classmethod
    def tunnel_count(cls) -> int:
        """Generate realistic tunnel count."""
        return random.randint(2, 20)

    @classmethod
    def flow_count(cls) -> int:
        """Generate realistic flow count."""
        return random.randint(50, 5000)

    @classmethod
    def bytes_transferred(cls, interval_minutes: int = 5) -> int:
        """Generate realistic bytes transferred in interval."""
        # Assume 10-100 Mbps average utilization
        mbps = random.uniform(10, 100)
        bytes_per_second = (mbps * 1_000_000) / 8
        return int(bytes_per_second * interval_minutes * 60 * random.uniform(0.5, 1.5))

    @classmethod
    def time_series(
        cls,
        start: datetime,
        end: datetime,
        interval_minutes: int = 5,
        metric_type: str = "health"
    ) -> List[Dict[str, Any]]:
        """Generate time series data points."""
        points = []
        current = start
        healthy = random.random() > 0.2  # 80% chance of healthy

        while current <= end:
            point = {"time": int(current.timestamp() * 1000)}

            if metric_type == "health":
                point["cpuPct"] = cls.cpu_pct(healthy)
                point["memoryPct"] = cls.memory_pct(healthy)
                point["tunnelCount"] = cls.tunnel_count()
                point["flowCount"] = cls.flow_count()
            elif metric_type == "link":
                point["txBytes"] = cls.bytes_transferred(interval_minutes)
                point["rxBytes"] = cls.bytes_transferred(interval_minutes)
                point["latencyMs"] = cls.latency_ms(healthy)
                point["jitterMs"] = cls.jitter_ms(healthy)
                point["lossPct"] = cls.loss_pct(healthy)

            points.append(point)
            current += timedelta(minutes=interval_minutes)

        return points

    @classmethod
    def min_max_avg(cls, base: float, variance: float = 0.2) -> Dict[str, float]:
        """Generate min/max/average structure."""
        min_val = base * (1 - variance)
        max_val = base * (1 + variance)
        avg_val = base
        return {
            "min": round(min_val, 2),
            "max": round(max_val, 2),
            "average": round(avg_val, 2),
        }
