from enum import Enum
import EBNF
import VirtualParser as VP
from numbers import Number
from typing import Union, Any

# Token types
class TokenType(Enum):
	EOF = -1
	Breaker = 0
	Command = 1
	Word = 2
	Number = 3
	Bracket = 4
	Brace = 5
	Separator = 6
	Operator = 7
	Parenthesis = 8
	Type = 9

# Reads tokens from string
class Lexer(VP.BaseLexer):
	word_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_"
	bracket_chars = "[]"
	brace_chars = "{}"
	parenthesis_chars = "()"
	break_chars = "\n;"
	number_chars = "0123456789"
	decimal_chars = "."
	operator_chars = "-+|&~=*/><^"
	separator_chars = ","
	ignore_chars = " \t"
	comment_chars = "#"
	comment_break_chars = "\n"
	commands = ["fuck", "="]
	operators = ["not", "~", "**", "*", "/", "+", "-", "<<", ">>", "&", "|", "^", "==", "and", "or", "<", ">", "<=", ">="]
	types = ["num"]

	def __init__(self, stream) -> None:
		self.stream = stream
		self.pos = 0

	# Consumes comments
	def process_comment(self) -> None:
		while self.pos < len(self.stream) and self.stream[self.pos] not in self.comment_break_chars: self.pos += 1
		self.pos += 1

	# Processes words
	def process_word(self) -> VP.Token:
		word = ""
		while self.pos < len(self.stream) and (self.stream[self.pos] in self.word_chars or self.stream[self.pos] in self.number_chars):
			word += self.stream[self.pos]
			self.pos += 1
		if word in self.commands: return VP.Token(TokenType.Command, word)
		elif word in self.operators: return VP.Token(TokenType.Operator, word)
		elif word in self.types: return VP.Token(TokenType.Type, word)
		return VP.Token(TokenType.Word, word)

	# Processes numbers
	def process_number(self) -> VP.Token:
		number = 0
		while self.pos < len(self.stream) and self.stream[self.pos] in self.number_chars:
			number *= 10
			number += ord(self.stream[self.pos]) - ord('0')
			self.pos += 1
		if self.pos < len(self.stream) and self.stream[self.pos] in self.decimal_chars:
			decimal = 1.0
			self.pos += 1
			while self.pos < len(self.stream) and self.stream[self.pos] in self.number_chars:
				decimal /= 10
				number += decimal*(ord(self.stream[self.pos]) - ord('0'))
				self.pos += 1
		return VP.Token(TokenType.Number, str(number))

	# Processes operators
	def process_operators(self) -> VP.Token:
		operator = self.stream[self.pos]
		self.pos += 1
		while self.pos < len(self.stream) and self.stream[self.pos] in self.operator_chars and operator + self.stream[self.pos] in self.operators:
			operator += self.stream[self.pos]
			self.pos += 1
		if operator not in self.operators:
			if operator in self.commands: return VP.Token(TokenType.Command, operator)
		return VP.Token(TokenType.Operator, operator)

	# Gets the next token
	def next_token(self) -> VP.Token:
		if self.pos >= len(self.stream): return VP.Token(TokenType.EOF, None)
		char = self.stream[self.pos]
		while True:
			if char in self.ignore_chars: self.pos += 1
			elif char in self.comment_chars: self.process_comment()
			else: break
			if self.pos >= len(self.stream): return VP.Token(TokenType.EOF, None)
			char = self.stream[self.pos]
		if char in self.word_chars: return self.process_word()
		elif char in self.number_chars: return self.process_number()
		elif char in self.operator_chars: return self.process_operators()
		else: self.pos += 1
		if char in self.bracket_chars: return VP.Token(TokenType.Bracket, char)
		elif char in self.brace_chars: return VP.Token(TokenType.Brace, char)
		elif char in self.break_chars: return VP.Token(TokenType.Breaker, None)
		elif char in self.separator_chars: return VP.Token(TokenType.Separator, None)
		elif char in self.parenthesis_chars: return VP.Token(TokenType.Parenthesis, char)
		raise KeyError(f"{char} is not a valid character.")
	
	def get_position(self) -> int:
		return self.pos
	
	def set_position(self, pos: int) -> None:
		self.pos = pos

