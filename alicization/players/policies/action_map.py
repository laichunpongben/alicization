# players/policies/action_map.py

from ..enums.action import Action

ACTION_INDEX_MAP = {action.value: i for i, action in enumerate(Action)}
ACTIONS = [action.value for _, action in enumerate(Action)]
