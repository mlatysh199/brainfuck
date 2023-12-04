from ASTBase import *
from ASTBase import Token

class TokenType(BaseTokenType):
	Breaker = 0
	Word = 1
	Terminal = 2
	Or = 3
	OneOrMore = 4
	ZeroOrMore = 5
	ZeroOrOne = 6
	Parenthesis = 7
	Setter = 8

class Lexer(BaseLexer):
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
		super().__init__()
		self.stream = stream

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

class EBNFParser:

	def __init__(self, stream: str):
		EBNFParser.lexer = Lexer(stream)

	class ASTNode:
		def __init__(self) -> None:
			self.lexer_pos = EBNFParser.lexer.get_position()
			self.children: list["EBNFParser.ASTNode"] = []
		
		# Virtual method
		def match(self) -> bool:
			return False
		
		def save(self, node: "EBNFParser.ASTNode") -> None:
			self.children.append(node)

		def jump(self) -> None:
			while True:
				node = EBNFParser.TerminalAstNode(TokenType.Breaker)
				if not node.match(): break
				self.save(node)
		
		def __del__(self) -> None:
			self.children.clear()
			EBNFParser.lexer.set_position(self.lexer_pos)

	class TerminalAstNode(ASTNode):

		def __init__(self, token_type: TokenType) -> None:
			super().__init__()
			self.token_type = token_type
			self.value = None

		def match(self) -> bool:
			token = EBNFParser.lexer.next_token()
			if token.type == self.token_type:
				self.value = token.value
				return True
			return False
	
	class Term(ASTNode):
		def match(self):
			node = EBNFParser.TerminalAstNode(TokenType.Parenthesis)
			if node.match():
				if node.value != "(": return False
				self.save(node)
				node = EBNFParser.Alternation()
				if not node.match(): return False
				self.save(node)
				node = EBNFParser.TerminalAstNode(TokenType.Parenthesis)
				if not node.match() or node.value != ")": return False
				self.save(node)
				return True
			del node
			node = EBNFParser.TerminalAstNode(TokenType.Terminal)
			if node.match():
				self.save(node)
				return True
			del node
			node = EBNFParser.TerminalAstNode(TokenType.Word)
			if node.match():
				self.save(node)
				return True
			return False
	
	class Factor(ASTNode):
		node_types = [
			TokenType.OneOrMore,
			TokenType.ZeroOrMore,
			TokenType.ZeroOrOne
		]

		def match(self):
			node = EBNFParser.Term()
			if not node.match(): return False
			self.save(node)

			for i in self.node_types:
				node = EBNFParser.TerminalAstNode(i)
				if node.match():
					self.save(node)
					break
				del node
			return True
	
	class Concatenation(ASTNode):
		def match(self):
			node = EBNFParser.Factor()
			if not node.match(): return False
			self.save(node)
			node = EBNFParser.TerminalAstNode(TokenType.Breaker)
			while not node.match():
				del node
				node = EBNFParser.Factor()
				if not node.match(): return True
				self.save(node)
				node = EBNFParser.TerminalAstNode(TokenType.Breaker)
			return True
	
	class Alternation(ASTNode):
		def match(self):
			node = EBNFParser.Concatenation()
			if not node.match(): return False
			self.save(node)
			while True:
				self.jump()
				node = EBNFParser.TerminalAstNode(TokenType.Or)
				if not node.match():
					del node
					if type(self.children[-1]) == EBNFParser.TerminalAstNode and self.children[-1].token_type == TokenType.Breaker: self.children.pop()
					return True
				self.save(node)
				node = EBNFParser.Concatenation()
				if not node.match(): return False
				self.save(node)

	class Rule(ASTNode):
		def match(self):
			node = EBNFParser.TerminalAstNode(TokenType.Word)
			if not node.match(): return False
			self.save(node)
			node = EBNFParser.TerminalAstNode(TokenType.Setter)
			if not node.match(): return False
			self.save(node)
			self.jump()
			node = EBNFParser.Alternation()
			if not node.match(): return False
			self.save(node)
			return True

	class Grammar(ASTNode):
		def match(self):
			self.jump()
			node = EBNFParser.Rule()
			while node.match():
				self.save(node)
				node = EBNFParser.TerminalAstNode(TokenType.EOF)
				if node.match(): return True
				del node
				node = EBNFParser.TerminalAstNode(TokenType.Breaker)
				if not node.match(): return False
				self.save(node)
				self.jump()
				node = EBNFParser.TerminalAstNode(TokenType.EOF)
				if node.match(): return True
				del node
				node = EBNFParser.Rule()
			return False
	
	def evaluate(self) -> "EBNFParser.ASTNode":
		node = self.Grammar()
		if not node.match(): raise SyntaxError("Illegal EBNF")
		return node

