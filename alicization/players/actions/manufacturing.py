import logging

from ...managers.player_manager import PlayerManager

logger = logging.getLogger(__name__)

player_manager = PlayerManager()


blueprints = {
    "miner": [
        ("cosmic_resin", 160),
        ("hyper_dust", 70),
        ("presolar_grain", 180),
        ("nebulite", 35),
        ("water_ice", 55),
    ],
    "corvette": [
        ("cosmic_ice", 320),
        ("helium", 360),
        ("hyper_dust", 140),
        ("nebulite", 70),
        ("water_ice", 110),
    ],
    "frigate": [
        ("cosmic_dust", 8000),
        ("cosmic_ice", 6000),
        ("helium", 5000),
        ("hyper_dust", 4000),
        ("spacetime_dust", 7000),
        ("astralite", 2500),
        ("hyperspace_flux", 1800),
        ("pulsar_residue", 2000),
        ("rare_earth_minerals", 1500),
        ("voidium", 2200),
    ],
    "destroyer": [
        ("cosmic_ice", 50000),
        ("presolar_grain", 80000),
        ("photon_dust", 100000),
        ("quantum_foam", 120000),
        ("solar_dust", 150000),
        ("antigravity_dust", 100000),
        ("etherium", 120000),
        ("hyperspace_flux", 50000),
        ("nullmetal", 150000),
        ("rare_earth_minerals", 80000),
        ("aetherium", 30000),
        ("chronomite", 70000),
        ("dimensional_rift_residue", 40000),
        ("warpflux", 60000),
        ("xylothium", 50000),
    ],
    "extractor": [
        ("cosmic_resin", 4000),
        ("hyper_dust", 3000),
        ("presolar_grain", 2500),
        ("nebulite", 2000),
        ("water_ice", 3500),
        ("astralite", 1250),
        ("etherium", 900),
        ("hyperspace_flux", 1000),
        ("pulsar_residue", 750),
        ("voidium", 1100),
    ],
    "courier": [
        ("hyper_dust", 140),
        ("nebular_energy", 360),
        ("nebulite", 70),
        ("stellar_dust", 320),
        ("water_ice", 110),
    ],
}


def manufacture(player, blueprint_name: str) -> None:
    current_location = player_manager.get_location(player.name)
    if can_manufacture(player, current_location, blueprint_name):
        if current_location.factory.manufacture(player, blueprint_name):
            logger.debug(f"{player.name} built {blueprint_name}.")
        else:
            logger.warning(f"{blueprint_name} manufacturing job failed!")
    else:
        logger.warning(f"Cannot manufacture from this location")


def can_manufacture(player, current_location, blueprint_name: str) -> bool:
    blueprint = blueprints.get(blueprint_name)
    return (
        current_location.has_factory()
        and current_location.has_storage()
        and all(
            current_location.storage.get_item(player.name, item) >= qty
            for item, qty in blueprint
        )
    )