"""
# Manages variables
class BinX:
	def __init__(self, x, offset, protected=False) -> None:
		self.x = x
		self.offset = offset
		self.protected = protected
	
	# Clears the variable
	def clear(self, forced=False) -> str:
		if self.protected and not forced: raise AttributeError("Protected variables cannot be altered.")
		return f"{self.offset}>clearbinx({self.x}){self.offset}<"

	# Moves the contents of one variable into this one (thus clearing the other one).
	def setas(self, var) -> str:
		if self.protected: raise AttributeError("Protected variables cannot be altered.")
		if self.offset == var.offset: raise AttributeError(f"Variables can't share offsets.")
		if self.x != var.x: raise AttributeError(f"Setter and settee must have same size ({self.x} != {var.x}).")
		if self.offset < var.offset: return self.clear() + f"{var.offset}>downbinx({self.x};{var.offset - self.offset - 1}){var.offset}<"
		return self.clear() + f"{var.offset}>upbinx({self.x};{self.offset - var.offset - 1}){var.offset}<"

	# Copies variable to top of stack
	def copytotop(self, var, top_offset) -> str:
		if self.protected: raise AttributeError("Protected variables cannot be altered.")
		if self.offset >= var.offset or top_offset - var.x != var.offset: raise AttributeError(f"Variables can only be copied to the top of the stack.")
		if self.x != var.x: raise AttributeError(f"Destination must have the same size as the original variable ({var.x} != {self.x}).")
		return f"{var.offset}>upbinx({self.x};{self.offset - var.offset - 1}){var.offset}<"

# Basically a C struct
class Group:
	def __init__(self, name, components) -> None:
		self.name = name
		if not len(components): raise IndexError(f"Groups requieres at least one component.")
		self.components = components
		self.x = 0
		for component in self.components:
			if component < 1: raise AttributeError(f"All components in a group have to possess a size of at least 1.")
			self.x += component

# Manages a group of variables
class BinXManager(dict):
	def __init__(self, relative_offset) -> None:
		self.relative_offset = relative_offset
		self.offset = 0
		self.components = []
		self.is_finalized = False

	# Splits (inplace) a group into separate variables
	def split(self, name, group) -> None:
		if self.is_finalized: raise ReferenceError("This BinXManager has already been finalized.")
		var = self[name]
		if var.x != group.x: raise AttributeError(f"Cannot split BinX of size {var.x} into group of size {group.x}.")
		del self[name]
		pos = 0
		while self.components[pos].x != var.x: pos += 1
		self.components.pop(pos)
		i_var = var
		for i in range(len(group.components)):
			i_var.x = group.componentes[i]
			self.components.insert(pos, i_var)
			self[name + '.' + group.name + '.' + str(i)] = i_var
			pos += 1
			i_var = BinX(0, i_var.offset + i_var.x)

	# Merges (inplace) a group of variables into one variable
	def inplace_merge(self, name, group, new_name=None) -> None:
		if not new_name: new_name = name + '.' + group.name
		if self.is_finalized: raise ReferenceError("This BinXManager has already been finalized.")
		var = self[name]
		pos = 0
		while self.components[pos][1].x != var.x: pos += 1
		subpos = pos
		for i in range(len(group.components)):
			if group.components[i].x != self.components[subpos][1].x: raise AttributeError(f"Cannot merge BinX of size {self.components[subpos].x} into group of size {group.x}.")
			subpos += 1
		pos += 1
		del self[name]
		var.x = group.x
		self[new_name] = var
		for i in range(1, len(group.components)):
			pop_var_name = self.components.pop(pos)[1]
			del self[pop_var_name]
	
	# Merges (not inplace) a group of variables into one variable
	def merge(self, names, group, new_name=None) -> str:
		if not new_name: new_name = names[0] + '.' + group.name
		if self.is_finalized: raise ReferenceError("This BinXManager has already been finalized.")
		data = ""
		for i in range(len(names)):
			var = self[names[i]]
			self[new_name + '.' + str(i)] = var.x
			data += var.copytotop(self[new_name + '.' + str(i)], self.offset)
		self.inplace_merge(new_name + ".0", group, new_name)
		return data

	# Eliminates value on the top of the stack
	def pop(self, forced=False) -> str:
		if self.is_finalized: raise ReferenceError("This BinXManager has already been finalized.")
		var_name, var = self.components.pop()
		if var.protected and not forced: raise AttributeError("Protected variables cannot be popped.")
		del self[var_name]
		self.offset -= var.x
		return var.clear()

	# Swaps two variables
	def swap(self, name_1, name_2) -> str:
		if self.is_finalized: raise ReferenceError("This BinXManager has already been finalized.")
		if var_1.x != var_2.x: raise AttributeError(f"{name_1} ({name_1.x}) and {name_2} ({name_2.x}) have different sizes.")
		var_1 = self[name_1]
		var_2 = self[name_2]
		var_3 = BinX(var_1.x, self.offset)
		return var_3.setas(var_2) + var_2.setas(var_1) + var_1.setas(var_3) + self.pop()

	# Return with variable
	def finalize(self, name) -> tuple[str, BinX]:
		if self.is_finalized: raise ReferenceError("This BinXManager has already been finalized.")
		var = self[name]
		data = ""
		for component in self.components:
			if component[1] != var: data += component[1].clear(True)
		new_var = BinX(var.x, 0)
		if var.protected: raise AttributeError("Protected variables cannot be finalize.")
		if var.offset: data += new_var.setas(var)
		self.offset = var.x
		self.is_finalized = True
		new_var.offset = self.relative_offset
		return data, new_var
	
	# Void return
	def finalize(self) -> str:
		if self.is_finalized: raise ReferenceError("This BinXManager has already been finalized.")
		data = ""
		for component in self.components: data += component[1].clear(True)
		self.is_finalized = True
		self.offset = 0
		return data

	def __setitem__(self, __key, __value) -> None:
		if self.is_finalized: raise ReferenceError("This BinXManager has already been finalized.")
		var = BinX(__value, self.offset)
		super().__setitem__(__key, var)
		self.offset += __value
		self.components.append([__key, var])
	
	def __getitem__(self, __key) -> BinX:
		if self.is_finalized: raise ReferenceError("This BinXManager has already been finalized.")
		return super().__getitem__(__key)

# TODO pointless?
class SmallMacro:
	def __init__(self, components, result):
		self.components = components
		self.result = result

# TODO merge into Precompiler and promote correct lexographical analyzer 
class BigMacro:
	reserved_words = ["setas", "clear", "invite", "void", "while", "ifel", "finalize", "swap", "pop", "merge", "imerge", "split"]

	def __init__(self, groups, name, params, output, code, offset):
		self.groups = groups
		self.name = name
		self.params = params
		self.output = output
		self.code = code
		self.data = "MAC_(" + self.name + ";"
		self.variables = BinXManager(offset)
		self.finalized = False
		self.process()
		self.data += ')'
	
	def process(self):
		i = 0
		while i < len(self.code) and not self.finalized:
			commands = self.code[i].split()
			if commands[0] == "clear":
				data += self.variables[commands[1]].clear()
			elif commands[0] == "invite":
				pass
			elif commands[0] == "void":
				data += BinX()
			elif commands[0] == "while":
				pass
			elif commands[0] == "ifel":
				pass
			elif commands[0] == "finalize":
				self.finalized = True
				if len(commands) - 1: data += self.variables.finalize(commands[1])
				else: data += self.variables.finalize()
			elif commands[0] == "pop":
				data += self.variables.pop()
			else:
				raise NameError(f"Couldn't find an instruction on line {i}: {self.code[i]}")
			i += 1
	
	def execute_mac(self, code):
		pass
"""
		
