from enum import Enum
from dataclasses import dataclass, field

class AssetType(Enum):
    CASH = "cash"
    STOCK = "stock"
    BOND = "bond"


# class Asset:
#     def __init__(self, ticker : str, name : str, value : float, asset_type : AssetType, duration: float = 0.0):
#         self.ticker = ticker
#         self.name = name
#         self.value = value
#         self.asset_type = asset_type
#         self.duration = duration
#
# class Portfolio:
#     def __init__(self, assets: list[Asset] | None = None):
#         self.assets = assets if assets is not None else []

@dataclass(frozen=True)
class Asset:
    ticker : str
    name : str
    value : float
    asset_type : AssetType
    duration : float = 0.0
    def __post_init__(self):
        if self.value < 0:
            raise ValueError("Value cannot be negative")
        if self.duration < 0:
            raise ValueError("Duration cannot be negative")

@dataclass
class Portfolio:
    assets: list[Asset] = field(default_factory=list)

    def add_asset(self, asset: Asset) -> None:
        self.assets.append(asset)

    def total_value(self) -> float:
        total = 0.0
        for asset in self.assets:
            total += asset.value
        return total

    def get_asset_weight(self, ticker: str) -> float:
        found = False
        value = 0.0
        for asset in self.assets:
            if asset.ticker == ticker:
                found = True
                value += asset.value
        if found == False:
            raise ValueError("Asset not found")
        total = self.total_value()
        if total == 0.0:
            return 0.0
        asset_weight = value/total * 100
        return asset_weight
