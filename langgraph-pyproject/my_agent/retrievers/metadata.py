from my_agent.model.user import AssetTypeEnum


def get_metadata():
    asset_types = [
        {
            "name": asset_type.name,
            "description": asset_type.value
        }
        for asset_type in AssetTypeEnum
    ]

    return {"available_asset_types": asset_types}
