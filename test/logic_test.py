""" Tests for game logic. """
from app.game_logic import apply_move

DEFAULT_STATE = {
    "tictactoe": "1---------",
    "checkers": "1"
        + "-w-w-w-w"
        + "w-w-w-w-"
        + "--------"*4
        + "-b-b-b-b"
        + "b-b-b-b-"
}

def test_state_updates():
    """ State is updated correctly """
    # Tictacto
    assert apply_move(5, "1---------", game_type="tictactoe")[0] == "2-----X---"
    assert apply_move(8, "2-------X-", game_type="tictactoe")[0] == "1-------XO"

    # Checkers
    state = DEFAULT_STATE["checkers"]
    test_state1 = apply_move([(49, 42)], state, game_type="checkers")[0][1:]
    assert test_state1[49] == "-"
    assert test_state1[42] == "b"
    test_state2 = apply_move([(8, 17)], "2" + state[1:], game_type="checkers")[0][1:]
    assert test_state2[8] == "-"
    assert test_state2[17] == "w"

def test_invalid_moves():
    """ Invalid moves return None """
    # Tictactoe
    state = DEFAULT_STATE["tictactoe"]
    assert apply_move(-1, state, game_type="tictactoe") is None
    assert apply_move(9, state, game_type="tictactoe") is None
    assert apply_move(0, "2X--------", game_type="tictactoe") is None

    # Checkers
    state = DEFAULT_STATE["checkers"]
    assert apply_move((8, 17), state, game_type="checkers") is None     # Wrong team moving
    assert apply_move((49, 58), state, game_type="checkers") is None    # Moving on top of own mark
    assert apply_move((56, 42), state, game_type="checkers") is None    # Eating own mark

def test_win_states():
    """ Correct win-state is returned """
    # Tictactoe
    state = DEFAULT_STATE["tictactoe"]
    assert apply_move(0, state, game_type="tictactoe")[1] == -1
    assert apply_move(2, "2XX-OOXXXO", game_type="tictactoe")[1] == 0
    assert apply_move(2, "1XX-OO----", game_type="tictactoe")[1] == 1
    assert apply_move(2, "2XX-XOXOXX", game_type="tictactoe")[1] == 2

    # Checkers, no win-state 0, as first team to be unable to move loses
    state = DEFAULT_STATE["checkers"]
    winning_b_example = "1" + "--------"*6 + "-----w--" + "------b-"
    winning_w_example = "2" + "--------"*6 + "-----b--" + "------w-"

    assert apply_move([(49, 42)], state, game_type="checkers")[1] == -1
    assert apply_move([(62, 44)], winning_b_example, game_type="checkers")[1] == 1
    assert apply_move([(62, 44)], winning_w_example, game_type="checkers")[1] == 2
