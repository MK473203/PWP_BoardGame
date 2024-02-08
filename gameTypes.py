from enum import Enum

class gameType(Enum):
	TICTACTOE = 1

defaultStates = {
	gameType.TICTACTOE : "---------"
}
