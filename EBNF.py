import VirtualParser as VP
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

class Lexer(VP.BaseLexer):
	word_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_"
	ignore_chars = " \t\n"
	break_chars = ";"
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

	def process_terminal(self) -> VP.Token:
		terminal_start = self.stream[self.pos]
		self.pos += 1
		original_pos = self.pos
		while self.pos < len(self.stream) and self.stream[self.pos] != terminal_start: self.pos += 1
		if self.pos > len(self.stream): return VP.Token(TokenType.EOF, None)
		self.pos += 1
		return VP.Token(TokenType.Terminal, self.stream[original_pos:self.pos - 1])

	def process_word(self) -> VP.Token:
		original_pos = self.pos
		while self.pos < len(self.stream) and self.stream[self.pos] in self.word_chars: self.pos += 1
		return VP.Token(TokenType.Word, self.stream[original_pos:self.pos])
	
	def next_token(self) -> VP.Token:
		if self.pos >= len(self.stream): return VP.Token(TokenType.EOF, None)
		char = self.stream[self.pos]
		while True:
			if char in self.ignore_chars: self.pos += 1
			else: break
			if self.pos >= len(self.stream): return VP.Token(TokenType.EOF, None)
			char = self.stream[self.pos]
		if char in self.word_chars: return self.process_word()
		elif char in self.terminal_chars: return self.process_terminal()
		elif self.stream[self.pos:self.pos + 3] in self.setter_exp:
			self.pos += 3
			return VP.Token(TokenType.Setter, None)
		else: self.pos += 1
		if char in self.or_chars: return VP.Token(TokenType.Or, None)
		elif char in self.break_chars: return VP.Token(TokenType.Breaker, None)
		elif char in self.parenthesis_chars: return VP.Token(TokenType.Parenthesis, char)
		elif char in self.one_or_more_chars: return VP.Token(TokenType.OneOrMore, None)
		elif char in self.zero_or_more_chars: return VP.Token(TokenType.ZeroOrMore, None)
		elif char in self.zero_or_one_chars: return VP.Token(TokenType.ZeroOrOne, None)
		raise KeyError(f"{char} is not a valid character.")

