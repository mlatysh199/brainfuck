from enum import Enum

# Token types
class TokenType(Enum):
	EOF = -1
	Brainfuck = 0
	Number = 1
	Macro = 2
	Params = 3

# Token container
class Token:
	def __init__(self, type : TokenType, value) -> None:
		self.type = type
		self.value = value

# Reads tokens from string
class Lexer:
	brainfuck_chars = "><+-.,[]@" # The @ symbol is a code marker
	macro_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_"
	number_chars = "0123456789"
	ignore_chars = " \t\n"
	separator_chars = ";"
	open_parenthesis_chars = "("
	close_parenthesis_chars = ")"
	comment_chars = "#"
	comment_break_chars = "\n"

	def __init__(self, stream : str) -> None:
		self.stream = stream
		self.pos = 0

	# Consumes comments
	def process_comment(self) -> None:
		while self.pos < len(self.stream) and self.stream[self.pos] not in self.comment_break_chars: self.pos += 1
		self.pos += 1

	# Processes macros
	def process_macro(self) -> Token:
		word = ""
		while self.pos < len(self.stream) and (self.stream[self.pos] in self.macro_chars or self.stream[self.pos] in self.number_chars):
			word += self.stream[self.pos]
			self.pos += 1
		return Token(TokenType.Macro, word)

	# Processes numbers
	def process_number(self) -> Token:
		number = 0
		while self.pos < len(self.stream) and self.stream[self.pos] in self.number_chars:
			number *= 10
			number += ord(self.stream[self.pos]) - ord('0')
			self.pos += 1
		return Token(TokenType.Number, number)

	# Processes params
	def process_params(self) -> Token:
		params = []
		try:
			level = 1
			self.pos += 1
			param = ""
			while level:
				char = self.stream[self.pos]
				level += char in self.open_parenthesis_chars
				level -= char in self.close_parenthesis_chars
				if level == 1 and char in self.separator_chars:
					params.append(param)
					param = ""
				else:
					param += char
				self.pos += 1
			params.append(param[:-1])
		except IndexError:
			raise IndexError("Lexer requieres that all parameters be contained.")
		return Token(TokenType.Params, params)

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
		if char in self.brainfuck_chars:
			self.pos += 1
			return Token(TokenType.Brainfuck, char)
		elif char in self.macro_chars: return self.process_macro()
		elif char in self.number_chars: return self.process_number()
		elif char in self.open_parenthesis_chars: return self.process_params()
		raise KeyError(f"{char} is not a valid character.")

