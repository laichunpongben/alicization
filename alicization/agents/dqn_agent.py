# dgn_agent.py

from collections import deque
import random

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F


class DQN(nn.Module):
    def __init__(self, input_size, hidden_sizes, output_size):
        super(DQN, self).__init__()
        self.layers = nn.ModuleList()
        self.layers.append(nn.Linear(input_size, hidden_sizes[0]))
        for i in range(len(hidden_sizes) - 1):
            self.layers.append(nn.Linear(hidden_sizes[i], hidden_sizes[i + 1]))
        self.layers.append(nn.Linear(hidden_sizes[-1], output_size))

    def forward(self, x):
        for layer in self.layers[:-1]:
            x = F.relu(layer(x))
        x = self.layers[-1](x)
        return x


class ReplayMemory:
    def __init__(self, capacity):
        self.memory = deque([], maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def sample(self, batch_size):
        return random.sample(self.memory, batch_size)

    def __len__(self):
        return len(self.memory)


class DQNAgent:
    def __init__(
        self,
        actions,
        input_size,
        hidden_sizes,
        output_size,
        gamma=0.99,
        epsilon=1.0,
        epsilon_decay=0.995,
        epsilon_min=0.01,
        learning_rate=0.001,
        memory_size=10000,
        batch_size=32,
        target_update_frequency=10,
    ):

        self.actions = actions
        self.input_size = input_size
        self.hidden_sizes = hidden_sizes
        self.output_size = output_size
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        self.learning_rate = learning_rate
        self.memory_size = memory_size
        self.batch_size = batch_size
        self.target_update_frequency = target_update_frequency
        self.steps_done = 0

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.policy_net = DQN(input_size, hidden_sizes, output_size).to(self.device)
        self.target_net = DQN(input_size, hidden_sizes, output_size).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=learning_rate)
        self.memory = ReplayMemory(memory_size)

    def choose_action(self, state):
        self.steps_done += 1
        if np.random.uniform(0, 1) < self.epsilon:
            return random.randint(0, len(self.actions) - 1)  # Explore
        else:
            with torch.no_grad():
                state = torch.tensor(
                    state, dtype=torch.float32, device=self.device
                ).unsqueeze(0)
                q_values = self.policy_net(state)
                return int(q_values.argmax().item())  # Exploit

    def learn(self):
        if len(self.memory) < self.batch_size:
            return

        transitions = self.memory.sample(self.batch_size)
        state_batch, action_batch, reward_batch, next_state_batch, done_batch = zip(
            *transitions
        )

        state_batch = torch.tensor(state_batch, dtype=torch.float32, device=self.device)
        action_batch = torch.tensor(action_batch, dtype=torch.long, device=self.device)
        reward_batch = torch.tensor(
            reward_batch, dtype=torch.float32, device=self.device
        )
        next_state_batch = torch.tensor(
            next_state_batch, dtype=torch.float32, device=self.device
        )
        done_batch = torch.tensor(done_batch, dtype=torch.bool, device=self.device)

        # Calculate Q-values for the current state
        q_values = self.policy_net(state_batch).gather(1, action_batch.unsqueeze(1))

        # # Calculate Q-values for the next state
        # with torch.no_grad():
        #     next_q_values = self.target_net(next_state_batch).max(1)[0].unsqueeze(1)
        #     next_q_values[done_batch] = 0.0  # Set Q-values to 0 for terminal states

        # # Calculate the target Q-values
        # expected_q_values = reward_batch + self.gamma * next_q_values

        # Double DQN: Use policy net to select the action, but target net to calculate the Q-value
        with torch.no_grad():
            next_actions = self.policy_net(next_state_batch).argmax(dim=1, keepdim=True)
            next_q_values = self.target_net(next_state_batch).gather(1, next_actions)
            next_q_values[done_batch] = 0.0  # Set Q-values to 0 for terminal states

        # Calculate the target Q-values
        expected_q_values = reward_batch.unsqueeze(1) + self.gamma * next_q_values

        # Calculate the loss
        loss = F.smooth_l1_loss(q_values, expected_q_values)

        # Optimize the model
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        # Update target network
        if self.steps_done % self.target_update_frequency == 0:
            self.update_target_net()

        # Decay epsilon
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def update_target_net(self):
        self.target_net.load_state_dict(self.policy_net.state_dict())

    def save_model(self, filename):
        torch.save(self.policy_net.state_dict(), filename)

    def load_model(self, filename):
        self.policy_net.load_state_dict(torch.load(filename))
        self.target_net.load_state_dict(torch.load(filename))