class Parser:
	terminal_dict = {
		VP.Token(EBNF.TokenType.Terminal, "fuck") : VP.Token(TokenType.Command, "fuck"),
		VP.Token(EBNF.TokenType.Terminal, "=") : VP.Token(TokenType.Command, "="),
		VP.Token(EBNF.TokenType.Terminal, "(") : VP.Token(TokenType.Parenthesis, "("),
		VP.Token(EBNF.TokenType.Terminal, ")") : VP.Token(TokenType.Parenthesis, ")"),	
		VP.Token(EBNF.TokenType.Terminal, "[") : VP.Token(TokenType.Bracket, "["),
		VP.Token(EBNF.TokenType.Terminal, "]") : VP.Token(TokenType.Bracket, "]"),
		VP.Token(EBNF.TokenType.Terminal, "{") : VP.Token(TokenType.Brace, "{"),
		VP.Token(EBNF.TokenType.Terminal, "}") : VP.Token(TokenType.Brace, "}"),
		VP.Token(EBNF.TokenType.Terminal, "num") : VP.Token(TokenType.Type, "num")
		
	}
	rule_dict = {
		"string" : TokenType.Word,
		"const" : TokenType.Number,
		"separator" : TokenType.Separator,
		"breaker" : TokenType.Breaker,
		"const_op" : TokenType.Operator,
		"u_const_op" : TokenType.Operator
	}
	terminal_set = {
		VP.Token(TokenType.Command, "fuck"),
		VP.Token(TokenType.Command, "="),
		TokenType.Bracket,
		TokenType.Brace,
		TokenType.Parenthesis,
		TokenType.Breaker,
		TokenType.Parenthesis
	}
	rule_set = {
	}

	grammar = None
	with open("Varfuck.ebnf", "r") as f:
		p = EBNF.Parser(f.read())
		grammar = p.build_if()
	
	def __init__(self, data: str) -> None:
		self.lexer = Lexer(data)
		self.parser = VP.Parser(Parser.grammar, self.lexer, Parser.terminal_dict, Parser.rule_dict, Parser.terminal_set, Parser.rule_set)
	
	def parse(self) -> VP.ASTNode:
		result = self.parser.parse()
		if len(result) == 0 or type(result[0]) != VP.ASTNode or result[0].rule != "grammar": raise SyntaxError("Not a grammar based AST.") # TODO replace with correct error
		return result[0]

