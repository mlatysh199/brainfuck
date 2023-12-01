from enum import Enum

class TokenType(Enum):
	EOF = -1
	Breaker = 0
	Word = 1
	Terminal = 2
	Or = 3
	OneOrMore = 4
	ZeroOrMore = 5
	ZeroOrOne = 6
	Parenthesis = 7
	Setter = 8

# Token container
class Token:
	def __init__(self, type: TokenType, value) -> None:
		self.type = type
		self.value = value

class Lexer:
	word_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_"
	ignore_chars = " \t"
	break_chars = "\n"
	terminal_chars = "\"'"
	or_chars = "|"
	one_or_more_chars = "+"
	zero_or_more_chars = "*"
	zero_or_one_chars = "?"
	parenthesis_chars = "()"
	setter_exp = ["::="]
	
	def __init__(self, stream : str) -> None:
		self.stream = stream
		self.pos = 0

	def process_terminal(self) -> Token:
		terminal_start = self.stream[self.pos]
		self.pos += 1
		original_pos = self.pos
		while self.pos < len(self.stream) and self.stream[self.pos] != terminal_start: self.pos += 1
		if self.pos > len(self.stream): return Token(TokenType.EOF, None)
		self.pos += 1
		return Token(TokenType.Terminal, self.stream[original_pos:self.pos - 1])

	def process_word(self) -> Token:
		original_pos = self.pos
		while self.pos < len(self.stream) and self.stream[self.pos] in self.word_chars: self.pos += 1
		return Token(TokenType.Word, self.stream[original_pos:self.pos])
	
	def next_token(self) -> Token:
		if self.pos >= len(self.stream): return Token(TokenType.EOF, None)
		char = self.stream[self.pos]
		while True:
			if char in self.ignore_chars: self.pos += 1
			else: break
			if self.pos >= len(self.stream): return Token(TokenType.EOF, None)
			char = self.stream[self.pos]
		if char in self.word_chars: return self.process_word()
		elif char in self.terminal_chars: return self.process_terminal()
		elif self.stream[self.pos:self.pos + 3] in self.setter_exp:
			self.pos += 3
			return Token(TokenType.Setter, None)
		else: self.pos += 1
		if char in self.or_chars: return Token(TokenType.Or, None)
		elif char in self.break_chars: return Token(TokenType.Breaker, None)
		elif char in self.parenthesis_chars: return Token(TokenType.Parenthesis, char)
		elif char in self.one_or_more_chars: return Token(TokenType.OneOrMore, None)
		elif char in self.zero_or_more_chars: return Token(TokenType.ZeroOrMore, None)
		elif char in self.zero_or_one_chars: return Token(TokenType.ZeroOrOne, None)
		raise KeyError(f"{char} is not a valid character.")

	def get_position(self) -> int:
		return self.pos
	
	def set_position(self, pos: int) -> None:
		self.pos = pos

class Parser:

	def __init__(self, stream: str):
		Parser.lexer = Lexer(stream)

	class AstNode:
		def __init__(self) -> None:
			self.lexer_pos = Parser.lexer.get_position()
			self.children: list["Parser.AstNode"] = []
		
		# Virtual method
		def match(self) -> bool:
			return False
		
		def save(self, node: "Parser.AstNode") -> None:
			self.children.append(node)

		def jump(self) -> None:
			while True:
				node = Parser.TerminalAstNode(TokenType.Breaker)
				if not node.match(): break
				self.save(node)
		
		def __del__(self) -> None:
			self.children.clear()
			Parser.lexer.set_position(self.lexer_pos)

	class TerminalAstNode(AstNode):

		def __init__(self, token_type: TokenType) -> None:
			super().__init__()
			self.token_type = token_type
			self.value = None

		def match(self) -> bool:
			token = Parser.lexer.next_token()
			if token.type == self.token_type:
				self.value = token.value
				return True
			return False
	
	class Term(AstNode):
		def match(self):
			node = Parser.TerminalAstNode(TokenType.Parenthesis)
			if node.match():
				if node.value != "(": return False
				self.save(node)
				node = Parser.Alternation()
				if not node.match(): return False
				self.save(node)
				node = Parser.TerminalAstNode(TokenType.Parenthesis)
				if not node.match() or node.value != ")": return False
				self.save(node)
				return True
			del node
			node = Parser.TerminalAstNode(TokenType.Terminal)
			if node.match():
				self.save(node)
				return True
			del node
			node = Parser.TerminalAstNode(TokenType.Word)
			if node.match():
				self.save(node)
				return True
			return False
	
	class Factor(AstNode):
		node_types = [
			TokenType.OneOrMore,
			TokenType.ZeroOrMore,
			TokenType.ZeroOrOne
		]

		def match(self):
			node = Parser.Term()
			if not node.match(): return False
			self.save(node)

			for i in self.node_types:
				node = Parser.TerminalAstNode(i)
				if node.match():
					self.save(node)
					break
				del node
			return True
	
	class Concatenation(AstNode):
		def match(self):
			node = Parser.Factor()
			if not node.match(): return False
			self.save(node)
			node = Parser.TerminalAstNode(TokenType.Breaker)
			while not node.match():
				del node
				node = Parser.Factor()
				if not node.match(): return True
				self.save(node)
				node = Parser.TerminalAstNode(TokenType.Breaker)
			return True
	
	class Alternation(AstNode):
		def match(self):
			node = Parser.Concatenation()
			if not node.match(): return False
			self.save(node)
			while True:
				self.jump()
				node = Parser.TerminalAstNode(TokenType.Or)
				if not node.match():
					del node
					if type(self.children[-1]) == Parser.TerminalAstNode and self.children[-1].token_type == TokenType.Breaker: self.children.pop()
					return True
				self.save(node)
				node = Parser.Concatenation()
				if not node.match(): return False
				self.save(node)

	class Rule(AstNode):
		def match(self):
			node = Parser.TerminalAstNode(TokenType.Word)
			if not node.match(): return False
			self.save(node)
			node = Parser.TerminalAstNode(TokenType.Setter)
			if not node.match(): return False
			self.save(node)
			self.jump()
			node = Parser.Alternation()
			if not node.match(): return False
			self.save(node)
			return True

	class Grammar(AstNode):
		def match(self):
			self.jump()
			node = Parser.Rule()
			while node.match():
				self.save(node)
				node = Parser.TerminalAstNode(TokenType.EOF)
				if node.match(): return True
				del node
				node = Parser.TerminalAstNode(TokenType.Breaker)
				if not node.match(): return False
				self.save(node)
				self.jump()
				node = Parser.TerminalAstNode(TokenType.EOF)
				if node.match(): return True
				del node
				node = Parser.Rule()
			return False
	
	def evaluate(self) -> AstNode:
		node = self.Grammar()
		if not node.match(): raise SyntaxError("Illegal EBNF")
		return node

class Generator:
	def __init__(self, tree: Parser.AstNode) -> None:
		self.tree = tree
	
	def clean(self):
		pass	


def show_AST(node: Parser.AstNode, level = 0):
	print(level*"\t", end="")
	if type(node) == Parser.TerminalAstNode: print(node.token_type, repr(str(node.value)))
	else:
		print("> ", type(node))
		for i in node.children:
			show_AST(i, level + 1)

if __name__ == "__main__":
	with open("Varfuck.ebnf", "r") as f:
		p = Parser(f.read())
		p.evaluate()
		show_AST(p.evaluate())
	