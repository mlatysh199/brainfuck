from enum import Enum
from typing import Union

class Token:
	def __init__(self, type: Enum, value: str) -> None:
		self.type = type
		self.value = value
	
	def __eq__(self, __value: object) -> bool:
		if type(__value) == Token: return __value.type == self.type and __value.value == self.value
		return __value == self.type
	
	def __ne__(self, __value: object) -> bool:
		return not self.__eq__(__value)
	
	def __str__(self) -> str:
		return repr(self.type) + " " + repr(self.value)
	
	def __hash__(self) -> int:
		return hash(self.__str__())

class BaseLexer:
	def __init__(self) -> None:
		self.pos = 0

	def next_token(self) -> Token:
		raise NotImplementedError()

	def get_position(self) -> int:
		return self.pos
	
	def set_position(self, pos: int) -> None:
		self.pos = pos

class CountType(Enum):
	ZeroOrOne = 0
	ZeroOrMany = 1
	One = 2
	OneOrMany = 3

class Count:
	def __init__(self, node: Union["RuleRef", "Alter", "Concat", "Terminal"], count_type: CountType) -> None:
		self.node = node
		self.count_type = count_type

class Terminal:
	def __init__(self, data: Token|Enum) -> None:
		self.data = data

class Concat:
	def __init__(self, additions: list[Count]) -> None:
		self.additions = additions

class Alter:
	def __init__(self, ors: list[Count]) -> None:
		self.ors = ors

class RuleRef:
	def __init__(self, rule_name: str, spec: Count) -> None:
		self.rule_name = rule_name
		self.spec = spec

class Grammar:
	def __init__(self, start_rule: RuleRef) -> None:
		self.start_rule = start_rule

class ASTNode:
	def __init__(self, rule_name: str, children: list[Union["ASTNode", Token]]) -> None:
		self.rule_name = rule_name
		self.children = children

# TODO
# Temp
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
print_level = [0]

class Matcher:
	def start(self) -> None:
		pass

	def next_match(self) -> list[ASTNode|Token]|None:
		raise NotImplementedError()
	
	def print_try(self, data: str) -> None:
		print("   "*print_level[0], f"{bcolors.OKCYAN}>?", data)
		print_level[0] += 1
	
	def print_match(self, data: str) -> None:
		print("   "*print_level[0], f"{bcolors.OKGREEN}<#", data)
		print_level[0] -= 1	

	def print_fail(self, data: str) -> None:
		print("   "*print_level[0], f"{bcolors.FAIL}<!", data)
		print_level[0] -= 1		
	
	def print_normal(self, data: str) -> None:
		print("   "*print_level[0], f"{bcolors.ENDC}: ", data)

class LiteralMatcher(Matcher):
	def __init__(self, lexer: BaseLexer, data: Token|Enum, forget: bool = False) -> None:
		self.data = data
		self.positions = []
		self.forget = forget
		self.lexer = lexer

	def start(self) -> None:
		self.positions.append(self.lexer.get_position())	
	
	def next_match(self) -> list[ASTNode|Token]|None:
		self.print_try(f"Literal: data = {self.data}; position = {self.positions[-1]}")
		self.lexer.set_position(self.positions[-1])
		token = self.lexer.next_token()
		self.print_normal(f"token = {token}")
		if self.data == token:
			self.print_match("Literal")
			return [token] if not self.forget else []
		self.lexer.set_position(self.positions[-1])
		self.print_fail("Literal")
		self.positions.pop()
		return None

class ConcatMatcher(Matcher):
	def __init__(self, this: Matcher, next: Union["ConcatMatcher", None]) -> None:
		self.this = this
		self.next = next
		self.level = 0
		self.built = []

	def start(self) -> None:
		self.level += 1
		self.this.start()

	def next_match(self) -> list[ASTNode|Token]|None:
		self.print_try("Concat")
		if self.level != len(self.built):
			result = self.this.next_match()
			if result == None:
				self.level -= 1
				self.print_fail("Concat")
				return None
			self.built.append(result)
			if self.next == None:
				self.print_match("Concat")
				return self.built[-1]
			self.next.start()
		result = None
		while True:
			if self.next != None: result = self.next.next_match()
			if result == None:
				result = self.this.next_match()
				if result == None:
					self.level -= 1
					self.built.pop()
					self.print_fail("Concat")	
					return None
				self.built[-1] = result
				if self.next == None:
					self.print_match("Concat")
					return self.built[-1]
				self.next.start()
				result = None
			else:
				self.print_match("Concat")
				return self.built[-1] + result

class AlterMatcher(Matcher):
	def __init__(self, this: Matcher, next: Union["AlterMatcher", None]) -> None:
		self.this = this
		self.next = next
		self.level = 0
		self.selected = []

	def start(self) -> None:
		self.level += 1
		self.selected.append(True)
		self.this.start()
	
	def next_match(self) -> list[ASTNode|Token]|None:
		self.print_try("Alter")
		if self.selected[-1]:
			result = self.this.next_match()
			if result != None:
				self.print_match("Alter")
				return result
			if self.next == None:
				self.level -= 1
				self.selected.pop()
				self.print_fail("Alter")
				return None
			self.selected[-1] = False
			self.next.start()
		result = self.next.next_match()
		if result == None:
			self.print_fail("Alter")
			self.level -= 1
		else:
			self.print_match("Alter")
		return result

