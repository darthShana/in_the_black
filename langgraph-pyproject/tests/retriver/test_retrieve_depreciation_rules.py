from datetime import date
from decimal import Decimal

from my_agent.model.user import Asset
from my_agent.retrievers.ir_264 import calculate_depreciation


def test_retrieve_depreciation_rules():
    heat_pump = Asset(
        asset_type="Heat Pump",
        installation_date=date(2021, 8, 1),
        installation_value=3800
    )
    result = calculate_depreciation(heat_pump, 2024)
    assert result['depreciation'] == 526.93
    assert result['opening_value'] == 2634.66
