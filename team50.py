import sys
import random
import time
from copy import deepcopy

class Team50:

    def __init__(self):
        self.pos_weight = ((3,2,3),(2,4,2),(3,2,3)) # weight of winning position[i][j]
        self.boardHeuriStore = {} # store calculated board heuristics
        self.blockHeuriStore = {} # store calculated block heuristics
        self.randTable = [[[[long(0) for k in xrange(2)] for j in xrange(9)] for i in xrange(9)] for a in xrange(2)] # random strings for hash components
        self.boardHash = [long(0) for i in xrange(2)]
        self.blockHash = [[[long(0) for j in xrange(3)] for i in xrange(3)] for a in xrange(2)]
        self.blockPoints = 30
        self.time = 0
        patterns = []

		# diagonal patterns
        patterns.append(((0,0) , (1,1) , (2,2)))

		# straight line patterns (rows and columns)
        for i in xrange(3):
			row_array = [] # i'th row
			col_array = [] # i'th column
			for j in xrange(3):
				row_array.append((i,j))
				col_array.append((j,i))
			patterns.append(tuple(row_array))
			patterns.append(tuple(col_array))
            
        self.patterns = tuple(patterns)
        self.hash_init()

    def hash_init(self):
		# Every (position,player) pair is given a random bit-string
        for a in xrange(2):
            for i in xrange(9):
                for j in xrange(9):
                    for k in xrange(2):
                        self.randTable[a][i][j][k] = long(random.randint(1, 2**64))

    def oppFlag(self, flag):
		# NOT operation on flag
		return 'o' if flag == 'x' else 'x'

    def addMovetoHash(self, cell, player):
		# player -> 0: opponent, 1: us
        a = cell[0]
        x = cell[1]
        y = cell[2]
        self.boardHash[a] ^= self.randTable[a][x][y][player]
        self.blockHash[a][x/3][y/3] ^= self.randTable[a][x][y][player]
        
    def board_heuristic(self, blockHeurs):
        boardHeur = 0
        for a in xrange(2):
            for i in xrange(3):
                for j in xrange(3):
                    if blockHeurs[a][i][j] > 0:
                        boardHeur += 0.02 * self.pos_weight[i][j] * blockHeurs[i][j]

		return boardHeur

    def board_pattern_checker(self, pos_arr, blockHeurs):
        playerCount = 0
        patternHeur = 0
        
        for a in xrange(2):
            for pos in pos_arr:
                val = blockHeurs[a][pos[0]][pos[1]]
                patternHeur += val
                if val < 0:
                    return 0
                elif val == self.blockPoints:
                    playerCount+=1

		multiplier = 1
		if playerCount == 2:
			multiplier = 1.1
		elif playerCount == 3:
			multiplier = 2.3
		elif playerCount == 4:
			multiplier = 50

		return multiplier * patternHeur

    def block_heuristic(self, flag, block):
		# Not just the places of flags, but also their relative position contributes to heuristic
		blockHeur = 0

		for pos_arr in self.patterns:
			blockHeur += self.pattern_checker(flag,block,pos_arr)

		# Finally, contribution of place (for settling tie-breakers, etc)
		for i in xrange(3):
			for j in xrange(3):
				if block[i][j] == flag:
					blockHeur += 0.1 * self.pos_weight[i][j]

		return blockHeur

    def pattern_checker(self, flag, block, pos_array):
		playerCount = 0
		for pos in pos_array:
			if block[pos[0]][pos[1]] == flag:
				playerCount += 1
			elif block[pos[0]][pos[1]] == self.oppFlag(flag):
				return -1
		if playerCount == 1:
			return 3
		elif playerCount == 2:
			return 11
		return 0

    def heuristic(self, flag, board):
        if (self.boardHash[0], self.boardHash[1], flag) in self.boardHeuriStore:
            return self.boardHeuriStore[(self.boardHash[0], self.boardHash[1], flag)]
            
        total = 0
        
        blocks = board.small_boards_status
        b = board.big_boards_status
        blockHeurs = [[[long(0) for j in xrange(3)] for i in xrange(3)] for a in xrange(2)]
        
        for a in xrange(2):
            for i in xrange(3):
                for j in xrange(3):
                    if blocks[a][i][j]==flag:
                        blockHeurs[a][i][j] = self.blockPoints
                    elif blocks[a][i][j]==self.oppFlag(flag) or blocks[a][i][j]=='d':
                        blockHeurs[a][i][j] = -1
                    else:
                        block = tuple([tuple(b[a][3*i + x][3*j:3*(j+1)]) for x in xrange(3)])
                        if (self.blockHash[a][i][j],flag) in self.blockHeuriStore:
                            blockHeurs[a][i][j] = self.blockHeuriStore[(self.blockHash[a][i][j],flag)]
                        else:
                            blockHeurs[a][i][j] = self.block_heuristic(flag,block)
                            self.blockHeuriStore[(self.blockHash[a][i][j],flag)] = blockHeurs[a][i][j]

		for pos_arr in self.patterns:
			total += self.board_pattern_checker(pos_arr,blockHeurs)

		total += self.board_heuristic(blockHeurs)

		self.boardHeuriStore[(self.boardHash,flag)] = total
		return total

    def minimax(self, board, flag, depth, maxDepth, alpha, beta, old_move):

		checkGoal = board.find_terminal_state()

		if checkGoal[1] == 'WON':
			if checkGoal[0] == self.who:
				return float("inf"), "placeholder"
			else:
				return float("-inf"), "placeholder"
		elif checkGoal[1] == 'DRAW':
			return -100000, "placeholder"

		if depth == maxDepth:
			return ( self.heuristic(self.who,board) - self.heuristic(self.oppFlag(self.who),board) ) , "placeholder"

		validCells = board.find_valid_move_cells(old_move)

		isMax = (flag==self.who)

		if isMax:
			maxVal = float("-inf")
			maxInd = 0
			for i in xrange(len(validCells)):

				cell = validCells[i]
				board.update(old_move,cell,flag)
				self.addMovetoHash(cell,1)

				val = self.minimax(board,self.oppFlag(flag),depth+1,maxDepth,alpha,beta,cell)[0]

				if val > maxVal:
					maxVal = val
					maxInd = i
				if maxVal > alpha:
					alpha = maxVal

				board.big_boards_status[cell[0]][cell[1]][cell[2]] = '-'
				board.small_boards_status[cell[0]][cell[1]/3][cell[2]/3] = '-'

				self.addMovetoHash(cell,1)
				if beta <= alpha:
					break
			return maxVal, validCells[maxInd]

		else:
			minVal = float("inf")
			for i in xrange(len(validCells)):

				cell = validCells[i]
				board.update(old_move,cell,flag)
				self.addMovetoHash(cell,0)

				val = self.minimax(board,self.oppFlag(flag),depth+1,maxDepth,alpha,beta,cell)[0]

				if val < minVal:
					minVal = val
				if minVal < beta:
					beta = minVal

				board.big_boards_status[cell[0]][cell[1]][cell[2]] = '-'
				board.small_boards_status[cell[0]][cell[1]/3][cell[2]/3] = '-'

				self.addMovetoHash(cell,0)
				if beta <= alpha:
					break
			return minVal, "placeholder"

    def move(self, board, old_move, flag):
		self.time = time.time()
		
		if old_move == (-1,-1,-1):
			self.addMovetoHash((1,3,3),1)
			return (1,3,3)
		else:
			if board.big_boards_status[old_move[0]][old_move[1]][old_move[2]] == self.oppFlag(flag):
				self.addMovetoHash(old_move,0)
				
		self.who = flag
		
		maxDepth = 3
		
		validCells = board.find_valid_move_cells(old_move)
		bestMove = validCells[0]
		
		try:
			while True:
				if self.time - time.time() > 20:
					break
				self.boardHashSafeCopy = deepcopy(self.boardHash)
				self.blockHashSafeCopy = deepcopy(self.blockHash)
				b = deepcopy(board)
				move = self.minimax(b,flag,0,maxDepth,float("-inf"),float("inf"),old_move)[1]
				bestMove = move
				maxDepth += 1
				del b

		except Exception as e:
			self.boardHash = deepcopy(self.boardHashSafeCopy)
			self.blockHash = deepcopy(self.blockHashSafeCopy)
			pass

		self.addMovetoHash(bestMove,1)
		
		return bestMove