class RuleMatcher(Matcher):
	def __init__(self, rule_name: str, matcher: "CountMatcher", forget: bool = False) -> None:
		self.rule_name = rule_name
		self.matcher = matcher
		self.forget = forget

	def next_match(self) -> list[ASTNode|Token]|None:
		self.print_try(f"Rule: rule_name = {self.rule_name}")
		self.matcher.start()
		result = self.matcher.next_match()
		if result == None:
			self.print_fail("Rule")
			return None
		self.print_match("Rule")
		return [ASTNode(self.rule_name, result)] if not self.forget else []

class CountMatcher(Matcher):
	def __init__(self, matcher: Matcher, count_type: CountType) -> None:
		self.matcher = matcher
		self.count_type = count_type
		self.data: list[list[ASTNode|Token]] = []
		self.level = 0
	
	def start(self) -> None:
		self.level += 1
	
	def next_match(self) -> list[ASTNode|Token]|None:
		self.print_try(f"Count: type = {self.count_type}")
		if len(self.data) != self.level:
			self.print_normal("Starting count...")
			self.matcher.start()
			result = self.matcher.next_match()
			build = []
			if result == None:
				if self.count_type == CountType.One or self.count_type == CountType.OneOrMany:
					self.level -= 1
					self.print_fail("Count")
					return None
				build = []
			else:
				if self.count_type == CountType.One or self.count_type == CountType.ZeroOrOne:
					if result != None: build.append(result)
				else:
					while result != None:
						build.append(result)
						self.matcher.start()
						result = self.matcher.next_match()
			self.data.append(build)
			result = []
			for i in build: result += i
			self.print_match(f"Count: matched = {len(build)}")
			return result
		build = self.data[-1]
		if not len(build):
			self.level -= 1
			self.data.pop()
			self.print_fail("Count")
			return None
		build.pop()
		result = self.matcher.next_match()
		if self.count_type == CountType.One or self.count_type == CountType.ZeroOrOne:
			if result != None: build.append(result)
		else:
			while result != None:
				build.append(result)
				self.matcher.start()
				result = self.matcher.next_match()
		if len(build):
			result = []
			for i in build: result += i
			self.print_match(f"Count: matched = {len(build)}")
			return result
		if self.count_type == CountType.One or self.count_type == CountType.OneOrMany:
			self.level -= 1
			self.data.pop()
			self.print_fail("Count")
			return None
		self.print_match(f"Count: matched = 0")
		return []

class GrammarMatcher(Matcher):
	def __init__(self, matcher: RuleMatcher) -> None:
		self.matcher = matcher
	
	def next_match(self) -> list[ASTNode|Token]|None:
		self.print_try("Grammar")
		self.matcher.start()
		return self.matcher.next_match()

class Parser:

	def __init__(self, tree: Grammar, lexer: BaseLexer, terminal_token_table: dict[Token|Enum, Token|Enum], rule_token_table: dict[str, Token|Enum] = dict(), terminal_forget_set: set[Token|Enum] = set(), rule_forget_set: set[str] = set()) -> None:
		self.tree = tree
		self.lexer = lexer
		self.terminal_token_table = terminal_token_table
		self.rule_token_table = rule_token_table
		self.rule_forget_set = rule_forget_set
		self.terminal_forget_set = terminal_forget_set

	def __get_matcher_literal(self, data: Token|Enum) -> LiteralMatcher:
		if data in self.terminal_token_table: data = self.terminal_token_table[data]
		return LiteralMatcher(self.lexer, data, data in self.terminal_forget_set)

	def __get_matcher_concat(self, concat: Concat) -> ConcatMatcher:
		if concat not in self.matchers:
			matcher = None
			for i in reversed(concat.additions): matcher = ConcatMatcher(self.__get_matcher_count(i), matcher)
			self.matchers[concat] = matcher
		return self.matchers[concat]
	
	def __get_matcher_alter(self, alter: Alter) -> AlterMatcher:
		if alter not in self.matchers:
			matcher = None
			for i in reversed(alter.ors): matcher = AlterMatcher(self.__get_matcher_count(i), matcher)
			self.matchers[alter] = matcher
		return self.matchers[alter]

	def __get_matcher_rule(self, rule: RuleRef) -> RuleMatcher|LiteralMatcher:
		if rule not in self.matchers:
			matcher = None
			if rule.rule_name in self.rule_token_table: matcher = self.__get_matcher_literal(self.rule_token_table[rule.rule_name])
			else:
				matcher = RuleMatcher(rule.rule_name, None)
				self.matchers[rule] = matcher
				matcher.matcher = self.__get_matcher_count(rule.spec)
			self.matchers[rule] = matcher
		return self.matchers[rule]
		
	def __get_matcher_count(self, count: Count) -> CountMatcher:
		if count not in self.matchers:
			matcher = None
			t = type(count.node)
			if t == RuleRef: matcher = self.__get_matcher_rule(count.node)
			elif t == Terminal: matcher = self.__get_matcher_literal(count.node.data)
			elif t == Alter: matcher = self.__get_matcher_alter(count.node)
			elif t == Concat: matcher = self.__get_matcher_concat(count.node)
			self.matchers[count] = CountMatcher(matcher, count.count_type)
		return self.matchers[count]

	def create_matchers(self, grammar: Grammar) -> GrammarMatcher:
		self.matchers = dict()
		return GrammarMatcher(self.__get_matcher_rule(grammar.start_rule))
	
	def parse(self) -> ASTNode:
		matcher: GrammarMatcher = self.create_matchers(self.tree)
		result = matcher.next_match()
		if result == None: raise SyntaxError("Invalid syntax.")
		return result[0]

	def reset(self) -> None:
		self.lexer.set_position(0)



		