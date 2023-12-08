from enum import Enum
import EBNF
import VirtualParser as VP
from math import *
import numbers

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

class Parser:
	terminal_dict = {
		VP.Token(EBNF.TokenType.Terminal, "return") : VP.Token(TokenType.Command, "return"),
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
		VP.Token(TokenType.Command, "return"),
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

class Processor:
	def __init__(self, tree: VP.ASTNode) -> None:
		if tree.rule != "grammar": raise SyntaxError("Not a grammar based AST.") # TODO replace with correct error
		self.tree = tree
	
	def correct_const_expr(self, node: VP.ASTNode) -> VP.ASTNode:
		pass

	def process(self) -> VP.ASTNode:
		pass

class Context:
	def __init__(self, parent: "Context" = None, const_symbol_table: dict[str, "ConstExpr"] = dict()) -> None:
		self.const_symbol_table = const_symbol_table
		self.parent = parent
	
	def get_const(self, name: str) -> "ConstExpr"|None:
		if name in self.const_symbol_table: return self.const_symbol_table[name]
		if self.parent == None: return None
		return self.parent.get_const(name)

	def add_const(self, name: str, data: "ConstExpr") -> None:
		if self.get_const(name) != None: raise NameError(f"{name} is already a defined constant.")
		self.const_symbol_table[name] = data

class ConstRef:
	def __init__(self, name: str) -> None:
		self.name = name

class ConstExpr:
	# math expressions
	def __init__(self, data: list[str|ConstRef], force_nnint = False) -> None:
		self.refs = {ref.name for ref in data if type(ref) == ConstRef}
		self.data: list[str|ConstRef] = [str(eval(" ".join(self.data)))] if not len(self.refs) else data
		self.force_nnint = force_nnint

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
		self.ret = ret
		# Helps make sure that whatever we try to return does not overwrite any if spaces
		for i in ret: self.size = self.size + i
		self.stack: list[ConstExpr] = []
		self.code: list[str|ConstExpr] = []
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
		self.size = self.size + ConstExpr("2")

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
	
	def start_call(self, data: list[BinX]) -> None:
		start = self.size
		for i in data:
			if i.name != None: self.copy(i.name)
			self.size += i.size
		self.size = start
		self.goup(self.size)
	
	def end_call(self, data: list[BinX]) -> None:
		self.godown()
		for i in data:
			if i.name != None:
				if i.name in self.size_table:
					# TODO size comparisons
					self.comparisons.append((i.size, self.size_table[i.name]))
					# if self.size_table[i.name] != i.size: raise TypeError("Can't overwrite same variable with different size.")
					self.clear_name(i.name)
					self.replace(i.name)
				else:
					self.pos_table[i.name] = self.size
					self.size_table[i.name] = i.size
			else: self.clear_pos(self.size, i.size)
			self.size += i.size

	def copy(self, name: str) -> None:
		dif = self.size - self.pos_table[name] - ConstExpr(["-1"])
		self.goup(self.pos_table[name])
		self.add("copybinx(")
		self.add(self.size_table[name])
		self.add(";")
		self.add(dif)
		self.add(")")
		# self.size = self.size + self.size_table[name]
		self.godown()

	def moveup(self, name: str) -> None:
		dif = self.size - self.pos_table[name] - ConstExpr(["-1"])
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
		dif = self.size - ConstExpr(["-1"])
		self.goup(self.size)
		self.add("downbinx(")
		self.add(size)
		self.add(";")
		self.add(dif)
		self.add(")")
		self.godown()
	
	def replace(self, name: str) -> None:
		dif = self.size - self.pos_table[name] - ConstExpr(["-1"])
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
		self.add("repeat(->)")
		self.add(self.size_table[name])
		self.add("repeat(<)")
		self.godown()
	
	def clear_pos(self, pos: ConstExpr, size: ConstExpr) -> None:
		self.goup(pos)
		self.add(size)
		self.add("repeat(->)")
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
	
	def add(self, data: str|ConstExpr):
		self.code.append(data)

class MacroFuck:
	pass

class ConstOp:
	# repeat, ifel, const_def
	pass

class Macro:
	pass

class MacroInvocation:
	def __init__(self, macro: Macro, ) -> None:
		pass

if __name__ == "__main__":
	with open("test.vk", "r") as f:
		p = Parser(f.read())
		VP.show_AST(p.parse())