class VirtualParserBuilder:

	class CountType(Enum):
		ZeroOrOne = 0
		ZeroOrMany = 1
		One = 2
		OneOrMany = 3

	class Count:
		def __init__(self, node: "VirtualParserBuilder.RuleRef"|"VirtualParserBuilder.Alter"|"VirtualParserBuilder.Concat"|"VirtualParserBuilder.Terminal", count_type: "VirtualParserBuilder.CountType") -> None:
			self.node = node
			self.count_type = count_type
	
	class Terminal:
		def __init__(self, data: str) -> None:
			self.data = data

	class Concat:
		def __init__(self, additions: list["VirtualParserBuilder.Count"]) -> None:
			self.additions = additions

	class Alter:
		def __init__(self, ors: list["VirtualParserBuilder.Count"]) -> None:
			self.ors = ors

	class RuleRef:
		def __init__(self, rule_name: str, spec: "VirtualParserBuilder.Count") -> None:
			self.rule_name = rule_name
			self.spec = spec
	
	class Grammar:
		def __init__(self, start_rule: "VirtualParserBuilder.RuleRef") -> None:
			self.start_rule = start_rule

class VirtualParser:
	lexer: BaseLexer
	terminal_token_table: dict[str, Token|BaseTokenType]
	rule_token_table: dict[str, Token|BaseTokenType]

	def __init__(self, tree: VirtualParserBuilder.Grammar, lexer: BaseLexer, terminal_token_table: dict[str, Token|BaseTokenType] = dict(), rule_token_table: dict[str, Token|BaseTokenType] = dict()) -> None:
		self.tree = tree
		self.lexer = lexer
		self.terminal_token_table = terminal_token_table
		self.rule_token_table = rule_token_table

	class ASTNode:
		def __init__(self, rule_name: str, children: list["VirtualParser.ASTNode"|Token]) -> None:
			self.rule_name = rule_name
			self.children = children
	
	class Matcher:
	
		def start(self) -> None:
			pass

		def next_match(self) -> list["VirtualParser.ASTNode"|Token]|None:
			raise NotImplementedError()
	
	class LiteralMatcher(Matcher):
		def __init__(self, data: Token|BaseTokenType) -> None:
			if data in VirtualParser.terminal_token_table: self.data = VirtualParser.terminal_token_table[data]
			else: self.data = data
			self.positions = []

		def start(self) -> None:
			self.positions.append(VirtualParser.lexer.get_position())	
		
		def next_match(self) -> list["VirtualParser.ASTNode"|Token]|None:
			VirtualParser.lexer.set_position(self.positions[-1])
			token = VirtualParser.lexer.next_token()
			if self.data == token: return [token]
			VirtualParser.lexer.set_position(self.positions[-1])
			self.positions.pop()	
			return None
	
	class ConcatMatcher(Matcher):
		def __init__(self, this: "VirtualParser.Matcher", next: "VirtualParser.ConcatMatcher"|None) -> None:
			self.this = this
			self.next = next
			self.level = 0
			self.built = []

		def start(self) -> None:
			self.level += 1
			self.this.start()

		def next_match(self) -> list["VirtualParser.ASTNode"|Token]|None:
			if self.level != len(self.built):
				result = self.this.next_match()
				if result == None:
					self.level -= 1
					return None
				self.built.append(result)
				if self.next == None: return self.built[-1]
				self.next.start()
			result = None
			while True:
				if self.next != None: result = self.next.next_match()
				if result == None:
					result = self.this.next_match()
					if result == None:
						self.level -= 1
						self.built.pop()
						return None
					self.built[-1] = result
					if self.next == None: return self.built[-1]
					self.next.start()
					result = None
				else: return self.built[-1] + result

	class AlterMatcher(Matcher):
		def __init__(self, this: "VirtualParser.Matcher", next: "VirtualParser.AlterMatcher"|None) -> None:
			self.this = this
			self.next = next
			self.level = 0
			self.selected = []

		def start(self) -> None:
			self.level += 1
			self.selected.append(True)
			self.this.start()
		
		def next_match(self) -> list["VirtualParser.ASTNode"|Token]|None:
			if self.selected[-1]:
				result = self.this.next_match()
				if result != None: return result
				if self.next == None:
					self.level -= 1
					self.selected.pop()
					return None
				self.selected[-1] = False
				self.next.start()
			result = self.next.next_match()
			if result == None: self.level -= 1
			return result
	
	class RuleMatcher(Matcher):
		def __init__(self, rule_name: str, matcher: "VirtualParser.CountMatcher") -> None:
			self.rule_name = rule_name
			self.matcher = matcher

		def next_match(self) -> list["VirtualParser.ASTNode"|Token]|None:
			self.matcher.start()
			result = self.matcher.next_match()
			if result == None: return None
			return VirtualParser.ASTNode(self.rule_name, result)

	class CountMatcher(Matcher):
		def __init__(self, matcher: "VirtualParser.Matcher", count_type: VirtualParserBuilder.CountType) -> None:
			self.matcher = matcher
			self.count_type = count_type
			self.data: list[list["VirtualParser.ASTNode"|Token]] = []
			self.level = 0
		
		def start(self) -> None:
			self.level += 1
		
		def next_match(self) -> list["VirtualParser.ASTNode"|Token]|None:
			if len(self.data) != self.level:
				self.matcher.start()
				result = self.matcher.next_match()
				build = []
				if result == None:
					if self.count_type == VirtualParserBuilder.CountType.One or self.count_type == VirtualParserBuilder.CountType.OneOrMany:
						self.level -= 1
						return None
					build = []
				else:
					if self.count_type == VirtualParserBuilder.CountType.One or self.count_type == VirtualParserBuilder.CountType.ZeroOrOne:
						if result != None: build.append(result)
					else:
						while result != None:
							build.append(result)
							self.matcher.start()
							result = self.matcher.next_match()
				self.data.append(build)
				result = []
				for i in build: result += i
				return result
			build = self.data[-1]
			if not len(build):
				self.level -= 1
				self.data.pop()
				return None
			build.pop()
			result = self.matcher.next_match()
			if self.count_type == VirtualParserBuilder.CountType.One or self.count_type == VirtualParserBuilder.CountType.ZeroOrOne:
				if result != None: build.append(result)
			else:
				while result != None:
					build.append(result)
					self.matcher.start()
					result = self.matcher.next_match()
			if len(build):
				result = []
				for i in build: result += i
				return result	
			if self.count_type == VirtualParserBuilder.CountType.One or self.count_type == VirtualParserBuilder.CountType.OneOrMany:
				self.level -= 1
				self.data.pop()
				return None
			return []

	
	class GrammarMatcher(Matcher):
		def __init__(self, matcher: "VirtualParser.RuleMatcher") -> None:
			self.matcher = matcher
		
		def next_match(self) -> list["VirtualParser.ASTNode"|Token]|None:
			self.matcher.start()
			return self.matcher.next_match()
	
	def __get_matcher_literal(self, data: Token|BaseTokenType) -> LiteralMatcher:
		return VirtualParser.LiteralMatcher(data)

	def __get_matcher_concat(self, concat: VirtualParserBuilder.Concat) -> ConcatMatcher:
		if concat not in self.matchers:
			matcher = None
			for i in reversed(concat.additions): matcher = VirtualParser.ConcatMatcher(self.__get_matcher_count(i), matcher)
			self.matchers[concat] = matcher
		return self.matchers[concat]
	
	def __get_matcher_alter(self, alter: VirtualParserBuilder.Alter) -> AlterMatcher:
		if alter not in self.matchers:
			matcher = None
			for i in reversed(alter.ors): matcher = VirtualParser.AlterMatcher(self.__get_matcher_count(i), matcher)
			self.matchers[alter] = matcher
		return self.matchers[alter]

	def __get_matcher_rule(self, rule: VirtualParserBuilder.RuleRef) -> RuleMatcher|LiteralMatcher:
		if rule not in self.matchers:
			matcher = None
			if rule.rule_name in self.rule_token_table: matcher = VirtualParser.LiteralMatcher(self.rule_token_table[rule.rule_name])
			else: matcher = VirtualParser.RuleMatcher(rule.rule_name, self.__get_matcher_count(rule.spec))
			self.matchers[rule] = matcher
		return self.matchers[rule]
		
	def __get_matcher_count(self, count: VirtualParserBuilder.Count) -> CountMatcher:
		if count not in self.matchers:
			matcher = None
			t = type(count.node)
			if t == VirtualParserBuilder.RuleRef: matcher = self.__get_matcher_rule(count.node)
			elif t == VirtualParserBuilder.Terminal: matcher = self.__get_matcher_literal(count.node.data)
			elif t == VirtualParserBuilder.Alter: matcher = self.__get_matcher_alter(count.node)
			elif t == VirtualParserBuilder.Concat: matcher = self.__get_matcher_concat(count.node)
			self.matchers[count] = VirtualParser.CountMatcher(matcher, count.count_type)
		return self.matchers[count]

	def create_matchers(self, grammar: VirtualParserBuilder.Grammar) -> GrammarMatcher:
		self.matchers = dict()
		return VirtualParser.GrammarMatcher(self.__get_matcher_rule(grammar.start_rule))
	
	def parse(self) -> "VirtualParser.ASTNode":
		matcher: VirtualParser.GrammarMatcher = self.create_matchers()
		result = matcher.next_match()
		if not result: raise SyntaxError("Invalid syntax.")
		return result[0]

def show_AST(node: EBNFParser.ASTNode, level = 0):
	print(level*"\t", end="")
	if type(node) == EBNFParser.TerminalAstNode: print(node.token_type, repr(str(node.value)))
	else:
		print("> ", type(node))
		for i in node.children:
			show_AST(i, level + 1)

if __name__ == "__main__":
	with open("Varfuck.ebnf", "r") as f:
		p = EBNFParser(f.read())
		p.evaluate()
		show_AST(p.evaluate())
	