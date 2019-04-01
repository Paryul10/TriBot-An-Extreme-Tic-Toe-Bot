'''
Team 25
'''

import datetime
import time
import copy
import random


class Team25:
    '''
    Main class containing all functions pertaining to the bot
    '''

    def __init__(self):
        self.cell_weight = [[3, 2, 3], [2, 4, 2], [3, 2, 3]]
        self.global_rand_table = [[[long(0) for k in xrange(2)] for i in xrange(9)] for j in xrange(9)]
        self.small_board_heuristic = {}
        self.total_board_hash = long(0)
        self.big_board_heuristic = {}
        self.total_heuristic = {}
        self.big_board_hash = [long(0), long(0)]
        self.small_board_hash = ([[long(0) for i in range(3)] for j in range(3)], [[long(0) for i in range(3)] for j in range(3)])
        patterns = []
        self.start_time = 0
        self.time_limit = datetime.timedelta(seconds=20)
        self.win_small_board = 30
        self.debug = False
        self.ids = False

        # rows , columns and diagonals
        for i in xrange(3):
            row_arr = []
            for j in xrange(3):
                row_arr.append((i, j))
            patterns.append(tuple(row_arr))

        for i in xrange(3):
            col_arr = []
            for j in xrange(3):
                col_arr.append((j, i))
            patterns.append(tuple(col_arr))

        self.global_hash()

        diag_arr1 = []
        diag_arr1.append((0, 2))
        diag_arr1.append((1, 1))
        diag_arr1.append((2, 0))
        patterns.append(tuple(diag_arr1))

        diag_arr2 = []
        diag_arr2.append((0, 0))
        diag_arr2.append((1, 1))
        diag_arr2.append((2, 2))
        patterns.append(tuple(diag_arr2))

        self.patterns = tuple(patterns)

        if self.debug:
            print self.patterns


    def opponent_marker(self, flag):
        if flag == 'x':
            return 'o'
        else:
            return 'x'

    def move(self, board, old_move, flag):
        if old_move == (-1, -1, -1):
            self.update_hash((0, 4, 4), 1)
            return (0, 4, 4)
        
        self.start_time = datetime.datetime.utcnow()
        
        if self.ids:
            max_depth = 3
        else:
            max_depth = 5        

        self.turn = flag

        if board.big_boards_status[old_move[0]][old_move[1]][old_move[2]] == self.opponent_marker(flag):
            self.update_hash(old_move, 0)

        num_valid_moves = len(board.find_valid_move_cells(old_move))

        if num_valid_moves > 50:
            max_depth = 4

        best_move = ()

        if self.ids:
            max_depth = 3
            while datetime.datetime.utcnow() - self.start_time < self.time_limit:
                board_copy = copy.deepcopy(board)
                (temp_val, temp_move) = self.minimax(board_copy, float("-inf"), float("inf"), flag, 0, max_depth, old_move)
                if temp_val != -111:
                    best_move = temp_move
                if self.debug:
                    print datetime.datetime.utcnow() - self.start_time
                    print 'time limit', self.time_limit
                    print max_depth
                if num_valid_moves <= 50:
                    max_depth += 1
                else:
                    del board_copy
                    break
                del board_copy
        else:
            board_copy = copy.deepcopy(board)
            (temp_val, temp_move) = self.minimax(board_copy, float("-inf"), float("inf"), flag, 0, max_depth, old_move)
            best_move = temp_move
            if self.debug:
                print datetime.datetime.utcnow() - self.start_time
                print 'time limit', self.time_limit
                print max_depth
            del board_copy

        self.update_hash(best_move, 1)
        if self.debug:
            print best_move
        return best_move


    def minimax(self, board, alpha, beta, flag, current_depth, max_depth, old_move):
        if self.ids:
            if datetime.datetime.utcnow() - self.start_time > self.time_limit:
                return -111, (-1, -1, -1)

        check_goal_state = board.find_terminal_state()

        if check_goal_state[1] == 'WON':
            if check_goal_state[0] == self.turn:
                return float("inf"), ()
            else:
                return float("-inf"), ()
        elif check_goal_state[1] == 'DRAW':
            return -100000, ()

        if current_depth == max_depth:
            if (self.total_board_hash, flag) in self.total_heuristic:
                return self.total_heuristic[(self.total_board_hash, flag)], ()
            
            tot = (self.heuristic(board, 0, self.turn) + self.heuristic(board, 1, self.turn) - self.heuristic(board, 0, self.opponent_marker(self.turn)) - self.heuristic(board, 1, self.opponent_marker(self.turn))), ()
            if self.debug:
                print 'val = ' ,tot[0]
            return tot

        valid_moves = board.find_valid_move_cells(old_move)
        random.shuffle(valid_moves)

        if flag == self.turn:
            max_utility = float("-inf")
            move_ind = 0
            num_moves = len(valid_moves)

            for i in xrange(num_moves):
                current_move = valid_moves[i]
                board.update(old_move, current_move, flag)
                self.update_hash(current_move, 1)
                board_num = current_move[0]
                x = current_move[1]
                y = current_move[2]

                if self.ids:
                    if datetime.datetime.utcnow() - self.start_time > self.time_limit:
                        board.big_boards_status[board_num][x][y] = '-'
                        board.small_boards_status[board_num][x/3][y/3] = '-'
                        self.update_hash(current_move, 1)
                        return -111, (-1, -1, -1)

                node_val = self.minimax(board, alpha, beta, self.opponent_marker(flag), current_depth+1, max_depth, current_move)[0]
                
                if self.ids:
                    if datetime.datetime.utcnow() - self.start_time > self.time_limit:
                        board.big_boards_status[board_num][x][y] = '-'
                        board.small_boards_status[board_num][x/3][y/3] = '-'
                        self.update_hash(current_move, 1)
                        return -111, (-1, -1, -1)

                if node_val > max_utility:
                    max_utility = node_val
                    move_ind = i
                if max_utility > alpha:
                    alpha = max_utility

                board.big_boards_status[board_num][x][y] = '-'
                board.small_boards_status[board_num][x/3][y/3] = '-'
                self.update_hash(current_move, 1)

                if beta <= alpha:
                    break
                
                if self.debug:
                    print alpha, beta

            return max_utility, valid_moves[move_ind]
        else:
            min_utility = float("inf")
            move_ind = 0
            num_moves = len(valid_moves)

            for i in xrange(num_moves):
                current_move = valid_moves[i]
                board.update(old_move, current_move, flag)
                self.update_hash(current_move, 0)
                board_num = current_move[0]
                x = current_move[1]
                y = current_move[2]

                if self.ids:
                    if datetime.datetime.utcnow() - self.start_time > self.time_limit:
                        board.big_boards_status[board_num][x][y] = '-'
                        board.small_boards_status[board_num][x/3][y/3] = '-'
                        self.update_hash(current_move, 1)
                        return -111, (-1, -1, -1)

                node_val = self.minimax(board, alpha, beta, self.opponent_marker(flag), current_depth+1, max_depth, current_move)[0]
                
                if self.ids:
                    if datetime.datetime.utcnow() - self.start_time > self.time_limit:
                        board.big_boards_status[board_num][x][y] = '-'
                        board.small_boards_status[board_num][x/3][y/3] = '-'
                        self.update_hash(current_move, 0)
                        return -111, (-1, -1, -1)

                if node_val < min_utility:
                    min_utility = node_val
                    move_ind = i
                if min_utility < beta:
                    beta = min_utility

                board.big_boards_status[board_num][x][y] = '-'
                board.small_boards_status[board_num][x/3][y/3] = '-'
                self.update_hash(current_move, 0)

                if beta <= alpha:
                    break

            return min_utility, ()


    def heuristic(self, board, big_board_num, flag):
        if (self.big_board_hash[big_board_num], flag) in self.big_board_heuristic:
            return self.big_board_heuristic[(self.big_board_hash[big_board_num], flag)]
        
        utility = 0

        decision_board = board.small_boards_status[big_board_num]
        play_board = board.big_boards_status[big_board_num]
        decision_board_heuristics = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]

        for i in xrange(3):
            for j in xrange(3):
                if decision_board[i][j] == flag:
                    decision_board_heuristics[i][j] = self.win_small_board
                elif decision_board[i][j] == self.opponent_marker(flag):
                    decision_board_heuristics[i][j] = -1
                elif decision_board[i][j] == 'd':
                    decision_board_heuristics[i][j] = -1
                else:
                    small_play_board = tuple([tuple(play_board[3*i + x][3*j:3*(j+1)]) for x in xrange(3)])
                    if (self.small_board_hash[big_board_num][i][j], flag) in self.small_board_heuristic:
                        if self.debug:
                            print self.small_board_heuristic[(self.small_board_hash[big_board_num][i][j], flag)]
                        decision_board_heuristics[i][j] = self.small_board_heuristic[(self.small_board_hash[big_board_num][i][j], flag)]
                    else:
                        if self.debug:
                            print "Compute"
                        decision_board_heuristics[i][j] = self.compute_small_board_heuristic(small_play_board, flag)
                        self.small_board_heuristic[(self.small_board_hash[big_board_num][i][j], flag)] = decision_board_heuristics[i][j]

        
        for pattern in self.patterns:
            utility += self.decision_board_pattern_checker(pattern, decision_board_heuristics, board.small_boards_status[big_board_num], flag)

        for i in xrange(3):
            for j in xrange(3):
                if decision_board_heuristics[i][j] > 0:
                    utility += 0.02 * decision_board_heuristics[i][j] * self.cell_weight[i][j]

        if self.debug:
            print utility

        return utility

    def compute_small_board_heuristic(self, small_play_board, flag):
        small_play_board_heuristic = 0

        for pattern in self.patterns:
            if self.debug:
                print pattern
            small_play_board_heuristic += self.small_board_pattern_checker(pattern, small_play_board, flag)

        for i in xrange(3):
            for j in xrange(3):
                if small_play_board[i][j] == flag:
                    if self.debug:
                        print self.cell_weight[i][j]
                    small_play_board_heuristic += 0.1 * self.cell_weight[i][j]

        if self.debug:
            print small_play_board_heuristic

        return small_play_board_heuristic


    def decision_board_pattern_checker(self, pattern, decision_board_heuristics, decision_board, flag):
        player_count = 0
        opponent_count = 0
        pattern_heuristic = 0

        for pos in pattern:
            if self.debug:
                print pos
            val = decision_board_heuristics[pos[0]][pos[1]]
            pattern_heuristic += val
            if val < 0:
                if decision_board[pos[0]][pos[1]] == self.opponent_marker(flag):
                    opponent_count += 1
                else:
                    return 0
            elif val == self.win_small_board:
                player_count += 1
        
        if self.debug:
            print player_count, opponent_count

        multiplier = 1
        if opponent_count == 0:
            if player_count == 2: 
                multiplier = 3
            elif player_count == 3:
                multiplier = 50

        elif opponent_count == 1:
            return 0

        elif opponent_count == 2:
            if player_count == 0:
                return 0
            elif player_count == 1:
                multiplier = 14
        
        elif opponent_count == 3:
            return 0
        
        return multiplier * pattern_heuristic


    def small_board_pattern_checker(self, pattern, small_play_board, flag):
        player_count = 0
        opponent_count = 0

        for pos in pattern:
            if self.debug:
                print pos
            if small_play_board[pos[0]][pos[1]] == flag:
                if self.debug:
                    print "got one"
                player_count += 1
            elif small_play_board[pos[0]][pos[1]] == self.opponent_marker(flag):
                if self.debug:
                    print "lost one"
                opponent_count += 1
        
        if self.debug:
            print player_count, opponent_count

        if opponent_count == 0:
            if player_count == 2:
                return 5
            if player_count == 3:
                return 25

        elif opponent_count == 2:
            if player_count == 1:
                return 2.5
        
        return 0


    def global_hash(self):
        for i in xrange(9):
            for j in xrange(9):
                for k in xrange(2):
                    self.global_rand_table[i][j][k] = long(random.randint(1, 2**64))


    def update_hash(self, current_move, flag):
        board_num = current_move[0]
        self.total_board_hash ^= self.global_rand_table[current_move[1]][current_move[2]][flag]
        self.big_board_hash[board_num] ^= self.global_rand_table[current_move[1]][current_move[2]][flag]
        self.small_board_hash[board_num][current_move[1]/3][current_move[2] /3] ^= self.global_rand_table[current_move[1]][current_move[2]][flag]
