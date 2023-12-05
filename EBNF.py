import VirtualParser as VP

class TokenType:
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
		VP.Count(VP.Terminal(VP.Token(TokenType.Parenthesis, "(")), VP.CountType.One),
		temp_count,
		VP.Count(VP.Terminal(VP.Token(TokenType.Parenthesis, ")")), VP.CountType.One)
	]
	term_alter_list = [
		VP.Count(VP.Concat(term_concat_list), VP.CountType.One),
		VP.Count(terminal_rule, VP.CountType.One),
		VP.Count(word_rule, VP.CountType.One)
	]
	term_rule = VP.RuleRef("term", VP.Count(VP.Alter(term_alter_list), VP.CountType.One))
	factor_alter_list = [
		VP.Count(VP.Terminal(TokenType.ZeroOrMore), VP.CountType.One),
		VP.Count(VP.Terminal(TokenType.OneOrMore), VP.CountType.One),
		VP.Count(VP.Terminal(TokenType.ZeroOrOne), VP.CountType.One)
	]
	factor_alter = VP.Alter(factor_alter_list)
	factor_rule = VP.RuleRef("factor", VP.Count(VP.Concat([VP.Count(term_rule, VP.CountType.One), VP.Count(factor_alter, VP.CountType.ZeroOrOne)]), VP.CountType.One))
	concatenation_rule = VP.RuleRef("concat", VP.Count(factor_rule, VP.CountType.OneOrMany))
	alter_concat_list_2 = [
		VP.Count(VP.Terminal(TokenType.Or), VP.CountType.One),
		VP.Count(concatenation_rule, VP.CountType.One)
	]
	alter_concat_list = [
		VP.Count(concatenation_rule, VP.CountType.One),
		VP.Count(VP.Concat(alter_concat_list_2), VP.CountType.ZeroOrMany)
	]
	alternation_rule = VP.RuleRef("alter", VP.Count(VP.Concat(alter_concat_list), VP.CountType.One))
	temp_count.node = alternation_rule
	rule_concat_list = [
		VP.Count(word_rule, VP.CountType.One),
		VP.Count(VP.Terminal(TokenType.Setter), VP.CountType.One),
		VP.Count(alternation_rule, VP.CountType.One),
		VP.Count(VP.Terminal(TokenType.Breaker), VP.CountType.One),
	]
	rule_rule = VP.RuleRef("rule", VP.Count(VP.Concat(rule_concat_list), VP.CountType.One))
	grammar_concat_list = [
		VP.Count(rule_rule, VP.CountType.ZeroOrMany),
		VP.Count(VP.Terminal(TokenType.EOF), VP.CountType.One)
	]
	grammar_rule = VP.RuleRef("grammar", VP.Count(VP.Concat(grammar_concat_list), VP.CountType.One))

	grammar = VP.Grammar(grammar_rule)
	del grammar_rule, grammar_concat_list, rule_rule, rule_concat_list, alternation_rule, alter_concat_list,\
		alter_concat_list_2, concatenation_rule, factor_rule, factor_alter, factor_alter_list, term_rule,\
		term_alter_list, term_concat_list, temp_count, terminal_rule, word_rule

	def __init__(self, data: str) -> None:
		self.lexer = Lexer(data)
		self.parser = VP.Parser(Parser.grammar, self.lexer, Parser.terminal_dict, Parser.rule_dict, Parser.terminal_set, Parser.rule_set)
	
	def parse(self) -> VP.ASTNode:
		return self.parser.parse()
	
	# From this point on it's just a tired mix of me trying to be dynamic and implementing the IF statically
	def __get_term(self, node: VP.ASTNode|VP.Token) -> VP.Concat|VP.RuleRef|VP.Alter|VP.Terminal:
		if type(node) == VP.Token:
			if node.type == TokenType.Word: return self.__get_rule(node.value)[0]
			return VP.Terminal(node)
		return self.__get_next(node).node # ??????

	def __get_factor(self, data: list[VP.ASTNode|VP.Token]) -> tuple[VP.Concat|VP.RuleRef|VP.Alter|VP.Terminal, VP.CountType]:
		term = self.__get_term(data[0].children[0])
		count = VP.CountType.One
		if len(data) == 2:
			n = data[1].type
			if n == TokenType.ZeroOrMore: count = VP.CountType.ZeroOrMany
			elif n == TokenType.ZeroOrOne: count = VP.CountType.ZeroOrOne
			elif n == TokenType.OneOrMore: count = VP.CountType.OneOrMany
			else: raise SyntaxError("Unexpected pluralization.")
		return term, count

	def __get_concat(self, data: list[VP.ASTNode]) -> tuple[VP.Concat, VP.CountType]:
		return VP.Concat([self.__get_next(node) for node in data]), VP.CountType.One

	def __get_alter(self, data: list[VP.ASTNode]) -> tuple[VP.Alter, VP.CountType]:
		return VP.Alter([self.__get_next(node) for node in data]), VP.CountType.One

	def __get_rule(self, rule_name: str) -> tuple[VP.RuleRef, VP.CountType]:
		if rule_name not in self.rules:
			self.rules[rule_name] = VP.RuleRef(rule_name, None)
			rule_tree = None
			try:
				rule_tree = self.rule_trees[rule_name]
			except KeyError:
				raise SyntaxError(f"Rule {rule_name} not found.")
			self.rules[rule_name].spec = self.__get_next(rule_tree.children[1])
		return self.rules[rule_name], VP.CountType.One
	
	def __get_next(self, node: VP.ASTNode) -> VP.Count:
		data = None
		name = node.rule_name
		if name == "rule": data = self.__get_rule(node.children[0].value)
		elif name == "term": raise SyntaxError("Term should be proceeded by factor.")
		elif name == "alter": data = self.__get_alter(node.children)
		elif name == "concat": data = self.__get_concat(node.children)
		elif name == "factor": data = self.__get_factor(node.children)
		else: raise SyntaxError("Unexpected node in tree.")
		return VP.Count(data[0], data[1])
	
	def build_if(self) -> VP.Grammar:
		tree = self.parse()
		if tree.rule_name != "grammar": raise SyntaxError("Not a grammar based AST.")
		self.rule_trees: dict[str, VP.ASTNode] = dict()
		self.rules: dict[str, VP.RuleRef] = dict()
		for rule in tree.children:
			rule_name = rule.children[0].value
			self.rules
			self.rule_trees[rule_name] = rule
		result = VP.Grammar(VP.Count(self.__get_rule("grammar"), VP.CountType.One))
		del self.rule_trees, self.rules

def show_IF(data: VP.Grammar) -> None:
	pass

if __name__ == "__main__":
	with open("Varfuck.ebnf", "r") as f:
		p = Parser(f.read())
		IF = p.build_if()