class Parser:
	terminal_dict = dict()
	rule_dict = {
		"word" : TokenType.Word,
		"terminal" : TokenType.Terminal
	}
	terminal_set = {
		VP.Token(TokenType.Parenthesis, "("),
		VP.Token(TokenType.Parenthesis, ")"),
		TokenType.EOF,
		TokenType.Setter,
		TokenType.Breaker,
		TokenType.Or
	}
	rule_set = {}

	word_rule = VP.RuleRef("word", None)
	terminal_rule = VP.RuleRef("terminal", None)
	temp_count = VP.Count(None, VP.CountType.One)
	term_concat_list = [
		VP.Terminal(VP.Token(TokenType.Parenthesis, "(")),
		temp_count,
		VP.Terminal(VP.Token(TokenType.Parenthesis, ")"))
	]
	term_alter_list = [
		VP.Concat(term_concat_list),
		terminal_rule,
		word_rule
	]
	term_rule = VP.RuleRef("term", VP.Alter(term_alter_list))
	factor_alter_list = [
		VP.Terminal(TokenType.ZeroOrMore),
		VP.Terminal(TokenType.OneOrMore),
		VP.Terminal(TokenType.ZeroOrOne)
	]
	factor_alter = VP.Alter(factor_alter_list)
	factor_rule = VP.RuleRef("factor", VP.Concat([term_rule, VP.Count(factor_alter, VP.CountType.ZeroOrOne)]))
	concatenation_rule = VP.RuleRef("concat", VP.Count(factor_rule, VP.CountType.OneOrMany))
	alter_concat_list_2 = [
		VP.Terminal(TokenType.Or),
		concatenation_rule
	]
	alter_concat_list = [
		concatenation_rule,
		VP.Count(VP.Concat(alter_concat_list_2), VP.CountType.ZeroOrMany)
	]
	alternation_rule = VP.RuleRef("alter", VP.Concat(alter_concat_list))
	temp_count.node = alternation_rule
	rule_concat_list = [
		word_rule,
		VP.Terminal(TokenType.Setter),
		alternation_rule,
		VP.Terminal(TokenType.Breaker),
	]
	rule_rule = VP.RuleRef("rule", VP.Concat(rule_concat_list))
	grammar_rule = VP.RuleRef("grammar", VP.Count(rule_rule, VP.CountType.ZeroOrMany))

	grammar = VP.Grammar(grammar_rule)
	del grammar_rule, rule_rule, rule_concat_list, alternation_rule, alter_concat_list,\
		alter_concat_list_2, concatenation_rule, factor_rule, factor_alter, factor_alter_list, term_rule,\
		term_alter_list, term_concat_list, temp_count, terminal_rule, word_rule

	def __init__(self, data: str) -> None:
		self.lexer = Lexer(data)
		self.parser = VP.Parser(Parser.grammar, self.lexer, Parser.terminal_dict, Parser.rule_dict, Parser.terminal_set, Parser.rule_set)
	
	def parse(self) -> VP.ASTNode:
		result = self.parser.parse()
		if len(result) == 0 or type(result[0]) != VP.ASTNode or result[0].rule != "grammar": raise SyntaxError("Not a grammar based AST.")
		return result[0]
	
	# From this point on it's just a tired mix of me trying to be dynamic and implementing the IF statically
	def __get_term(self, node: VP.ASTNode|VP.Token) -> VP.IntermediateForm:
		if type(node) == VP.Token:
			if node.type == TokenType.Word: return self.__get_rule(node.value)
			if node.value == "": return VP.IntermediateForm()
			return VP.Terminal(node)
		return self.__get_next(node)

	def __get_factor(self, data: list[VP.ASTNode|VP.Token]) -> VP.Count:
		term = self.__get_term(data[0].children[0])
		count = VP.CountType.One
		if len(data) == 2:
			n = data[1].type
			if n == TokenType.ZeroOrMore: count = VP.CountType.ZeroOrMany
			elif n == TokenType.ZeroOrOne: count = VP.CountType.ZeroOrOne
			elif n == TokenType.OneOrMore: count = VP.CountType.OneOrMany
			else: raise SyntaxError("Unexpected pluralization.")
		return VP.Count(term, count)

	def __get_concat(self, data: list[VP.ASTNode]) -> VP.Concat:
		return VP.Concat([self.__get_next(node) for node in data])

	def __get_alter(self, data: list[VP.ASTNode]) -> VP.Alter:
		return VP.Alter([self.__get_next(node) for node in data])

	def __get_rule(self, rule_name: str) -> VP.RuleRef:
		if rule_name not in self.rules:
			self.rules[rule_name] = VP.RuleRef(rule_name, None)
			rule_tree = None
			try:
				rule_tree = self.rule_trees[rule_name]
			except KeyError:
				raise SyntaxError(f"Rule {rule_name} not found.")
			self.rules[rule_name].spec = self.__get_next(rule_tree.children[1])
		return self.rules[rule_name]
	
	def __get_next(self, node: VP.ASTNode) -> VP.IntermediateForm:
		data = None
		name = node.rule
		if name == "rule": data = self.__get_rule(node.children[0].value)
		elif name == "term": raise SyntaxError("Term should be proceeded by factor.")
		elif name == "alter": data = self.__get_alter(node.children)
		elif name == "concat": data = self.__get_concat(node.children)
		elif name == "factor": data = self.__get_factor(node.children)
		else: raise SyntaxError("Unexpected node in tree.")
		return data
	
	def build_if(self) -> VP.Grammar:
		tree = self.parse() 
		VP.show_AST(tree) # TODO
		self.rule_trees: dict[str, VP.ASTNode] = dict()
		self.rules: dict[str, VP.RuleRef] = dict()
		for rule in tree.children:
			rule_name = rule.children[0].value
			self.rules
			self.rule_trees[rule_name] = rule
		result = VP.Grammar(VP.Count(self.__get_rule("grammar"), VP.CountType.One))
		del self.rule_trees, self.rules
		VP.show_IF(result) # TODO
		return result
