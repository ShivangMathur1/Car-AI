from collections import deque
import torch as T
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import numpy as np

# Deep Q network
class DQN(nn.Module):
    def __init__(self, lr, inputs, layer1, layer2, nActions):
        super(DQN, self).__init__()

        self.l1 = nn.Linear(inputs, layer1)
        self.l2 = nn.Linear(layer1, layer2)
        self.l3 = nn.Linear(layer2, nActions)

        self.optimiser = optim.Adam(self.parameters(), lr=lr)
        self.loss = nn.MSELoss()

        if T.cuda.is_available():
            print("Using CUDA")
        self.device = T.device('cuda:0' if T.cuda.is_available() else 'cpu:0')
        self.to(self.device)
    
    def forward(self, state):
        x = F.relu(self.l1(state))
        x = F.relu(self.l2(x))
        x = self.l3(x)

        return x

# The car agent
class Agent:
    def __init__(self, gamma, epsilon, lr, inputs, nActions, batchSize, memSize=100000, epsilonFinal=0.05, epsilonDecrease=5e-4):
        self.DQN = DQN(lr, inputs, 512, 512, nActions)
        self.DQNext = DQN(lr, inputs, 512, 512, nActions)
        self.DQNext.load_state_dict(self.DQN.state_dict())
        self.actionSpace = [i for i in range(nActions)]

        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilonFinal = epsilonFinal
        self.epsilonDec = epsilonDecrease
        self.batchSize = batchSize
        self.memSize = memSize
        self.memCounter = 0

        self.memory = deque(maxlen=self.memSize)
     
    def store(self, observation):
        self.memory.append(observation)
        self.memCounter += 1
    
    def choose(self, observation):
        rand = np.random.random()
        if rand < self.epsilon:
            action = np.random.choice(self.actionSpace)
        else:
            state = T.tensor([observation]).to(self.DQN.device)
            actions = self.DQN(state)
            action = T.argmax(actions).item()

        return action
    
    def learn(self):
        if self.memCounter < self.batchSize:
            return
        self.DQN.optimizer.zero_grad()

        # Make batch
        maxMem = min(self.memCounter, self.memSize)
        batchIndices = np.random.choice(maxMem, self.batchSize, replace=False)
        batchArange = np.arange(self.batchSize, dtype=np.int32)

        batch = np.array([self.memory[i] for i in batchIndices])
        stateBatch = T.tensor(batch[:, 0]).to(self.DQN.device)
        newStateBatch = T.tensor(batch[:, 1]).to(self.DQN.device)
        rewardBatch = T.tensor(batch[:, 2]).to(self.DQN.device)
        terminalBatch = T.tensor(batch[:, 3]).to(self.DQN.device)
        actionBatch = T.tensor(batch[:, 4])

        qVals = self.DQN(stateBatch)[batchArange, actionBatch]
        qNext = self.DQNext(newStateBatch)
        qNext[terminalBatch] = 0.0
        qTarget = rewardBatch + self.gamma * T.max(qNext, dim=1)[0]

        loss = self.DQN.loss(qTarget, qVals).to(self.DQN.device)
        loss.backward()
        self.DQN.optimizer.step()
        self.updateEpsilon()
    
    def updateEpsilon(self):
        self.epsilon = self.epsilon * self.epsilonDec if self.epsilon > self.epsilonFinal else self.epsilonFinal
    
    def updateNetwork(self):
        self.DQNext.load_state_dict(self.DQN.state_dict())
