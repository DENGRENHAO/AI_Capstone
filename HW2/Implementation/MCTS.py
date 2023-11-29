import copy
import random
import math
import time
import STcpClient
import numpy as np
 
class GameState:
    '''
    Class for game state processing
    Attributes:
        mapStat: map state from TCP client
        gameStat: game history from TCP client
    '''
    def __init__(self, mapStat, gameStat):
        self.mapStat = mapStat
        self.gameStat = gameStat

    def is_terminated(self):
        '''
        Check if this game is terminated
        Returns:
            True if all elements in self.mapStat is not zero, else False
        '''
        return True if np.count_nonzero(self.mapStat) == len(self.mapStat) * len(self.mapStat[0]) else False

    def get_actions(self):
        '''
        Get all possible actions from current mapStat
        Returns:
            actions: list of all possible actions
        '''
        actions = []
        for i in range(len(self.mapStat)):
            for j in range(len(self.mapStat[0])):
                if(self.mapStat[i][j] == 0):
                    actions.append(([i, j], 1, 1))
                    for dir in range(1, 7):
                        next_i, next_j = i, j
                        for dist in range(2, 4):
                            [next_i, next_j] = self.Next_Node(next_i, next_j, dir)
                            if(next_i >= 0 and next_i < 12 and next_j >= 0 and next_j < 12 and self.mapStat[next_i][next_j] == 0):
                                actions.append(([i, j], dist, dir))
                            else:
                                break
        
        return actions

    def get_player(self):
        '''
        Get next player and step number from self.gameStat
        Returns:
            player: next player
            next_step: next step
        '''
        max_step = np.max(self.gameStat)
        next_step = max_step + 1
        if max_step % 2 == 0:
            player = 1
        else:
            player = 2
        
        return player, next_step

    def play(self, action):
        '''
        Update self.mapStat and self.gameStat from action
        Arguments:
            action: Action to do
        '''
        [action_i, action_j], dist, dir = action

        next_i = action_i
        next_j = action_j
        player, next_step = self.get_player()
        self.mapStat[next_i][next_j] = player
        self.gameStat[next_i][next_j] = next_step
        for i in range(dist - 1): 
            [next_i, next_j] = self.Next_Node(next_i, next_j, dir)
            self.mapStat[next_i][next_j] = player
            self.gameStat[next_i][next_j] = next_step

    def Next_Node(self, pos_x, pos_y, direction):
        '''
        Input position (x,y) and direction
        Output next node position on this direction
        '''
        if pos_y % 2 == 1:
            if direction == 1:
                return pos_x, pos_y - 1
            elif direction == 2:
                return pos_x + 1, pos_y - 1
            elif direction == 3:
                return pos_x - 1, pos_y
            elif direction == 4:
                return pos_x + 1, pos_y
            elif direction == 5:
                return pos_x, pos_y + 1
            elif direction == 6:
                return pos_x + 1, pos_y + 1
        else:
            if direction == 1:
                return pos_x - 1, pos_y - 1
            elif direction == 2:
                return pos_x, pos_y - 1
            elif direction == 3:
                return pos_x - 1, pos_y
            elif direction == 4:
                return pos_x + 1, pos_y
            elif direction == 5:
                return pos_x - 1, pos_y + 1
            elif direction == 6:
                return pos_x, pos_y + 1

class MCTS_Node:
    '''
    Class Node for MCTS
    Attributes:
        action: The action which its parent do to transfer to this node
        parent: The parent node of this node
        Q: The value of this node
        N: Number of visit of this node
        children: list of child nodes of this node
    '''
    def __init__(self, action=None, parent=None):
        self.action = action
        self.parent = parent
        self.Q = 0
        self.N = 0
        self.children = []
    
    def add_children(self, children):
        '''
        Add children nodes to this node
        Arguments:
            children: list of child nodes
        '''
        for child in children:
            self.children.append(child)

    def UCT_value(self, explore_rate):
        '''
        Calculate UCT_value of this node for select
        Arguments:
            explore_rate: Explore rate for UCT calculation
        Returns:
            float: UCT value of this node
        '''
        explore_rate = 2
        if self.N == 0:
            return 0 if explore_rate == 0 else float('inf')
        else:
            exploit = self.Q / self.N
            explore = math.sqrt(2.0 * math.log(self.parent.N) / self.N)
            return exploit + explore_rate * explore
        
    def average_value(self):
        '''
        Calculate average value of this node for best_node_average_value
        Returns:
            float: Average value of this node
        '''
        if self.N == 0:
            # If this node hasn't been visited, don't select it for best node.
            # Therefore, return -inf
            return float("-inf")
        return self.Q / self.N

