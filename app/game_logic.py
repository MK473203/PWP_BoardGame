"""
Use included apply_move() function to play a move on a specific board.
"""

# State contains next team at index 0.
# After removing team, board state represents board indexes flattened into 1 dimension.
# For example, tictactoe board with indexes is like:
# 0 1 2
# 3 4 5
# 6 7 8
# It becomes "012345678" after flattening. Checkers is similar, but with 8x8 sized board.
# Empty board position is represented by "-". For example in tictactoe "---------" is empty board.

# Tictactoe:
#  mark of team 1 = "X"
#  mark of team 2 = "O"
#  game type = "tictactoe"
#  board size = 3x3, indexes 0-8
#  move = index to place next mark on.

# Checkers:
#  black team starts at the bottom, white at the top
#  all marks always move diagonally, can jump over 1 enemy mark to destroy it
#  marks only move forward, while king marks can also move backwards
#  destroying enemy mark can be done backwards by all marks
#  a mark that reaches the opposite row becomes king
#  mark of team 1 = "b", "B" for king
#  mark of team 2 = "w", "W" for king
#  game type = "checkers"
#  board size = 8x8, indexes 0-63
#  move = tuple like (1, 2), where a mark is moved from index 1 to index 2.

def apply_move(move: int | list[tuple], old_state: str, game_type: str) -> tuple[str, bool] | None:
    """ Applies a move to a board state.
    
    Returns None if an argument is invalid.
    
    Arguments:
    - move (int or list of tuples): Move(s) to play
    - old_state (str): Board state to apply the move to
    - game_type (str): Which game is being played

    Returns 2 values as a tuple (unless move is invalid):
    - New board state (str)
    - Game result (int):
       * -1 == Game has not finished
       * 0 == Draw
       * 1 == Team 1 won
       * 2 == Team 2 won
    """
    team = int(old_state[0])
    new_state = old_state[1:]

    # Play the move
    if game_type == "tictactoe":
        if not (isinstance(move, int) and is_valid_move(move, team, new_state, game_type)):
            return None
        next_mark = "X" if (team == 1) else "O"
        new_state = new_state[:move] + next_mark + new_state[move+1:]
    elif game_type == "checkers":
        if not (isinstance(move, list) and all(isinstance(m, tuple) for m in move)):
            return None
        prev_move_to = 0
        for m_index, m in enumerate(move):
            if not is_valid_move(m, team, new_state, game_type):
                if m_index == 0:
                    return None
                break

            # Get indexes from move tuple
            move_from = m[0]
            move_to = m[1]
            middle = (move_to + move_from) / 2

            # Chained moves must start from the end of previous move and jump over an enemy mark
            if m_index > 0 and (prev_move_to != move_from or middle % 1 != 0):
                break
            prev_move_to = move_to

            # If jumped over a mark, remove it
            if middle % 1 == 0:
                middle = int(middle)
                new_state = new_state[:middle] + "-" + new_state[middle+1:]

            # Move mark to new position, converting it to king if
            #  it reached the opponents side of the board
            if move_to // 8 == (0 if (team == 1) else 7):
                new_state = new_state[:move_to] + new_state[move_from].upper() + new_state[move_to+1:]
            else:
                new_state = new_state[:move_to] + new_state[move_from] + new_state[move_to+1:]
            new_state = new_state[:move_from] + "-" + new_state[move_from+1:]

    # Check win conditions
    win_state = get_winner(new_state, team, game_type)

    # Add next team to state
    next_team = 2 if (team == 1) else 1
    new_state = str(next_team) + new_state

    return new_state, win_state

# Helper functions for local use
## Move validation
def is_valid_move(move: int | tuple, team: int, state: str, game_type: str) -> bool:
    """
    Returns True if move is valid, otherwise returns False.
    """
    try:
        if game_type == "tictactoe" and state[move] == "-":
            return True
        if game_type == "checkers":
            move_from = int(move[0])
            move_to = int(move[1])
            middle = int((move_from + move_to) / 2)

            enemy_mark = "w" if (team == 1) else "b"
            friend_mark = "b" if (team == 1) else "w"

            # Check that indexes are in range
            if not (0 <= move_from <= 63 and 0 <= move_to <= 63):
                return False

            # Only move friendly mark to empty space
            if state[move_to] != "-" or state[move_from].lower() != friend_mark:
                return False

            # Get position coordinates, position (0,0) is top left, (7,7) is bottom right
            row_change = move_from // 8 - move_to // 8 # Negative means down, positive means up
            col_change = move_to % 8 - move_from % 8 # Negative means left, positive means right

            # Only move diagonally and jump over enemy pieces
            if not (
                (row_change in (-1, 1) and col_change in (-1, 1)) or
                (row_change in (-2, 2) and col_change in (-2, 2) and
                 state[middle].lower() == enemy_mark)
            ):
                return False

            # Only move towards opponent side, unless mark is a king or jumping over opponent mark
            is_king = state[move_from].isupper()
            if is_king or not (
                row_change == -1 and friend_mark == "b" or
                row_change == 1 and friend_mark == "w"
            ):
                return True
    except (IndexError, TypeError, ValueError):
        pass
    return False

## Win condition checker
tictactoe_winning_lines = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
def get_winner(state: str, team, game_type: str) -> int:
    """
    Returns game conclusion state:
    * -1 = not finished
    * 0 = no winner
    * 1 = team 1 won
    * 2 = team 2 won
    """
    if game_type == "tictactoe":
        result = 0
        for indexes in tictactoe_winning_lines:
            marks = list(state[i] for i in indexes)

            # Check if one team has filled the row
            if marks[0] == marks[1] == marks[2] != "-":
                return 1 if (marks[0] == "X") else 2

            # Check if the row could still be filled by only "X" or only "O"
            if not ("X" in marks and "O" in marks):
                result = -1
        return result

    if game_type == "checkers":
        state_lower = state.lower()
        w_exists = "w" in state_lower
        b_exists = "b" in state_lower

        # Check if one team has no more marks
        if b_exists and not w_exists:
            return 1
        if w_exists and not b_exists:
            return 2

        # Both teams have marks (empty board is not possible)
        # Keep playing if current player can play a valid move
        # If valid move is not possible, opponent wins
        if checkers_move_exists(team, state):
            return -1
        else:
            return 2 if (team == 1) else 1
    return 0

## Checkers valid moves analysis
def checkers_move_exists(team: int, state: str) -> bool:
    """
    Check if given team can play a valid move.
    
    Returns True if a valid move exists, returns False otherwise
    """
    friend_mark = "b" if (team == 1) else "w"
    moves = [-18, 18, -14, 14, -9, 9, -7, 7]

    # Gather indexes of given team's marks
    indexes = list(tup[0] for tup in enumerate(state) if tup[1] == friend_mark)

    for index in indexes:
        # Check if any move is possible for mark at current index
        for move in moves:
            new_index = index + move
            if is_valid_move((index, new_index), team, state, game_type="checkers"):
                return True
    return False