# Parses and generates the compiled brainfuck.
class Compiler:
	placeholder_macros = ["while_run", "while_bool", "repeat", "ifel_true", "ifel_false", "MAC_"]
	glide_based = ["searchup255", "searchdown255", "sendboolup", "sendbooldown", "sendbooldownaddress", "writeaddress", "whilememregister", "movetoaddress", "sendboolmemdownaddress", "addmemprefix", "movememprefix", "movetonextmeminternal", "movetoprevmeminternal", "movetonextmem", "movetoprevmem", "endmemaccess", "loadbinx", "savebinx", "mallocbinx", "free", "kill"]

	def __init__(self, code : str) -> None:
		self.macros = {"repeat" : self.mac_placeholder,
		 	"implant" : self.mac_implant,
		 	"kill" : self.mac_kill,
			"upb" : self.mac_upb,
			"downb" : self.mac_downb,
			"copyb" : self.mac_copyb,
			"upbinx" : self.mac_upbinx,
			"downbinx" : self.mac_downbinx,
			"copybinx" : self.mac_copybinx,
			"bool" : self.mac_bool,
			"not" : self.mac_not,
			"and" : self.mac_and,
			"or" : self.mac_or,
			"addb" : self.mac_addb,
			"subb" : self.mac_subb,
			"multb" : self.mac_multb,
			"divb" : self.mac_divb,
			"diffb" : self.mac_diffb,
			"eqb" : self.mac_eqb,
			"lessb" : self.mac_lessb,
			"greatb" : self.mac_greatb,
			"ifel" : self.mac_ifel,
			"ifel_true" : self.mac_placeholder,
			"ifel_false" : self.mac_placeholder,
			"while" : self.mac_while,
			"while_bool" : self.mac_placeholder,
			"while_run" : self.mac_placeholder,
			"MAC_" : self.mac_placeholder,
			"moveupb" : self.mac_moveupb,
			"movedownb" : self.mac_movedownb,
			"bin8tobyte" : self.mac_bin8tobyte,
			"bytetobin8" : self.mac_bytetobin8,
			"digitbin4" : self.mac_digitbin4,
			"printb" : self.mac_printb,
			"printbinx" : self.mac_printbinx,
			"printbool" : self.mac_printbool,
			"printintbinx" : self.mac_printintbinx,
			"printdigit" : self.mac_printdigit,
			"endl" : self.mac_endl,
			"getintbinx" : self.mac_getintbinx,
			"getbinx" : self.mac_getbinx,
			"cleanbinx" : self.mac_cleanbinx,
			"boolbinx" : self.mac_boolbinx,
			"notbinx" : self.mac_notbinx,
			"andbinx" : self.mac_andbinx,
			"orbinx" : self.mac_orbinx,
			"addbinx" : self.mac_addbinx,
			"subbinx" : self.mac_subbinx,
			"rshiftbinx" : self.mac_rshiftbinx,
			"lshiftbinx" : self.mac_lshiftbinx,
			"multbinx" : self.mac_multbinx,
			"divbinx" : self.mac_divbinx,
			"modbinx" : self.mac_modbinx,
			"diffbinx" : self.mac_diffbinx,
			"eqbinx" : self.mac_eqbinx,
			"lessbinx" : self.mac_lessbinx,
			"greatbinx" : self.mac_greatbinx,
			"moveupb" : self.mac_moveupb,
			"movedownb" : self.mac_movedownb,
			"mem" : self.mac_mem,
			"searchup255" : self.mac_searchup255,
			"searchdown255" : self.mac_searchdown255,
			"sendboolup" : self.mac_sendboolup,
			"sendbooldown" : self.mac_sendbooldown,
			"sendbooldownaddress" : self.mac_sendbooldownaddress,
			"writeaddress" : self.mac_writeaddress,
			"whilememregister" : self.mac_whilememregister,
			"movetoaddress" : self.mac_movetoaddress,
			"sendboolmemdownaddress" : self.mac_sendboolmemdownaddress,
			"addmemprefix" : self.mac_addmemprefix,
			"movememprefix" : self.mac_movememprefix,
			"movetonextmeminternal" : self.mac_movetonextmeminternal,
			"movetoprevmeminternal" : self.mac_movetoprevmeminternal,
			"movetonextmem" : self.mac_movetonextmem,
			"movetoprevmem" : self.mac_movetoprevmem,
			"endmemaccess" : self.mac_endmemaccess,
			"loadbinx" : self.mac_loadbinx,
			"savebinx" : self.mac_savebinx,
			"mallocbinx" : self.mac_mallocbinx,
			"free" : self.mac_free}
		self.has_memory = False
		self.memory_address_size = 0
		self.pc = 0
		self.stack_trace_data = [dict(), dict()]
		self.in_mem = False
		self.min_mem_size = 0
		self.current_mem_size = 0
		self.bf = self.convert(code)
		self.min_mem_size += 1

	# Returns the generated brainfuck code
	def get_bf(self) -> str:
		return self.bf

	# Returns the generated macro stack trace
	def get_stack_trace_data(self) -> list[dict]:
		return self.stack_trace_data

	# Converter system
	def convert(self, code : str) -> str:
		lexer = Lexer(code)
		result = ""
		number = 1
		token = lexer.next_token()
		while token.type != TokenType.EOF:
			if token.type == TokenType.Brainfuck:
				result += token.value*number
				self.pc += number
				if token.value == '>' and not self.in_mem:
					self.current_mem_size += number
					self.min_mem_size = max(self.current_mem_size, self.min_mem_size)
				if token.value == '<' and not self.in_mem: self.current_mem_size -= number
				number = 1
			elif token.type == TokenType.Number: number = token.value
			elif token.type == TokenType.Macro:
				macro = token.value
				if macro not in self.macros: raise NameError(f"The bf-macro '{macro}' is not defined (pos: {lexer.pos - len(macro)}).")
				before_mem = self.in_mem
				self.in_mem = macro in self.glide_based or self.in_mem
				token = lexer.next_token()
				if token.type != TokenType.Params: raise SyntaxError(f"Expected lexer type was {TokenType.Params.name} (got {token.type.name} instead).")
				params = token.value
				macro_id = macro if macro != "MAC_" else params[0]
				if macro == "MAC_": params = params[1:]
				if macro not in self.placeholder_macros or params[0]:
					for i in range(number):
						if self.pc not in self.stack_trace_data[0]:
							self.stack_trace_data[0][self.pc] = []
						self.stack_trace_data[0][self.pc].append(macro_id + f"_{i}"*(number != 1))
						result += self.macros[macro](params)
						if self.pc - 1 not in self.stack_trace_data[1]:
							self.stack_trace_data[1][self.pc - 1] = []
						self.stack_trace_data[1][self.pc - 1].insert(0, macro_id + f"_{i}"*(number != 1))
				self.in_mem = before_mem
				number = 1
			else: raise SyntaxError(f"Unknown lexer type ({token.type.name}).")
			token = lexer.next_token()
		return result
	
	def param_to_number(self, param : str) -> int:
		lexer = Lexer(param)
		token = lexer.next_token()
		if token.type != TokenType.Number: raise SyntaxError("This parameter expected a number.")
		return token.value
	
	# Searches for value 254, which is reserved for killing the program
	def mac_kill(self, values : list[str]) -> str:
		return self.convert("2+[2-<2+]2-")

	# Placeholder function
	def mac_placeholder(self, values : list[str]) -> str:
		return self.convert(f"{values[0]}")

	def mac_implant(self, values : list[str]) -> str:
		x = self.param_to_number(values[0])
		v = self.param_to_number(values[1])
		data = bin(v)[2:]
		if len(data) >= x: data = data[len(data) - x:]
		else: data = '0'*(x - len(data)) + data
		implant = '>'.join(['+' if i == '1' else '' for i in data])
		return self.convert(implant + '<'*(x - 1))

	# Move byte up to x distance
	# A<x>B
	def mac_upb(self, values : list[str]) -> str:
		x = self.param_to_number(values[0])
		return self.convert(f"[-{x}>>+{x}<<]")

	# B<x>A
	# Move byte down to x distance
	def mac_downb(self, values : list[str]) -> str:
		x = self.param_to_number(values[0])
		return self.convert(f"[-{x}<<+{x}>>]")

	# B = A
	# A<x>B.
	def mac_copyb(self, values : list[str]) -> str:
		x = self.param_to_number(values[0])
		return self.convert(f"[-{x}>>+>+<<{x}<]{x}>>>[-{x}<<<+{x}>>>]{x}<<<")
	
	# Moves a group of variables up
	# (A*x)<y>(B*x).
	def mac_upbinx(self, values : list[str]) -> str:
		x = self.param_to_number(values[0])
		y = self.param_to_number(values[1])
		return self.convert(f"{x}>{x}repeat(<upb({y}))")

	# Moves a group of variables down
	# (A*x)<y>(B*x).
	def mac_downbinx(self, values : list[str]) -> str:
		x = self.param_to_number(values[0])
		y = self.param_to_number(values[1])
		return self.convert(f"{x}repeat(downb({y})>){x}<")

	# Copies a group of variables
	# (A*x)<y>(B*x).
	def mac_copybinx(self, values : list[str]) -> str:
		x = self.param_to_number(values[0])
		y = self.param_to_number(values[1])
		return self.convert(f"copyb({y}){x - 1}repeat(>copyb({y})){x - 1}<")

	# A += B
	# AB
	def mac_addb(self, values : list[str]) -> str:
		return self.convert(">downb(0)<")

	# A -= B
	# AB
	def mac_subb(self, values : list[str]) -> str:
		return self.convert(">[-<->]<")

	# A *= B
	# AB..
	def mac_multb(self, values : list[str]) -> str:
		return self.convert(">[-<copyb(1)>]<[-]>>downb(1)<<")

	# A = A/B, B = A%B
	# AB...........
	def mac_divb(self, values : list[str]) -> str:
		return self.convert("[2repeat(copyb(2)>)>lessb()ifel(5<upb(4)5>;3<+<copyb(4)<subb()6>downb(4)<)3<]>[-]>downb(1)3>downb(3)5<")

	# A != B
	# AB
	def mac_diffb(self, values : list[str]) -> str:
		return self.convert("subb()bool()")

	# A == B
	# AB
	def mac_eqb(self, values : list[str]) -> str:
		return self.convert("diffb()not()")

	# A < B
	# AB........
	def mac_lessb(self, values : list[str]) -> str:
		return self.convert("2repeat(copyb(1)>)diffb()ifel(3<[-<copyb(1)2>ifel(4<-4>;3<[-]4>+<)<]<[-]>[-]4>downb(4)<;4<[-]>[-]3>)2<")

	# A > B
	# AB........
	def mac_greatb(self, values : list[str]) -> str:
		return self.convert("upb(1)2repeat(>downb(0))<<lessb()")

	# A > 0
	# A.
	def mac_bool(self, values : list[str]) -> str:
		return self.convert("[[-]>+<]addb()")

	# not A
	# A.
	def mac_not(self, values : list[str]) -> str:
		return self.convert("bool()-[+>+<]addb()")

	# A && B
	# AB.
	def mac_and(self, values : list[str]) -> str:
		return self.convert(">bool()upb(0)<bool()>>downb(0)<<addb()>++<eqb()")

	# A || B
	# AB
	def mac_or(self, values : list[str]) -> str:
		return self.convert("addb()bool()")

	# If not A then execute code one, otherwise code 2
	# A.?
	def mac_ifel(self, values : list[str]) -> str:
		return self.convert(f"bool()[->>ifel_true({values[0]})<+<]->downb(0)<[+>>ifel_false({values[1]})<<]")
	
	# While values[0] (where that code gives represents a condition): execute values[1]
	# .. (because of the bool)
	def mac_while(self, values : list[str]) -> str:
		return self.convert(f"while_bool({values[0]})bool()[-while_run({values[1]})while_bool({values[0]})bool()]")

	# Constructs a byte from binary data and puts it into A
	# A8.
	def mac_bin8tobyte(self, values : list[str]) -> str:
		return self.convert("[-8>128+8<]>[-7>64+7<]>[-6>32+6<]>[-5>16+5<]>[-4>8+4<]>[-3>4+3<]>[->>2+<<]>[->1+<]>downb(7)8<")

	# Constructs binary information from A
	# A8...........
	def mac_bytetobin8(self, values : list[str]) -> str:
		return self.convert(">128+<divb()>>64+<divb()>>32+<divb()>>16+<divb()>>8+<divb()>>4+<divb()>>2+<divb()6<")

	def mac_digitbin4(self, values : list[str]) -> str:
		return self.convert(">8+<divb()>>4+<divb()>>2+<divb()2<")

	# Prints out the byte A
	# A............
	def mac_printb(self, values : list[str]) -> str:
		return self.convert(">100+<divb()[48+.[-]]addb()>10+<divb()[48+.[-]]addb()48+.[-]")

	# Prints out the binary information AX
	# AX.
	def mac_printbinx(self, values : list[str]) -> str:
		x = self.param_to_number(values[0])
		return self.convert(f"{x}repeat(48+.[-]>){x}<")

	# Prints TRUE or FALSE respectively
	# A..
	def mac_printbool(self, values : list[str]) -> str:
		return self.convert("ifel(84+.2-.3+.16-.[-];70+.5-.11+.7+.14-.[-])")

	# Prints an integer (at least 4 bits)
	def mac_printintbinx(self, values : list[str]) -> str:
		x = self.param_to_number(values[0])
		bx = 1 << x
		ten = 1
		while ten*10 < bx: ten *= 10
		data = ""
		while ten:
			data += f"copybinx({x};{x - 1}){2*x}>implant({x};{ten}){x}<divbinx({x}){x - 4}>printdigit(){x - 4}<implant({x};{ten}){x}<modbinx({x})"
			ten //= 10
		return self.convert(data)

	def mac_printdigit(self, values : list[str]) -> str:
		return self.convert(f"[-4>8+4<]>[-3>4+3<]>[-2>2+2<]>[->+<]>48+.[-]4<")

	# Prints a line change
	# .
	def mac_endl(self, values : list[str]) -> str:
		return self.convert("10+.[-]")

	# At least bin4
	def mac_getintbinx(self, values : list[str]) -> str:
		x = self.param_to_number(values[0])
		return self.convert(f"{x}>while(,48-copyb(0)2>10+<lessb();<upb({6*x + 11})implant({x};10){x}<multbinx({x}){7*x + 12}>downb({6*x + 11}){6*x + 12}<{x - 4}repeat(upb(0)>)digitbin4(){2*x - 4}<addbinx({x}){x}>)<[-]{x}<")

	def mac_getbinx(self, values : list[str]) -> str:
		x = self.param_to_number(values[0])
		return self.convert(f"{x}repeat(,48-bool()>){x}<")

	# Sets a binx value to 0
	# AX
	def mac_cleanbinx(self, values : list[str]) -> str:
		x = self.param_to_number(values[0])
		return self.convert(f"[-]{x - 1}repeat(>[-]){x - 1}<")

	# Gets boolean value of AX
	# AX
	def mac_boolbinx(self, values : list[str]) -> str:
		x = self.param_to_number(values[0])
		return self.convert(f"{x - 1}>{x - 1}repeat(<or())")

	# Gets not value of AX
	# AX..
	def mac_notbinx(self, values : list[str]) -> str:
		x = self.param_to_number(values[0])
		return self.convert(f"{x}>{x}repeat(<not()upb(0))>downbinx(8;0)<")

	# AX and BX
	# AXBX.
	def mac_andbinx(self, values : list[str]) -> str:
		x = self.param_to_number(values[0])
		return self.convert(f"{x}>{x}repeat(<upb({x - 1}){x}>>++<eqb()downb({x - 1}){x}<)")

	# AX or BX
	# AXBX.
	def mac_orbinx(self, values : list[str]) -> str:
		x = self.param_to_number(values[0])
		return self.convert(f"{x}>{x}repeat(<upb({x - 1}){x}>bool()downb({x - 1}){x}<)")
	
	# AX += BX
	# AXBX.........
	def mac_addbinx(self, values : list[str]) -> str:
		x = self.param_to_number(values[0])
		x1 = x + 9
		return self.convert(f"{x}>{x}repeat(<upb({x+3}){x}>upb({6})>ifel(>ifel(>ifel(9<+{x}<+{x1}>;9<+9>)<;>ifel(9<+9>;{x1}<+{x1}>)<)<;>ifel(>ifel(9<+9>;{x1}<+{x1}>)<;>ifel({x1}<+{x1}>;)<)<){x + 1}<){x}>[-]{x}<")

	# AX -= BX
	# AXBX.........
	def mac_subbinx(self, values : list[str]) -> str:
		x = self.param_to_number(values[0])
		x1 = x + 9
		return self.convert(f"{x}>{x}repeat(<upb({x+3}){x}>upb({6})>ifel(>ifel(>ifel(9<+{x}<+{x1}>;)<;>ifel(9<+9>;9<+{x}<+{x1}>)<)<;>ifel(>ifel(;{x1}<+{x1}>)<;>ifel(9<+{x}<+{x1}>;)<)<){x + 1}<){x}>[-]{x}<")

	def mac_rshiftbinx(self, values : list[str]) -> str:
		x = self.param_to_number(values[0])
		return self.convert(f"{x - 1}>[-]{x - 1}repeat(<upb(0))")

	def mac_lshiftbinx(self, values : list[str]) -> str:
		x = self.param_to_number(values[0])
		return self.convert(f"[-]{x - 1}repeat(>downb(0)){x - 1}<")

	def mac_multbinx(self, values : list[str]) -> str:
		x = self.param_to_number(values[0])
		return self.convert(f"{x}>upbinx({x};{x + 1}){x}repeat(<ifel(>copybinx({2*x};{4*x - 1}){2*x}>addbinx({2*x}){2*x + 1}<;)3>lshiftbinx({2*x}){2+x}<rshiftbinx({x}){x}>)2>cleanbinx({2*x})@{2*x}>{x}lshiftbinx({2*x})downbinx({x};{x + 2 + 2*x - 1}){x + 2 + 2*x}<")
	
	# Min x size: 4
	def mac_divbinx(self, values : list[str]) -> str:
		x = self.param_to_number(values[0])
		return self.convert(f"""upbinx({x};{3*x - 1}){x}>copybinx({x};{3*x - 1}){3*x}>eqbinx({x})ifel(kill();)implant({x};{x})while(
				while(
					{3*x}<copybinx({2*x};{4*x - 1}){2*x}>copybinx({x};{5*x - 1}){2*x}>greatbinx({2*x})not()copyb(1)2>not()ifel(
						{4 + x}<copybinx({x};{x - 1 + 4}){4 + x}>diffbinx({x})downb(2)
					;)<
				;
					{x - 2}>+{2*x - 1}<subbinx({x}){3*x}<rshiftbinx({2*x}){x}<lshiftbinx({x}){4*x}>
				)
			  <
			  ;
			  	{4*x + 1}<+>copybinx({2*x};{6*x - 1}){2*x}>upbinx({x};{3*x - 1}){x + x}>subbinx({2*x}){x}>downbinx({x};{3*x - 1}){2*x}<
			  ){4*x}<cleanbinx({3*x}){x}<""")

	# Min x size: 4
	def mac_modbinx(self, values : list[str]) -> str:
		x = self.param_to_number(values[0])
		return self.convert(f"2repeat(copybinx({x};{2*x - 1}){x}>)divbinx({x}){x}<multbinx({x}){x}<subbinx({x})")

	def mac_diffbinx(self, values : list[str]) -> str:
		x = self.param_to_number(values[0])
		return self.convert(f"subbinx({x})boolbinx({x})")

	def mac_eqbinx(self, values : list[str]) -> str:
		x = self.param_to_number(values[0])
		return self.convert(f"subbinx({x})boolbinx({x})not()")
	
	def mac_lessbinx(self, values : list[str]) -> str:
		x = self.param_to_number(values[0])
		return self.convert(f"""copybinx({x};{2*x - 1}){x}>copybinx({x};{2*x - 1}){x}>diffbinx({x})upb(0)>ifel(
			  3<while(
				{2*x}<copyb({2*x - 1}){x}>copyb({x}){x}>eqb()
				;
				2repeat({x}<lshiftbinx({x})){2*x}>
			  )
			  	{2*x}<upb({2*x + 3}){x}>upb({x}){x + 1}>ifel(>ifel(;6<+6>)<;)2>;){2*x + 1}<cleanbinx({2*x}){2*x}>downb({2*x - 1}){2*x}<""")
	
	def mac_greatbinx(self, values : list[str]) -> str:
		x = self.param_to_number(values[0])
		return self.convert(f"""copybinx({x};{2*x - 1}){x}>copybinx({x};{2*x - 1}){x}>diffbinx({x})upb(0)>ifel(
			  3<while(
				{2*x}<copyb({2*x - 1}){x}>copyb({x}){x}>eqb()
				;
				2repeat({x}<lshiftbinx({x})){2*x}>
			  )
			  	{2*x}<upb({2*x + 3}){x}>upb({x}){x + 1}>ifel(;>ifel(6<+6>;)<)2>;){2*x + 1}<cleanbinx({2*x}){2*x}>downb({2*x - 1}){2*x}<""")

	# Deprecated
	def mac_moveupb(self, values : list[str]) -> str:
		return self.convert("[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[->]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]")
	
	# Deprecated
	def mac_movedownb(self, values : list[str]) -> str:
		return self.convert("[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]")

	# Initiates memory system
	# First bit/byte is saved for memory travel outpost
	# Next values[0]*2 + 11 bits/bytes are the memory address size plus the space needed to use the address
	# Each value stored in memory has 3 extra spaces to permit copies plus position data
	# Each binx value stored in memory has a preceding values[0] bits*4 to indicate the size of the occupied chunk for algorithms such as malloc
	# values[1] determines the number of memory bit/byte cells
	# The last reserved byte is set to 243 as a memory delimiter for mallocbinx
	def mac_mem(self, values : list[str]) -> str:
		x = self.param_to_number(values[0])
		y = self.param_to_number(values[1])
		self.memory_address_size = x
		self.has_memory = True
		return self.convert(f"-{1 + self.memory_address_size*2 + 9 + y*4}>3-4>")

	# Looks up to find a cell equal to 255
	def mac_searchup255(self, values : list[str]) -> str:
		if not self.has_memory: raise MemoryError("Memory was never initiated.")
		return self.convert(">+[->+]-")

	# Looks down to find a cell equal to 255
	def mac_searchdown255(self, values : list[str]) -> str:
		if not self.has_memory: raise MemoryError("Memory was never initiated.")
		return self.convert("<+[-<+]-")
	
	# Sends a boolean up from memory
	# (no idea how to format this stack descriptor)
	def mac_sendboolup(self, values : list[str]) -> str:
		if not self.has_memory: raise MemoryError("Memory was never initiated.")
		return self.convert("+3<copyb(0)>ifel(-searchup255()++>-searchdown255();-searchup255()+>-searchdown255())>>")

	# Sends a boolean down to memory (if positioning is loaded)
	# A..
	def mac_sendbooldown(self, values : list[str]) -> str:
		if not self.has_memory: raise MemoryError("Memory was never initiated.")
		return self.convert("ifel(-searchdown255()+3<[-]+<-4>searchup255()+;-searchdown255()+3<[-]<-4>searchup255()+)")

	# Sends a boolean down to the memory address section
	# A..
	def mac_sendbooldownaddress(self, values : list[str]) -> str:
		if not self.has_memory: raise MemoryError("Memory was never initiated.")
		return self.convert("ifel(-searchdown255()++<->searchup255()+;-searchdown255()+<->searchup255()+)")

	# Moves an address down to be loaded into the memory address
	# AY.. (y is the default memory address size)
	def mac_writeaddress(self, values : list[str]) -> str:
		if not self.has_memory: raise MemoryError("Memory was never initiated.")
		return self.convert(f"{self.memory_address_size}>-searchdown255()+{self.memory_address_size}>-searchup255()+{self.memory_address_size}repeat(<sendbooldownaddress())")

	def mac_sendboolmemdownaddress(self, values : list[str]) -> str:
		if not self.has_memory: raise MemoryError("Memory was never initiated.")
		return self.convert("+3<copyb(0)>ifel(-searchdown255()++>-searchup255();-searchdown255()+>-searchup255())>>")

	# Adds current prefix in memory to address buffer
	# 0{self.memory_address_size}
	def mac_addmemprefix(self, values : list[str]) -> str:
		if not self.has_memory: raise MemoryError("Memory was never initiated.")
		return self.convert(f"searchdown255(){self.memory_address_size + 1}>-{self.memory_address_size}repeat(movetonextmeminternal()sendboolmemdownaddress())searchdown255()+searchup255(){self.memory_address_size}repeat(movetoprevmeminternal())")

	def mac_movememprefix(self, values : list[str]) -> str:
		if not self.has_memory: raise MemoryError("Memory was never initiated.")
		return self.convert(f"searchdown255()>-searchup255(){self.memory_address_size}repeat(movetonextmeminternal()sendboolmemdownaddress())searchdown255()+searchup255(){self.memory_address_size}repeat(movetoprevmeminternal())")

	def mac_whilememregister(self, values : list[str]) -> str:
		return self.convert(f"while(>copybinx({self.memory_address_size};{self.memory_address_size - 1}){self.memory_address_size}>boolbinx({self.memory_address_size});{self.memory_address_size - 1}>+searchdown255()>subbinx({self.memory_address_size})searchup255(){values[0]}searchdown255())")

	# Uses the loaded pointer to find the respective position in memory
	#0
	def mac_movetoaddress(self, values : list[str]) -> str:
		if not self.has_memory: raise MemoryError("Memory was never initiated.")
		return self.convert(f"-searchdown255()>{self.memory_address_size}>{self.memory_address_size}>9>3>-searchdown255()whilememregister(movetonextmeminternal())2searchup255()+")

	# Move the memory pointer right
	#0
	def mac_movetonextmeminternal(self, values : list[str]) -> str:
		if not self.has_memory: raise MemoryError("Memory was never initiated.")
		return self.convert("+4>-")

	# Move the memory pointer left
	#0
	def mac_movetoprevmeminternal(self, values : list[str]) -> str:
		if not self.has_memory: raise MemoryError("Memory was never initiated.")
		return self.convert("+4<-")

	# Move the memory pointer right
	#0
	def mac_movetonextmem(self, values : list[str]) -> str:
		if not self.has_memory: raise MemoryError("Memory was never initiated.")
		return self.convert("-searchdown255()movetonextmeminternal()searchup255()+")

	# Move the memory pointer left
	#0
	def mac_movetoprevmem(self, values : list[str]) -> str:
		if not self.has_memory: raise MemoryError("Memory was never initiated.")
		return self.convert("-searchdown255()movetoprevmeminternal()searchup255()+")
	
	# Ends access to memory
	#0
	def mac_endmemaccess(self, values : list[str]) -> str:
		if not self.has_memory: raise MemoryError("Memory was never initiated.")
		return self.convert("-searchdown255()+searchup255()+")

	# Reads binx from address BY
	# max(BY, binx)
	def mac_loadbinx(self, values : list[str]) -> str:
		if not self.has_memory: raise MemoryError("Memory was never initiated.")
		x = self.param_to_number(values[0])
		return self.convert(f"writeaddress()movetoaddress()-searchdown255(){self.memory_address_size + 1}movetonextmeminternal(){x}repeat(sendboolup()movetonextmeminternal())+searchup255()+{x}<")
	
	# Saves AX to address BY
	# AXBY..
	def mac_savebinx(self, values : list[str]) -> str:
		if not self.has_memory: raise MemoryError("Memory was never initiated.")
		x = self.param_to_number(values[0])
		return self.convert(f"{x}>writeaddress()movetoaddress()-searchdown255(){x + self.memory_address_size}movetonextmeminternal()searchup255()+{x}repeat(<sendbooldown())endmemaccess()")

	# Occupies the first memory chunk with sufficient size. Stops the program if no space is found
	# Y. (ie, empty stack input for the placement of the pointer) (specify in the params the size that is required)
	def mac_mallocbinx(self, values : list[str]) -> str:
		x = self.param_to_number(values[0])
		binary1 = bin(self.memory_address_size)[2:]
		binary1 = '0'*(self.memory_address_size - len(binary1)) + binary1
		binary2 = bin(x)[2:]
		binary2 = '0'*(self.memory_address_size - len(binary2)) + binary2
		writebin1 = ''.join([f">[-]{i}+" for i in binary1])
		writebin2 = ''.join([f"4>[-]{i}+" for i in binary2])
		code = f"""# Prepare
-searchdown255()>{2*self.memory_address_size}>9>1>
# While we have not found a space, go up.
while(<copyb(0)>3+ifel(;kill())<copyb(0)>ifel(
		# If current space is 1, get the size of the memory chunk and jump over it
		# Jump over initial part
		-searchup255(){self.memory_address_size}>{writebin1}{self.memory_address_size*2}<>addbinx({self.memory_address_size})<searchdown255()
		# Add on the rest
		movememprefix(){self.memory_address_size - 1}movetonextmeminternal()4>-2searchdown255()whilememregister(searchup255()movetonextmeminternal()
			# Add one to the positioning
			searchup255(){self.memory_address_size*2}>+{self.memory_address_size*2}<>addbinx({self.memory_address_size})<searchdown255()
		searchdown255())searchup255()+searchup255()2+
		# If current space is 0, check if it has enough space for another memory chunk
		;<->{self.memory_address_size}repeat(4>)-{x}repeat(movetonextmeminternal()+3<copyb(0)>3+ifel(;kill())<copyb(0)>ifel(-searchdown255()>[-]+searchup255();-)2>)+searchdown255()+>)2>downb(1)2<
	# Sum one to the malloced address
	;2>-searchup255(){self.memory_address_size*2}>+{self.memory_address_size*2}<>addbinx({self.memory_address_size})<searchdown255()movetonextmeminternal()+2<)
# Write the size data to indicate the size of the new memory chunk
<+{writebin2}searchup255()+>downbinx({self.memory_address_size};0)<"""
		return self.convert(code)

	# Frees the memory chunk
	# Dynamic
	# AY..
	def mac_free(self, values : list[str]) -> str:
		if not self.has_memory: raise MemoryError("Memory was never initiated.")
		return self.convert(f"writeaddress()movetoaddress()-searchdown255()movememprefix(){self.memory_address_size - 1}movetonextmeminternal()4>-2searchdown255()whilememregister(searchup255()movetonextmeminternal()3<[-]3>searchdown255())2searchup255()+searchdown255()2movetonextmeminternal(){self.memory_address_size + 1}repeat(movetoprevmeminternal()3<[-]3>)+searchup255()+")
	
if __name__ == "__main__":
	pass