class ASTNode:
	def __init__(self, name: str, data: list[Union["ASTNode",VP.Token]]) -> None:
		self.name = name
		self.data = data

class Cleaner:
	def __init__(self, tree: VP.ASTNode) -> None:
		if tree.rule != "grammar": raise SyntaxError("Not a grammar based AST.") # TODO replace with correct error
		self.tree = tree
	
	def __correct_const_expr(self, node: VP.ASTNode|VP.Token) -> ASTNode|VP.Token:
		if type(node) == VP.Token: return node
		if node.rule == "const_expr_p":
			if len(node.children) == 0: return ASTNode("temp", [])
			return ASTNode("temp", [self.__correct_const_expr(i) for i in node.children])
		back = self.__correct_const_expr(node.children[-1]).data
		if len(back) == 0: return ASTNode("const_expr", [self.__correct_const_expr(i) for i in node.children[:-1]])
		# Not as dynamic as I would like it to be, but we got to start hardcoding in some parts at some point
		return ASTNode("const_expr", [ASTNode("const_expr", [self.__correct_const_expr(i) for i in node.children[:-1]]), back[0], back[1]])
			
	def __clean(self, node: VP.ASTNode|VP.Token) -> ASTNode|VP.Token:
		if type(node) == VP.Token: return node
		if node.rule == "const_expr": return self.__correct_const_expr(node)
		return ASTNode(node.rule, [self.__clean(i) for i in node.children])

	def clean(self) -> ASTNode:
		return self.__clean(self.tree)

class ConstRef:
	def __init__(self, name: str) -> None:
		self.name = name
	
	def __str__(self) -> str:
		return self.name

class ConstExpr:
	# math expressions
	def __init__(self, data: list[str|ConstRef], force_nnint = False) -> None:
		self.refs = {ref.name for ref in data if type(ref) == ConstRef}
		import math
		self.data: list[str|ConstRef] = [str(eval(" ".join(data)))] if not len(self.refs) else data
		self.force_nnint = force_nnint
		self.done = not len(self.refs)
	
	def __builder(base: ASTNode) -> list[str|ConstRef]:
		data = base.data
		# Once again, boring hardcoding
		if type(data[0]) == VP.Token:
			if data[0].type == TokenType.Number: return [data[0].value]
			if data[0].type == TokenType.Operator: return [data[0].value] + ConstExpr.__builder(data[1])
			if len(data) == 1: return [ConstRef(data[0].value)]
			return ["math.", data[0].value, "("] + ConstExpr.__builder(data[1]) + [")"]
		if len(data) == 1: return ["("] + ConstExpr.__builder(data[0]) + [")"]
		return ConstExpr.__builder(data[0]) + [data[1].value] + ConstExpr.__builder(data[2])

	def builder(base: ASTNode) -> "ConstExpr":
		return ConstExpr(ConstExpr.__builder(base))

	def replace(self, name: str, expr: "ConstExpr") -> "ConstExpr":
		if name not in self.refs: return ConstExpr(self.data.copy(), self.force_nnint)
		cp = []
		for i in self.data:
			if type(i) == str or i.name != name: cp.append(i)
			else: cp.extend(expr.data)
		return ConstExpr(cp, self.force_nnint)

	def __add__(self, other) -> "ConstExpr":
		if type(other) != ConstExpr: raise TypeError(f"Cannot add ConstExpr with {type(other)}.")
		return ConstExpr(other.data + ["+"] + self.data, self.force_nnint or other.force_nnint)
	
	def __sub__(self, other) -> "ConstExpr":
		if type(other) != ConstExpr: raise TypeError(f"Cannot sub ConstExpr with {type(other)}.")
		return ConstExpr(self.data + ["-"] + other.data, self.force_nnint or other.force_nnint)
	
	def __str__(self) -> str:
		if len(self.refs): raise ValueError("ConstExpr hasn't been fully built.")
		if self.force_nnint:
			e = eval(self.data[0])
			if int(e) != e or e < 0: raise ValueError(f"ConstExpr's forced NNINT, instead got {e}.")
		return self.data[0]

