# Alicization: A Space 4X Agent-Based Simulation

Alicization is a Python-based space 4X game that utilizes agent-based simulation to create a dynamic and engaging experience.

## Introduction

Welcome to Alicization! Inspired by classic 4X space games, Alicization aims to combine the excitement of space exploration, resource management, and strategic combat with the cutting-edge technology of agent-based simulation and reinforcement learning.

## Features

* **Exploration:** Discover new star systems and explore their planets, moons, asteroid belts, and other locations.
* **Expansion:** Set up a home system and expand your territory through exploration and strategic stargate activation.
* **Exploitation:** Mine resources, manufacture spaceships, invest in buildings (factories, drydocks), and collect profits.
* **Extermination:** Engage in combat with other players, conquer systems, and claim bounties.
* **Agent-Based Simulation:** Players can be controlled by various AI agents:
    * **Random Walk AI:** Randomly chooses actions.
    * **Symbolic AI:** Uses predefined rules and heuristics for decision-making.
    * **Neural AI (DQN):** Learns through reinforcement learning (currently in development, with expected roles to enhance decision-making and strategy).
* **Dynamic Universe:** The universe expands as players explore and interact, with new star systems, resources, and missions emerging.
* **Web Interface:** A web interface using FastAPI and WebSockets provides a real-time visualization of the game state. Connect to the websocket endpoint using `'ws://localhost:8000/ws'`.

## Gameplay Mechanics

**Earning and Competition**

Alicization offers diverse ways to earn resources and compete with other players:

* **Mining:** Collect resources from planets, moons, and asteroid belts. The rarity of resources affects both their abundance and value.
* **Manufacturing:** Build spaceships using mined resources. Different spaceship types excel in different areas, such as mining, exploration, combat, and transport.
* **Building Investment:** Invest in buildings like factories and drydocks. These buildings increase your production capacity, repair/upgrade capabilities, and generate profits based on player interaction with their services.
* **Trading:** Buy and sell resources and spaceships at marketplaces located on planets. Prices fluctuate based on supply and demand, offering opportunities for profit.
* **Missions:** Complete missions on moons for rewards, but be wary of their difficulty and potential consequences.
* **Bounties:** Place bounties on other players who have killed you to encourage their elimination. Clarify the conditions under which bounties are placed.
* **Combat:** Engage in combat with other players to eliminate their spaceships and claim their resources.

**Unique Flavor**

Alicization distinguishes itself from other space 4X games through its focus on:

* **Player Interaction:** Buildings generate profits based on player interaction with their services, creating a dynamic economy where players can earn money by providing valuable services to others.
* **Investment and Profit-Sharing:** The investment system allows players to invest in buildings and share the profits with other investors, fostering alliances and strategic partnerships.
* **Resource Rarity:** Resources have different rarities, affecting their abundance, value, and mining efficiency, leading to a dynamic resource market where players must adapt their strategies to maximize profits.

## Reinforcement Learning Platform

Alicization provides a compelling platform for studying reinforcement learning:

* **Agent Training:** The game's AI agents can be trained using reinforcement learning techniques like Deep Q-Networks (DQN), allowing researchers to experiment with different learning algorithms and evaluate their performance.
* **State Space and Action Space:** The game's large and complex state and action spaces present a challenging yet rewarding environment for reinforcement learning research.
* **Dynamic Environment:** The universe's dynamic nature provides a constantly changing environment that tests agents' adaptability and learning capabilities.

## Contributing

Contributions are welcome! Here are some ways to contribute:

* **Game Design:** Suggest new features, mechanics, and victory conditions.
* **AI Development:** Improve the performance of existing AI agents or create new agents, such as those using genetic algorithms or Multi-Agent Reinforcement Learning (MARL).
* **UI Improvements:** Enhance the web interface for better visualization and user experience.
* **Code Optimization:** Refactor existing code for better performance and readability.
* **Setup Guide:** Provide instructions for setting up the development environment and running the simulation locally.

## Future Directions

* **Victory Conditions:** Implement victory conditions based on different game goals.
* **More AI Agents:** Develop more sophisticated AI agents, including those using genetic algorithms or MARL.
* **More Gameplay Mechanics:** Add more complex gameplay mechanics, such as diplomacy and a technology tree.
* **Improved UI:** Enhance the web interface with features like an interactive map, detailed player statistics, and chat functionality.

## Acknowledgements

This project was inspired by the classic 4X space games and the advancements in agent-based simulation and reinforcement learning. We also acknowledge the contributions of libraries, frameworks, and tools developed by others.

## Disclaimer

This project is still under development and may have bugs or incomplete features. Please feel free to report any issues or suggestions.