class MCTS_Agent:
    '''
    Class of MCTS Agent
    Attributes:
        root_state: A copy of current game state
        root: Root node
        explore_rate: Explore rate for UCT value calculation
        time_out_sec: Time out for searching. Time unit is second
    '''
    def __init__(self, game_state, explore_rate=2, time_out_sec=5):
        self.root_state = copy.deepcopy(game_state)
        self.root = MCTS_Node()
        self.explore_rate = explore_rate
        self.time_out_sec = time_out_sec
    
    def search(self):
        '''
        Do Monte Carlo search for this Monte Carlo Tree
        '''
        epoch = 0
        start_time = time.time()
        # Run search for up to time_out_sec second
        while (time.time() - start_time) <= self.time_out_sec:
            node, state = self.select_node()
            reward = self.simulate(state)
            self.backpropagate(node, reward)
            epoch += 1
        print(f"Search epoch = {epoch}")

    def select_node(self):
        '''
        Select a node with highest UCT value
        '''
        node = self.root
        state = copy.deepcopy(self.root_state)

        while len(node.children) != 0:
            node = self.best_node(node)
            state.play(node.action)

            # Select this node if it hasn't been visited
            if node.N == 0:
                return node, state
            
        # Expand tree if this leaf node was already visited and the game is not terminated
        if not state.is_terminated():
            self.expand(node, state)
            node = random.choice(node.children)
            state.play(node.action)
        return node, state

    def expand(self, parent, state):
        '''
        Expand this leaf node with all possible actions
        Arguments:
            parent: Parent node
            state: Current game state
        '''
        children = []

        for action in state.get_actions():
            children.append(MCTS_Node(action, parent))

        parent.add_children(children)

    def simulate(self, state):
        '''
        Do simulatation from this state until the game is terminated
        Arguments:
            state: Current game state

        Returns:
            reward: Reward for this terminal node. reward = 0 if game terminated after this player's action
            (this player losed because he/she took the last action), else: reward = 1 
        '''
        reward = -1
        # reward = 0

        while not state.is_terminated():
            actions = state.get_actions()
            action = random.choice(actions)
            state.play(action)
            reward = (-1) * reward
            # reward = 1 - reward

        return reward

    def backpropagate(self, node, reward):
        '''
        Back Propagate from terminate node to root node with reward.
        If current player is winner, then its nodes should have reward value = 1. Meanwhile, enemy's node should have reward value = -1. 
        If current player is loser, then its nodes should have reward value = -1. Meanwhile, enemy's node should have reward value = 1. 
        Arguments:
            node: Terminal node
            reward: Reward of this terminal node
        '''
        while node is not None:
            node.Q += reward
            node.N += 1
            node = node.parent
            reward = (-1) * reward
            # reward = 1 - reward

    def best_node(self, node=None):
        '''
        Get the best node which has the highest UCT value
        Arguments:
            node: The node for choosing the best node from its child nodes. If node == None, node = self.root node
        
        Returns:
            node: The best child node with the highest UCT value
        '''
        if not node:
            node = self.root

        max_UCT_value = max(node.children, key = lambda temp_node: temp_node.UCT_value(self.explore_rate)).UCT_value(self.explore_rate)
        max_nodes = [temp_node for temp_node in node.children if temp_node.UCT_value(self.explore_rate) == max_UCT_value]
        node = random.choice(max_nodes)

        return node
    
    def best_node_most_visit(self, node=None):
        '''
        Get the best node which has the most visited count
        Arguments:
            node: The node for choosing the best node from its child nodes. If node == None, node = self.root node
        
        Returns:
            node: The best child node with the most visited count
        '''
        if not node:
            node = self.root

        max_visited_cnt = max(node.children, key = lambda temp_node: temp_node.N).N
        max_nodes = [temp_node for temp_node in node.children if temp_node.N == max_visited_cnt]
        node = random.choice(max_nodes)

        return node
    
    def best_node_average_value(self, node=None):
        '''
        Get the best node which has the highest average value
        Arguments:
            node: The node for choosing the best node from its child nodes. If node == None, node = self.root node
        
        Returns:
            node: The best child node with the highest average value
        '''
        if not node:
            node = self.root


        max_avg_value = max(node.children, key = lambda temp_node: temp_node.average_value()).average_value()
        max_nodes = [temp_node for temp_node in node.children if temp_node.average_value() == max_avg_value]
        node = random.choice(max_nodes)

        return node

def Getstep(mapStat, gameStat):
    '''
    輪到此程式移動棋子
    mapStat: 棋盤狀態 (list of list), 為 12 * 12 矩陣, 0 = 可移動區域, -1 = 障礙, 1 ~ 2 為玩家 1 ~ 2 佔領區域
    gameStat: 棋盤歷史順序
    return Step
    Step: 3 elements, [(x, y), l, dir]
            x, y 表示要畫線起始座標
            l = 線條長度 (1 ~ 3)
            dir = 方向 (1 ~ 6), 對應方向如下圖所示
                1  2
              3  x  4
                5  6
    '''
    #Please write your code here
    #TODO
    game_state = GameState(mapStat, gameStat)
    mcts_agent = MCTS_Agent(game_state, explore_rate=math.sqrt(2), time_out_sec=5.5)
    mcts_agent.search()
    return mcts_agent.best_node_average_value().action

    #Please write your code here
    



# start game
print('start game')
while (True):

    (end_program, id_package, mapStat, gameStat) = STcpClient.GetBoard()
    if end_program:
        STcpClient._StopConnect()
        break
    
    decision_step = Getstep(mapStat, gameStat)
    
    STcpClient.SendStep(id_package, decision_step)