class BinX:
	def __init__(self, name: str|None, size: ConstExpr) -> None:
		self.name = name if name != "" else None
		self.size = ConstExpr(size.data, True)

class BinXManager:
	def __init__(self, data: list[BinX], ret: list[ConstExpr]) -> None:
		self.size = ConstExpr(["0"], True)
		self.pos = ConstExpr(["0"], True)
		self.size_table: dict[str, BinX] = dict()
		self.pos_table: dict[str, ConstExpr] = dict()
		for i in data:
			if i.name == None: raise NameError("Variable names must be complete.")
			if i.name in self.size_table: raise NameError("Variable names must be non repeating.")
			self.size_table[i.name] = i
			self.pos_table[i.name] = self.size
			self.size = self.size + i.size
		self.params = data
		self.ret = ret
		# Helps make sure that whatever we try to return does not overwrite any if spaces
		for i in ret: self.size = self.size + i
		self.stack: list[ConstExpr] = []
		self.code: list[str|ConstExpr|MacroInvocation] = []
		self.comparisons: list[tuple[ConstExpr, ConstExpr]] = []
	
	def start_while(self, name: str) -> None:
		self.add("while(")
		self.copy(name)
		self.goup(self.size)
		self.add("boolbinx(")
		self.add(self.size_table[name])
		self.add(")")
		self.add(";")
		self.godown()
		self.stack.append(self.size)
		self.size = self.size + ConstExpr("2") + self.size_table[name]

	def end_while(self) -> None:
		self.add(")")
		self.pos = self.stack.pop()
		self.godown()
	
	def start_if(self, name: str) -> None:
		self.copy(name)
		self.goup(self.size)
		self.add("boolbinx(")
		self.add(self.size_table[name])
		self.add(")ifel(")
		self.stack.append(self.size)
		self.size = self.size + ConstExpr("2")
		self.godown()

	def continue_if(self) -> None:
		self.goup(self.stack[-1])
		self.add(";")
		self.godown()

	def end_if(self) -> None:
		self.goup(self.stack.pop())
		self.add(")")
		self.godown()
	
	def start_call(self, data: list[str|None], params: list[ConstExpr]) -> None:
		start = self.size
		if len(data) != len(params): raise TypeError(f"Expected {len(params)} parameters but got {len(data)}.")
		for i in range(len(data)):
			if data[i] != None:
				if data[i] not in self.pos_table: raise NameError(f"No such variable defined as {data[i]}.")
				self.comparisons.append((params[i], self.size_table[data[i]]))
				self.copy(data[i])
			self.size = self.size + params[i]
		self.size = start
		self.goup(self.size)
	
	def end_call(self, data: list[str|None], ret: list[ConstExpr]) -> None:
		self.godown()
		if len(data) != len(ret): raise TypeError(f"Expected {len(ret)} return parameters but got {len(data)}.")
		for i in range(len(ret)):
			if data[i] != None:
				if data[i] in self.size_table:
					self.comparisons.append((ret[i], self.size_table[data[i]]))
					self.clear_name(data[i])
					self.replace(data[i])
				else:
					self.pos_table[data[i]] = self.size
					self.size_table[data[i]] = ret[i]
			else: self.clear_pos(self.size, ret[i])
			self.size = self.size + ret[i]
	
	def start_repeat(self, num: ConstExpr) -> None:
		self.add(num)
		self.add("repeat(")
	
	def end_repeat(self) -> None:
		self.add(")")

	def copy(self, name: str) -> None:
		dif = self.size - self.pos_table[name] - ConstExpr(["1"])
		self.goup(self.pos_table[name])
		self.add("copybinx(")
		self.add(self.size_table[name])
		self.add(";")
		self.add(dif)
		self.add(")")
		# self.size = self.size + self.size_table[name]
		self.godown()

	def moveup(self, name: str) -> None:
		dif = self.size - self.pos_table[name] - ConstExpr(["1"])
		self.goup(self.pos_table[name])
		self.add("upbinx(")
		self.add(self.size_table[name])
		self.add(";")
		self.add(dif)
		self.add(")")
		self.pos_table[name] = self.size
		self.size = self.size + self.size_table[name]
		self.godown()

	def movedown(self, size: ConstExpr) -> None:
		dif = self.size - ConstExpr(["1"])
		self.goup(self.size)
		self.add("downbinx(")
		self.add(size)
		self.add(";")
		self.add(dif)
		self.add(")")
		self.godown()
	
	def replace(self, name: str) -> None:
		dif = self.size - self.pos_table[name] - ConstExpr(["1"])
		self.goup(self.size)
		self.add("downbinx(")
		self.add(self.size_table[name])
		self.add(";")
		self.add(dif)
		self.add(")")
		self.godown()

	def fuck(self, data: list[str]) -> None:
		if len(data) == 0:
			self.clear_pos(ConstExpr("0"), self.size)
			return
		if len(data) != len(self.ret): raise TypeError("Return types do not match indicated")
		size = ConstExpr("0")
		start = self.size
		for i in range(len(data)):
			if data[i] != None: 
				self.comparisons.append((self.size_table[data[i]], self.ret[i]))
				self.moveup(data[i])
			size = size + self.ret[i]
			self.size = self.size + self.ret[i]
		self.size = start
		self.clear_pos(ConstExpr("0"), self.size)
		self.movedown(size)
		self.size = size

	def clear_name(self, name: str) -> None:
		self.goup(self.pos_table[name])
		self.add(self.size_table[name])
		self.add("repeat([-]>)")
		self.add(self.size_table[name])
		self.add("repeat(<)")
		self.godown()
	
	def clear_pos(self, pos: ConstExpr, size: ConstExpr) -> None:
		self.goup(pos)
		self.add(size)
		self.add("repeat([-]>)")
		self.add(size)
		self.add("repeat(<)")
		self.godown()

	def goup(self, pos: ConstExpr) -> None:
		self.add(pos)
		self.add("repeat(>)")
		self.pos = pos
	
	def godown(self) -> None:
		self.add(self.pos)
		self.add("repeat(<)")
	
	def add(self, data: Union[str,ConstExpr,"MacroInvocation"]):
		self.code.append(data)

