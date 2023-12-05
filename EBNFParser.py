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

def build_ebnf_parser() -> tuple[VP.Grammar,dict[VP.Enum|VP.Token, VP.Enum|VP.Token],dict[str, VP.Token|VP.Enum],set[VP.Enum|VP.Token],set[str]]:
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
		TokenType.Breaker
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
	return VP.Grammar(grammar_rule), terminal_dict, rule_dict, terminal_set, rule_set

def show_AST_2(node: VP.ASTNode|VP.Token, level = 0):
	print(level*"\t", end="")
	if type(node) == VP.Token: print(node.type, repr(str(node.value)))
	else:
		print("> ", node.rule_name)
		for i in node.children:
			show_AST_2(i, level + 1)

if __name__ == "__main__":
	with open("Varfuck.ebnf", "r") as f:
		g, d1, d2, s1, s2 = build_ebnf_parser()
		l = Lexer(f.read())
		p = VP.Parser(g, l, d1, d2, s1, s2)
		show_AST_2(p.parse())