"""
Use included apply_move() function to play a move on a specific board.
"""

def apply_move(move: int | tuple, old_state: str, game_type: str) -> tuple[str, bool] | None:
    """ Applies a move to a board state.
    
    Returns None if move is invalid.
    
    Arguments:
    - move (int or tuple): Move to play
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
    # Check validity
    if not is_valid_move(move, old_state, game_type):
        return None

    # Play the move
    new_state = old_state
    if game_type == "tictactoe":
        empty_cells = old_state.count("-")
        next_mark = "X" if (empty_cells % 2 == 1) else "O"
        new_state[move] = next_mark
    elif game_type == "checkers":
        pass #TODO

    # Check win conditions
    win_state = get_winner(new_state, game_type)

    return new_state, win_state

# Helper functions for local use
## Move validation
def is_valid_move(move: int, board_state: str, game_type: str) -> bool:
    """
    Returns True if move is valid, otherwise returns False.
    """
    try:
        if game_type == "tictactoe" and board_state[move] == "-":
            return True
        if game_type == "checkers":
            return True #TODO
    except IndexError:
        pass
    return False

## Win condition checker
tictactoe_winning_lines = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
def get_winner(board_state: str, game_type: str) -> int:
    """
    Returns game conclusion state:
    * -1 = not finished
    * 0 = no winner
    * 1 = team 1 won
    * 2 = team 2 won
    """
    result = 0
    if game_type == "tictactoe":
        for indexes in tictactoe_winning_lines:
            marks = list(board_state(i) for i in indexes)
            if marks[0] == marks[1] == marks[2] != "-":
                # Winner found, return winning team
                return 1 if (marks[0] == "X") else 2
            if not ("X" in marks and "O" in marks):
                # If any line could be filled by one team, continue game
                result = -1
    elif game_type == "checkers":
        pass #TODO
    return result