class ConstOp:
	# repeat, ifel, const_def
	pass

class Macro:
	def __init__(self, name: str, c_params: list[tuple[str, Any]], params: list[BinX], ret: list[ConstExpr]) -> None:
		self.name = name
		self.params = c_params
		self.data = BinXManager(params, ret)
	
	def build(name: str, c_params: list[tuple[str, Any]], params: list[BinX], ret: list[ConstExpr], include: list[ConstExpr]|None = None) -> "Macro":
		base = Macro(name, c_params, params, ret)
		base.data.add(name)
		base.data.add("(")
		if include != None:
			first = True
			for i in include:
				i.force_nnint = True
				if first: first = False
				else: base.data.add(";")
				base.data.add(i)
		base.data.add(")")
		return base
	
	def invoke(self, params: list[ConstExpr]) -> str:
		for i in range(len(params)):
			if not params[i].done: raise NameError(f"The {i}th parameter hasn't been completed.")
		code = self.data.code.copy()
		comp = self.data.comparisons.copy()
		for i in range(len(code)):
			# if type(code[j]) == String...
			if type(code[i]) == ConstExpr:
				for j in range(len(params)):
					if type(code[i]) == ConstExpr: code[i] = code[i].replace(self.params[j][0], params[j])
			if type(code[i]) == MacroInvocation: code[i].prepare([(self.params[j][0], params[j]) for j in range(len(params))])
		for i in range(len(params)):
			for j in range(len(comp)): comp[j] = comp[j][0].replace(self.params[i][0], params[i]), comp[j][1].replace(self.params[i][0], params[i])
		for i in comp:
			if str(i[0]) != str(i[1]): raise TypeError(f"Expected expressions to be the same but got {i[0]} and {i[1]}.")
		return "".join(map(str, code))



class MacroInvocation:
	def __init__(self, macro: Macro, params: list[ConstExpr]) -> None:
		if len(params) != len(macro.params): raise TypeError(f"The macro {macro.name} takes {len(macro.params)} positional arguments but {len(params)} were provided.")
		for i in range(len(params)):
			if type(params[i]) != macro.params[i][1]: raise TypeError(f"The macro {macro.name} in argument position {i} has type {macro.params[i][1]} but the type {type(params[i])} was provided.")
		self.macro = macro
		self.params = params
		self.current = None
	
	def prepare(self, params: list[tuple[str, ConstExpr]]) -> None:
		self.current = self.params.copy()
		for i in range(len(self.current)):
			for j in range(len(params)): self.current[i] = self.current[i].replace(params[j][0], params[j][1])
	
	def __str__(self) -> str:
		result = self.macro.invoke(self.current)
		self.current = None
		return result

	def test_params(self) -> list[ConstExpr]:
		p = [i.size for i in self.macro.data.params.copy()]
		for i in range(len(p)):
			for j in range(len(self.params)):
				p[i] = p[i].replace(self.macro.params[j][0], self.params[j])
		return p

	def test_ret(self) -> list[ConstExpr]:
		ret = self.macro.data.ret.copy()
		for i in range(len(ret)):
			for j in range(len(self.params)):
				ret[i] = ret[i].replace(self.macro.params[j][0], self.params[j])
		return ret

