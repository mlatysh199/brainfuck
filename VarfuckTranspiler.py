from enum import Enum

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

# Token container
class Token:
	def __init__(self, type: TokenType, value) -> None:
		self.type = type
		self.value = value

# Reads tokens from string
class Lexer:
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
	commands = ["return"]
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
	def process_word(self) -> Token:
		word = ""
		while self.pos < len(self.stream) and (self.stream[self.pos] in self.word_chars or self.stream[self.pos] in self.number_chars):
			word += self.stream[self.pos]
			self.pos += 1
		if word in self.commands: return Token(TokenType.Command, word)
		elif word in self.operators: return Token(TokenType.Operator, word)
		elif word in self.types: return Token(TokenType.Type, word)
		return Token(TokenType.Word, word)

	# Processes numbers
	def process_number(self) -> Token:
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
		return Token(TokenType.Number, number)

	# Processes operators
	def process_operators(self) -> Token:
		operator = self.stream[self.pos]
		self.pos += 1
		while self.pos < len(self.stream) and self.stream[self.pos] in self.operator_chars and operator + self.stream[self.pos] in self.operators:
			operator += self.stream[self.pos]
			self.pos += 1
		return Token(TokenType.Operator, operator)

	# Gets the next token
	def next_token(self) -> Token:
		if self.pos >= len(self.stream): return Token(TokenType.EOF, None)
		char = self.stream[self.pos]
		while True:
			if char in self.ignore_chars: self.pos += 1
			elif char in self.comment_chars: self.process_comment()
			else: break
			if self.pos >= len(self.stream): return Token(TokenType.EOF, None)
			char = self.stream[self.pos]
		if char in self.word_chars: return self.process_word()
		elif char in self.number_chars: return self.process_number()
		elif char in self.operator_chars: return self.process_operators()
		else: self.pos += 1
		if char in self.bracket_chars: return Token(TokenType.Bracket, char)
		elif char in self.brace_chars: return Token(TokenType.Brace, char)
		elif char in self.break_chars: return Token(TokenType.Breaker, None)
		elif char in self.separator_chars: return Token(TokenType.Separator, None)
		elif char in self.parenthesis_chars: return Token(TokenType.Parenthesis, char)
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

# Abstract Syntax Tree node
class AstNode:

	# Initializes node with current lexer
	def __init__(self, lexer: Lexer) -> None:
		self.lexer = lexer
		self.lexer_pos = lexer.get_position()
		self.children = []
	
	# Virtual method that attempts to match corresponding production rule
	def match(self) -> bool:
		return False
	
	# Resets lexer if match failed
	def __del__(self) -> None:
		self.children.clear()
		self.lexer.set_position(self.lexer_pos)

class TerminalAstNode(AstNode):

	def __init__(self, lexer: Lexer, token_type: TokenType) -> None:
		super().__init__(lexer)
		self.token_type = token_type
		self.value = None

	def match(self) -> bool:
		token = self.lexer.next_token()	
		if token.type == self.token_type:
			self.value = token.value
			return True
		return False

class Const(TerminalAstNode):
	def __init__(self, lexer: Lexer) -> None:
		super().__init__(lexer, TokenType.Number)

class String(TerminalAstNode):
	def __init__(self, lexer: Lexer) -> None:
		super().__init__(lexer, TokenType.Word)

class Parenthesis(TerminalAstNode):
	def __init__(self, lexer: Lexer) -> None:
		super().__init__(lexer, TokenType.Parenthesis)

class ConstExpr(AstNode):
	def match(self) -> bool:
		node = Const(self.lexer)
		if node.match():
			self.children.append(node)
			return True
		node = String(self.lexer)
		if node.match():
			self.children.append(node)
			node = Parenthesis(self.lexer)
			if node.match() and node.value == "(":
				self.children.append(node)
				node = ConstExpr(self.lexer)
				if node.match():
					self.children.append(node)
					node = Parenthesis(self.lexer)
					if node.match() and node.value == ")":
						self.children.append(node)
						return True
					self.children.pop()
				self.children.pop()
			self.children.pop()
		return False

class Grammar(AstNode):
	def match(self) -> bool:
		node = ConstExpr(self.lexer)
		if node.match() and TerminalAstNode(self.lexer, TokenType.EOF).match():
			self.children.append(node)
			return True
		return False


# TODO create
# Translates varfuck into macrofuck.
class Transpiler:
	def __init__(self, code):
		self.macros = []
		self.code = code.split('\n')
		self.find_macros(code)

	def find_macros(self, code):
		pass

	def convert(self, code):
		pass

	def process_math(self, code):
		pass
	
test = """f(f(f(12.55))) #wikir wakir
"""

if __name__ == "__main__":
	g = Grammar(Lexer(test))
	print(g.match())