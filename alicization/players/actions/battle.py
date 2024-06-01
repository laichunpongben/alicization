import random
import logging

import numpy as np

from ...managers.player_manager import PlayerManager
from ...managers.leaderboard import Leaderboard

logger = logging.getLogger(__name__)

player_manager = PlayerManager()
leaderboard = Leaderboard()

NUM_ATTACK_ROUND = 10
NUM_DEFENSE_ROUND = 8
P_ATTACK_HIT = 0.25
P_DEFENSE_HIT = 0.2
P_SALVAGE = 0.95
MIN_BOUNTY = 100


def attack(player, target_player) -> None:
    current_system = player_manager.get_system(player.name)
    current_location = player_manager.get_location(player.name)
    spaceship = player_manager.get_spaceship(player.name)
    target_spaceship = player_manager.get_spaceship(target_player.name)

    if can_attack(current_location, spaceship):
        if random.random() < max(
            min(
                1 - target_spaceship.evasion * (1 + target_spaceship.level * 0.001),
                1,
            ),
            0,
        ):
            damage = (
                np.random.binomial(
                    NUM_ATTACK_ROUND,
                    max(P_ATTACK_HIT * (1 + spaceship.level * 0.01), 1),
                )
                * spaceship.weapon
            )
            player.total_damage += damage

            universe = player_manager.get_universe(player.name)
            universe.total_damage_dealt += damage
            target_spaceship.take_damage(damage)
            logger.debug(
                f"{player.name} attacked {target_player.name} and caused {damage} damage!"
            )
            if target_spaceship.destroyed:
                if not target_spaceship.is_cargo_full():
                    for item, qty in target_spaceship.cargo_hold.items():
                        if random.random() < P_SALVAGE:
                            target_spaceship.cargo_hold[item] += qty
                            player.turn_production += qty
                    target_spaceship.empty_cargo_hold()
                else:
                    current_system.make_debris(target_spaceship.cargo_hold)

                player.kill += 1
                universe.total_kill += 1
                leaderboard.log_achievement(player.name, "kill", 1)
                target_player.die()
                target_player.last_killed_by = player.name
                leaderboard.log_achievement(target_player.name, "death", 1)

                logger.warning(
                    f"{player.name} killed {target_player.name} at {current_location.name}!"
                )

                bounty = leaderboard.get_achievement_score(target_player.name, "bounty")
                if bounty > 0:
                    player.earn(bounty)
                    leaderboard.log_achievement(
                        target_player.name, "bounty", 0, overwrite=True
                    )
                    logger.info(f"{player.name} earned {bounty} bounty!")
            else:
                defensive_damage = (
                    np.random.binomial(
                        NUM_DEFENSE_ROUND,
                        max(
                            P_DEFENSE_HIT * (1 + target_spaceship.level * 0.01),
                            1,
                        ),
                    )
                    * target_spaceship.weapon
                )
                target_player.total_damage += defensive_damage
                universe = player_manager.get_universe(target_player.name)
                universe.total_damage_dealt += damage
                spaceship.take_damage(defensive_damage)
                logger.debug(
                    f"{target_player.name} returned fire at {player.name} and caused {damage} damage!"
                )
                if spaceship.destroyed:
                    current_system.make_debris(spaceship.cargo_hold)

                    target_player.kill += 1
                    universe.total_kill += 1
                    leaderboard.log_achievement(target_player.name, "kill", 1)
                    player.die()
                    player.last_killed_by = target_player.name
                    leaderboard.log_achievement(player.name, "death", 1)
                    logger.warning(
                        f"{target_player.name} killed {player.name} at {current_location.name}!"
                    )

                    bounty = leaderboard.get_achievement_score(player.name, "bounty")
                    if bounty > 0:
                        target_player.earn(bounty)
                        leaderboard.log_achievement(
                            player.name, "bounty", 0, overwrite=True
                        )
                        logger.info(f"{target_player.name} earned {bounty} bounty!")
        else:
            logger.info(
                f"{target_player.name} escaped an attack at {current_location.name}!"
            )
    else:
        logger.warning(
            f"No valid target or weapon to attack at {current_location.name}!"
        )


def _find_target_player(player, current_location, order_by: int) -> None:
    available_target_players = [p for p in current_location.players if p != player]
    if len(available_target_players) > 0:
        if order_by > 0:
            available_target_players.sort(key=lambda p: p.kill, reverse=False)
            target_player = available_target_players[0]
        elif order_by < 0:
            available_target_players.sort(key=lambda p: p.kill, reverse=True)
            target_player = available_target_players[0]
        else:
            target_player = random.choice(available_target_players)
        return target_player
    else:
        return None


def attack_player(player, difficulty: str) -> None:
    current_location = player_manager.get_location(player.name)
    if difficulty == "weak":
        order_by = 1
    elif difficulty == "strong":
        order_by = -1
    else:
        order_by = 0
    target_player = _find_target_player(player, current_location, order_by)
    if target_player is not None:
        attack(player, target_player)
    else:
        logger.warning("No valid target to attack!")


def bombard(player, target_building) -> None:
    current_location = player_manager.get_location(player.name)
    spaceship = player_manager.get_spaceship(player.name)
    if can_bombard(current_location, spaceship):
        target_building.bombard(player, spaceship)
    else:
        logger.warning("Cannot bombard from this location.")


def bombard_random_building(player) -> None:
    current_location = player_manager.get_location(player.name)
    available_target_buildings = [building for building in current_location.buildings]
    if len(available_target_buildings) > 0:
        target_building = random.choice(available_target_buildings)
        bombard(player, target_building)
    else:
        logger.warning("No building to bombard from this location.")


def place_bounty(player) -> None:
    if can_place_bounty(player):
        spend_factor = 0.01
        upper_bound = max(MIN_BOUNTY, int(player.wallet * spend_factor))
        bounty = random.randint(MIN_BOUNTY, upper_bound)
        player.spend(bounty)
        target_player_name = player.last_killed_by
        leaderboard.log_achievement(target_player_name, "bounty", bounty)
        player.last_killed_by = None
        logger.info(
            f"{player.name} placed a bounty of {bounty} on {target_player_name}!"
        )
    else:
        logger.warning("Cannot place bounty.")


def can_attack(current_location, spaceship) -> bool:
    return len(current_location.players) > 1 and spaceship.weapon > 0


def can_bombard(current_location, spaceship) -> bool:
    return (
        len(current_location.buildings) > 1
        and any(building.cooldown <= 0 for building in current_location.buildings)
        and spaceship.weapon > 0
    )


def can_place_bounty(player) -> bool:
    return player.wallet >= MIN_BOUNTY and player.last_killed_by is not None