class Processor:
	inbuilt_macros = {
		"implant" : Macro.build(
			"implant",
			[("x", ConstExpr), ("v", ConstExpr)],
			[],
			[ConstExpr([ConstRef("x")])],
			[ConstExpr([ConstRef("x")]), ConstExpr([ConstRef("v")])]
			),
		"printbinx" : Macro.build(
			"printbinx",
			[("x", ConstExpr)],
			[BinX("binx", ConstExpr([ConstRef("x")]))],
			[],
			[ConstExpr([ConstRef("x")])]
			),
		"kill" : Macro.build(
			"kill",
			[],
			[],
			[],
			[]
			),
		"endl" : Macro.build(
			"endl",
			[],
			[],
			[],
			[]
			),
		"printintbinx" : Macro.build(
			"printintbinx",
			[("x", ConstExpr)],
			[BinX("binx", ConstExpr([ConstRef("x")]))],
			[],
			[ConstExpr([ConstRef("x")])]
			),
		"addbinx" : Macro.build(
			"addbinx",
			[("x", ConstExpr)],
			[BinX("a", ConstExpr([ConstRef("x")])), BinX("b", ConstExpr([ConstRef("x")]))],
			[ConstExpr([ConstRef("x")])],
			[ConstExpr([ConstRef("x")])]
			),
		"subbinx" : Macro.build(
			"subbinx",
			[("x", ConstExpr)],
			[BinX("a", ConstExpr([ConstRef("x")])), BinX("b", ConstExpr([ConstRef("x")]))],
			[ConstExpr([ConstRef("x")])],
			[ConstExpr([ConstRef("x")])]
			),
		"multbinx" : Macro.build(
			"multbinx",
			[("x", ConstExpr)],
			[BinX("a", ConstExpr([ConstRef("x")])), BinX("b", ConstExpr([ConstRef("x")]))],
			[ConstExpr([ConstRef("x")])],
			[ConstExpr([ConstRef("x")])]
			),
		"divbinx" : Macro.build(
			"divbinx",
			[("x", ConstExpr)],
			[BinX("a", ConstExpr([ConstRef("x")])), BinX("b", ConstExpr([ConstRef("x")]))],
			[ConstExpr([ConstRef("x")])],
			[ConstExpr([ConstRef("x")])]
			),
		"lshiftbinx" : Macro.build(
			"lshiftbinx",
			[("x", ConstExpr)],
			[BinX("binx", ConstExpr([ConstRef("x")]))],
			[],
			[ConstExpr([ConstRef("x")])]
			),
		"rshiftbinx" : Macro.build(
			"rshitbinx",
			[("x", ConstExpr)],
			[BinX("binx", ConstExpr([ConstRef("x")]))],
			[],
			[ConstExpr([ConstRef("x")])]
			),
	}

	def __init__(self, tree: VP.ASTNode) -> None:
		self.tree = Cleaner(tree).clean()
		self.macros: dict[str, Macro] = dict()
		self.consts: dict[str, Any] = dict()
		self.local_consts: dict[str, Any] = dict()
	
	def __const_expr(self, node: ASTNode) -> ConstExpr:
		result = ConstExpr.builder(node)
		for i, j in self.local_consts.items(): result = result.replace(i, j)
		for i, j in self.consts.items(): result = result.replace(i, j)
		return result

	def __const_def(self, node: ASTNode) -> tuple[str, Any]:
		if node.data[0].data[0].value == "num": return node.data[1].value, self.__const_expr(node.data[2])
		raise TypeError(f"Unkown type {node.data[0].data[0].value}.")
	
	def __const_param_struct(self, node: ASTNode) -> list[tuple[str, Any]]:
		data = []
		for i in range(0, len(node.data), 3):
			if node.data[i].data[0].value == "num": data.append((node.data[i + 1].value, ConstExpr))
			else: raise TypeError(f"Unkown type {node.data[i].data[0].value}.")
		return data
	
	def __const_struct(self, node: ASTNode) -> list[ConstExpr]:
		data = []
		for i in range(0, len(node.data), 2): data.append(self.__const_expr(node.data[i]))
		return data

	def __param_struct(self, node: ASTNode) -> list[BinX]:
		data = []
		for i in range(0, len(node.data), 3): data.append(BinX(node.data[i + 1], self.__const_expr(node.data[i])))
		return data

	def __var_struct(self, node: ASTNode) -> list[str|None]:
		data = []
		pos = 0
		while pos < len(node.data):
			if node.data[pos].type == TokenType.Separator: data.append(None)
			else:
				data.append(node.data[pos].value)
				pos += 1
			pos += 1
		return data
	
	def __call(self, node: ASTNode) -> tuple[MacroInvocation, list[str|None], list[str|None]]:
		name = node.data[1].value
		if name in self.macros: mi = MacroInvocation(self.macros[node.data[1].value], self.__const_struct(node.data[0]))
		elif name in Processor.inbuilt_macros: mi = MacroInvocation(Processor.inbuilt_macros[node.data[1].value], self.__const_struct(node.data[0]))
		else: raise NameError(f"The macro {name} is undefined.")
		return mi, self.__var_struct(node.data[2]), self.__var_struct(node.data[3])
	
	def __macro_def(self, node: ASTNode) -> tuple[str, Macro]:
		name = node.data[1].value
		self.local_consts = dict()
		mac = Macro(name, self.__const_param_struct(node.data[0]), self.__param_struct(node.data[3]), self.__const_struct(node.data[2]))
		def process_block(data: ASTNode) -> None:
			for i in data.data:
				stmt: ASTNode = i.data[0]
				if stmt.name == "const_def":
					cdef = self.__const_def(stmt)
					self.local_consts[cdef[0]] = cdef[1]
				elif stmt.name == "call":
					invc = self.__call(stmt)
					mac.data.start_call(invc[2], invc[0].test_params())
					mac.data.add(invc[0])
					mac.data.end_call(invc[1], invc[0].test_ret())
				elif stmt.name == "return":
					s = []
					if len(stmt.data) == 1: s = self.__var_struct(stmt.data[0])
					mac.data.fuck(s)
				elif stmt.name == "ifel":
					expr = self.__const_expr(stmt.data[0])
					if len(expr.data) == 1 and type(expr.data[0]) == ConstRef and expr.data[0].name in mac.data.pos_table:
						mac.data.start_if(expr.data[0].name)
						process_block(stmt.data[1])
						mac.data.continue_if()
						process_block(stmt.data[2])
						mac.data.end_if()
					else:
						expr_y = ConstExpr(["1 if ("]) + expr + ConstExpr([") else 0"])
						expr_n = ConstExpr(["0 if ("]) + expr + ConstExpr([") else 1"])
						mac.data.start_repeat(expr_y)
						process_block(stmt.data[1])
						mac.data.end_repeat()
						mac.data.start_repeat(expr_n)
						process_block(stmt.data[2])
						mac.data.end_repeat()
				elif stmt.name == "while_or_repeat":
					expr = self.__const_expr(stmt.data[0])
					if len(expr.data) == 1 and type(expr.data[0]) == ConstRef and expr.data[0].name in mac.data.pos_table:
						mac.data.start_while(expr.data[0].name)
						process_block(stmt.data[1])
						mac.data.end_while()
					else:
						mac.data.start_repeat(expr)
						process_block(stmt.data[1])
						mac.data.end_repeat()
				else: raise SyntaxError(f"{stmt.name}???")
		process_block(node.data[4])
		return name, mac	
	
	def process(self) -> None:
		for i in self.tree.data[:-1]:
			if i.name == "const_def":
				cdef = self.__const_def(i)
				self.consts[cdef[0]] = cdef[1]
			elif i.name == "macro_def":
				mdef = self.__macro_def(i)
				self.macros[mdef[0]] = mdef[1]
			else: raise SyntaxError(f"{i.name}???")
		self.start = self.__call(self.tree.data[-1])[0]

	def build(self) -> str:
		self.start.prepare([])
		return str(self.start)

# TODO temp
def show_AST(node: ASTNode|VP.Token, level = 0):
	print(level*"\t", end="")
	if type(node) == VP.Token: print(node.type, repr(str(node.value)))
	else:
		print("> ", node.name)
		for i in node.data:
			show_AST(i, level + 1)

if __name__ == "__main__":
	with open("test.vk", "r") as f:
		t = f.read()
	p = Parser(t)
	tree = p.parse()
	VP.show_AST(tree)
	show_AST(Cleaner(tree).clean())
	proc = Processor(tree)
	proc.process()
	result = proc.build()
	print("\n=======================\nMacrofuck form\n=======================")
	print(result)
	print("\n=======================\nRunning code...\n=======================")
	import BrainfuckInterpreter
	b = BrainfuckInterpreter.Interpreter(proc.build())
	b.run(True)
	print("\n=======================\nBrainfuck code\n=======================")
	print(b.code)
	print("\n=======================\nCode size\n=======================")
	print(len(b.code))
	print("\n=======================\nStarting Varfuck code\n=======================")
	print(t)
