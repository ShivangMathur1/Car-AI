import numpy as np
import matplotlib.pyplot as plt
from Environment import Game
from Agent import Agent

env = Game()
## Not saving 

nActions = env.nActions
nInputs = env.nInputs

brain = Agent(gamma=0.99, epsilon=0.95, lr=0.002, inputs=nInputs, nActions=5,memSize=1000000 , batchSize=32, epsilonDecrease=0.02)
episodes = 1
scores = []

for i in range(episodes):
    done = False
    state = env.reset()
    score = 0

    if i % 10 == 4:
        brain.updateNetwork()
    j = 0

    while not done and j < 1500:
        action = brain.choose(state)
        newState, reward, done = env.step(action)

        score += reward

        if i % 5 == 0:
            env.render()
        brain.store((state, newState, reward, done, action))
        brain.learn()

        state = newState
        j += 1

    scores.append(score)
    avgScore = np.mean(scores[-100:])
    print("Episode: ", i, "\tScore: ", score, "\tAverage Score: ", avgScore, "\tEpsilon: ", brain.epsilon)

    brain.updateEpsilon()

env.close()

brain.save('./car_model.pt')
x = [i + 1 for i in range(episodes)]
plt.plot(x, scores)
plt.show()