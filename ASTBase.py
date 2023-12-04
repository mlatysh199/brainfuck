from enum import Enum

class BaseTokenType(Enum):
	EOF = -1

class Token:
	def __init__(self, type: BaseTokenType, value) -> None:
		self.type = type
		self.value = value
	
	def __eq__(self, __value: object) -> bool:
		return (type(__value) == Token and __value.type == self.type and __value.value == self.value) or __value == self.value
	
	def __ne__(self, __value: object) -> bool:
		return not self.__eq__(__value)

class BaseLexer:
	def __init__(self) -> None:
		self.pos = 0

	def next_token(self) -> Token:
		raise NotImplementedError()

	def get_position(self) -> int:
		return self.pos
	
	def set_position(self, pos: int) -> None:
		self.pos = pos