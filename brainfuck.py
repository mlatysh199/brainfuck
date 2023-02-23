import sys

# Runs brainfuck code
class Interpreter:
	def __init__(self, converter, debug=False, size=None):
		if not size: size = converter.min_mem_size()
		elif size < converter.min_mem_size(): raise IndexError(f"This program requires at least {converter.min_mem_size()} units of memory.")
		self.debug = debug
		self.code = converter.get_bf()
		self.stack_trace_data = converter.get_stack_trace_data()
		self.size = size
		self.reset()

	# Presets all the execution data
	def reset(self):
		self.ptr = 0
		self.in_tape_pos = 0
		self.mem = [0]*self.size
		self.pc = 0
		self.return_stack = []
		self.stack_trace = ["start"]

	# Shows debug info
	def __debug(self, ins):
		result = ""
		mem_text = list('  ' + '  '.join([str(i).rjust(3) for i in self.mem]) + '  ')
		mem_text[5 + self.ptr*5] = '#'
		if self.pc in self.stack_trace_data[1] and (ins != ']' or not self.mem[self.ptr]):
			for _ in range(len(self.stack_trace_data[1][self.pc])): self.stack_trace.pop()
			result += "DEBUG: " + " > ".join(self.stack_trace) + " <<< " + " < ".join(self.stack_trace_data[1][self.pc]) + '\n'
		elif self.pc in self.stack_trace_data[0] and (ins != '[' or len(self.stack_trace) < len(self.stack_trace_data[0][self.pc]) or self.stack_trace[-len(self.stack_trace_data[0][self.pc]):] != self.stack_trace_data[0][self.pc]):
			result += "DEBUG: " + " > ".join(self.stack_trace) + ' '
			self.stack_trace += self.stack_trace_data[0][self.pc]
			result += ">>> " + " > ".join(self.stack_trace_data[0][self.pc]) + '\n'
		result += f"DEBUG: {str(self.pc).rjust(4)} {ins} {str(self.ptr).rjust(3)}  [{''.join(mem_text)}]"
		return result

	# Main runner system
	def run(self, in_tape=""):
		length = len(self.code)
		result = ""
		while self.pc < length:
			ins = self.code[self.pc]
			if self.debug: print(self.__debug(ins))
			if ins == '<': self.ptr -= 1
			elif ins == '>': self.ptr += 1
			elif ins == '-': self.mem[self.ptr] = (self.mem[self.ptr] - 1)&255
			elif ins == '+': self.mem[self.ptr] = (self.mem[self.ptr] + 1)&255
			elif ins == '.':
				result += chr(self.mem[self.ptr])
				if not in_tape: print(chr(self.mem[self.ptr]), end='')
			elif ins == ',':
				char = ''
				if in_tape:
					char = in_tape[self.in_tape_pos]
					self.in_tape_pos += 1
				else: char = sys.stdin.read(1)
				self.mem[self.ptr] = ord(char)&255
			elif ins == '[':
				self.return_stack.append(self.pc)
				if not self.mem[self.ptr]:
					brks = 1
					while brks:
						self.pc += 1
						brks = brks + (self.code[self.pc] == '[') - (self.code[self.pc] == ']')
					self.pc -= 1
			elif ins == ']':
				ret = self.return_stack.pop()
				if self.mem[self.ptr]: self.pc = ret - 1
			if self.ptr < 0 or self.ptr >= self.size: raise MemoryError("Pointer exceeded designated memory.")
			self.pc += 1
		if self.debug: print(self.__debug(' '))
		return result

# TODO comparisons for xbit numbers
# TODO multiplication
# TODO division
# TODO printing xbit numbers 
"""
>>> int("11111111111111111111111111111111", 2)//1000000000
4
>>> bin(1000000000)
'0b111011100110101100101000000000'
>>> bin(100000000)
'0b101111101011110000100000000'
>>> bin(10000000)
'0b100110001001011010000000'
>>> bin(1000000)
'0b11110100001001000000'
>>> bin(100000)
'0b11000011010100000'
>>> bin(10000)
'0b10011100010000'
>>> bin(1000)
'0b1111101000'
>>> bin(100)
'0b1100100'
>>> 
"""
# TODO malloc and freeeeee

# Converts pseudo brainfuck code to brainfuck
class Converter:
	def __init__(self, code):
		self.functions = {"repeat(" : self.func_repeat,
			"upb(" : self.func_upb,
			"downb(" : self.func_downb,
			"copyb(" : self.func_copyb,
			"upbs(" : self.func_upbs,
			"downbs(" : self.func_downbs,
			"copybs(" : self.func_copybs,
			"bool(" : self.func_bool,
			"not(" : self.func_not,
			"and(" : self.func_and,
			"or(" : self.func_or,
			"addb(" : self.func_addb,
			"subb(" : self.func_subb,
			"multb(" : self.func_multb,
			"divb(" : self.func_divb,
			"diffb(" : self.func_diffb,
			"eqb(" : self.func_eqb,
			"lessb(" : self.func_lessb,
			"greatb(" : self.func_greatb,
			"ifel(" : self.func_ifel,
			"while(" : self.func_while,
			"forb(" : self.func_forb,
			"moveupb(" : self.func_moveupb,
			"movedownb(" : self.func_movedownb,
			"bin8tobyte(" : self.func_bin8tobyte,
			"bytetobin8(" : self.func_bytetobin8,
			"printb(" : self.func_printb,
			"printbin8(" : self.func_printbin8,
			"printbool(" : self.func_printbool,
			"endl(" : self.func_endl,
			"boolbinx(" : self.func_boolbinx,
			"notbinx(" : self.func_notbinx,
			"andbinx(" : self.func_andbinx,
			"orbinx(" : self.func_orbinx,
			"addbinx(" : self.func_addbinx,
			"subbinx(" : self.func_subbinx,
			"multbinx(" : self.func_multbinx,
			"divbinx(" : self.func_divbinx,
			"diffbbinx(" : self.func_diffbinx,
			"eqbinx(" : self.func_eqbinx,
			"lessbinx(" : self.func_lessbinx,
			"greatbinx(" : self.func_greatbinx,
			"forbinx(" : self.func_forbinx,
			"moveupb(" : self.func_moveupb,
			"movedownb(" : self.func_movedownb,
			"mem(" : self.func_mem,
			"searchup255(" : self.func_searchup255,
			"searchdown255(" : self.func_searchdown255,
			"sendboolup(" : self.func_sendboolup,
			"sendbooldown(" : self.func_sendbooldown,
			"sendbooldownaddress(" : self.func_sendbooldownaddress,
			"writeaddress(" : self.func_writeaddress,
			"movetoaddress(" : self.func_movetoaddress,
			"sendboolmemdownaddress(" : self.func_sendboolmemdownaddress,
			"addmemprefix(" : self.func_addmemprefix,
			"movememprefix(" : self.func_movememprefix,
			"movetonextmeminternal(" : self.func_movetonextmeminternal,
			"movetoprevmeminternal(" : self.func_movetoprevmeminternal,
			"movetonextmem(" : self.func_movetonextmem,
			"movetoprevmem(" : self.func_movetoprevmem,
			"endmemaccess(" : self.func_endmemaccess,
			"loadbinx(" : self.func_loadbinx,
			"savebinx(" : self.func_savebinx,
			"mallocbinx(" : self.func_mallocbinx,
			"free(" : self.func_free}
		self.has_memory = False
		self.memory_address_size = 0
		self.commands = ['<', '>', '-', '+', '.', ',', '[', ']']
		self.skip = [' ', '\n', '\t']
		self.numbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
		self.pc = 0
		self.stack_trace_data = [dict(), dict()]
		self.bf = self.convert(code)

	# Returns the generated brainfuck code
	def get_bf(self):
		return self.bf

	# Returns the generated function stack trace
	def get_stack_trace_data(self):
		return self.stack_trace_data

	# Converter system
	def convert(self, code):
		result = ""
		pos = 0
		number = 0
		number_mode = False
		while pos < len(code):
			if code[pos] in self.commands:
				result += code[pos]*(number + (not number and not number_mode))
				self.pc += (number + (not number and not number_mode))
				number = 0
				number_mode = False
			elif code[pos] in self.numbers:
				number_mode = True
				number *= 10
				number += int(code[pos])
			elif code[pos] == '#':
				while pos < len(code) and code[pos] != '\n': pos += 1
			elif code[pos] not in self.skip:
				function = ""
				while function not in self.functions:
					if function and function[-1] == '(': raise NameError(f"The bf-function '{function[:-1]}' is not defined (pos: {pos - len(function)}).")
					function += code[pos]
					pos += 1
				params = []
				param = ""
				level = 1
				while level > 1 or code[pos] != ')':
					if code[pos] == ';' and level == 1:
						params.append(param)
						param = ""
					elif level > 1 or code[pos] != ')': param += code[pos]
					level += code[pos] == '('
					level -= code[pos] == ')'
					pos += 1
				params.append(param)
				for _ in range(number + (not number and not number_mode)):
					if self.pc not in self.stack_trace_data[0]:
						self.stack_trace_data[0][self.pc] = []
					self.stack_trace_data[0][self.pc].append(function[:-1])
					result += self.functions[function](params)
					if self.pc - 1 not in self.stack_trace_data[1]:
						self.stack_trace_data[1][self.pc - 1] = []
					self.stack_trace_data[1][self.pc - 1].insert(0, function[:-1])
			if code[pos] not in self.numbers:
				number = 0
				number_mode = False
			pos += 1
		return result
	
	# Returns the minimum size of memory required to execute the compiled code.
	def min_mem_size(self):
		mx = 0
		current = 0
		for i in self.bf:
			if i == '>':
				current += 1
				if current > mx: mx += 1
			elif i == '<': current -= 1
		return mx + 1 - self.has_memory*(8 + 7*self.memory_address_size)

	# Repeats code x number of times: repeat(x;code)
	def func_repeat(self, values):
		return self.convert(values[1]*int(values[0]))

	# Move byte up to x distance
	# A<x>B
	def func_upb(self, values):
		return self.convert(f"[-{values[0]}>>+{values[0]}<<]")

	# B<x>A
	# Move byte down to x distance
	def func_downb(self, values):
		return self.convert(f"[-{values[0]}<<+{values[0]}>>]")

	# B = A
	# A<x>B.
	def func_copyb(self, values):
		return self.convert("[-x>>+>+<<x<]x>>>[-x<<<+x>>>]x<<<".replace('x', values[0]))
	
	# Moves a group of variables up
	# (A*x)<y>(B*x).
	def func_upbs(self, values):
		return self.convert(f"repeat({values[0]};upb({values[1]})>){values[0]}<")

	# Moves a group of variables down
	# (A*x)<y>(B*x).
	def func_downbs(self, values):
		return self.convert(f"repeat({values[0]};downb({values[1]})>){values[0]}<")

	# Copies a group of variables
	# (A*x)<y>(B*x).
	def func_copybs(self, values):
		return self.convert(f"repeat({values[0]};copyb({values[1]})>){values[0]}<")

	# A += B
	# AB
	def func_addb(self, values):
		return self.convert(">downb(0)<")

	# A -= B
	# AB
	def func_subb(self, values):
		return self.convert(">[-<->]<")

	# A *= B
	# AB..
	def func_multb(self, values):
		return self.convert(">[-<copyb(1)>]<[-]>>downb(1)<<")

	# A = A/B, B = A%B
	# AB...........
	def func_divb(self, values):
		return self.convert("[repeat(2;copyb(2)>)>lessb()ifel(5<upb(4)5>;3<+<copyb(4)<subb()6>downb(4)<)3<]>[-]>downb(1)3>downb(3)5<")

	# A != B
	# AB
	def func_diffb(self, values):
		return self.convert("subb()bool()")

	# A == B
	# AB
	def func_eqb(self, values):
		return self.convert("diffb()not()")

	# A < B
	# AB........
	def func_lessb(self, values):
		return self.convert("repeat(2;copyb(1)>)diffb()ifel(4<repeat(2;upb(3)>)4>+<<[->copyb(1)>->ifel(4<->+3>;6<[-]6>)3<]>>[-<[-]<+>>]<<downb(3);4<[-]>[-]3>)<<")

	# A > B
	# AB........
	def func_greatb(self, values):
		return self.convert("upb(1)repeat(2;>downb(0))<<lessb()")

	# A > 0
	# A.
	def func_bool(self, values):
		return self.convert("[[-]>+<]addb()")

	# not A
	# A.
	def func_not(self, values):
		return self.convert("bool()-[+>+<]addb()")

	# A && B
	# AB.
	def func_and(self, values):
		return self.convert(">bool()upb(0)<bool()>>downb(0)<<addb()>++<eqb()")

	# A || B
	# AB
	def func_or(self, values):
		return self.convert("addb()bool()")

	# If not A then execute code one, otherwise code 2
	# A.?
	def func_ifel(self, values):
		return self.convert(f"bool()copyb(0)[->>{values[0]}<<]>-[+<+>]<[->>{values[1]}<<]")
	
	# While values[0] (where that code gives represents a condition): execute values[1]
	# .. (because of the bool)
	def func_while(self, values):
		return self.convert(f"{values[0]}bool()[-{values[1]}{values[0]}bool()]")

	# For i in range(A): execute values[0] 
	# AIi? (where i is the variable you can edit)
	def func_forb(self, values):
		return self.convert(f"[->>{values[0]}<+copyb(0)<]>[-]>[-]<<")

	# Constructs a byte from binary data and puts it into A
	# A8.
	def func_bin8tobyte(self, values):
		return self.convert("[-8>128+8<]>[-7>64+7<]>[-6>32+6<]>[-5>16+5<]>[-4>8+4<]>[-3>4+3<]>[->>2+<<]>[->1+<]>downb(7)8<")

	# Constructs binary information from A
	# A8...........
	def func_bytetobin8(self, values):
		return self.convert(">128+<divb()>>64+<divb()>>32+<divb()>>16+<divb()>>8+<divb()>>4+<divb()>>2+<divb()6<")

	# Prints out the byte A
	# A............
	def func_printb(self, values):
		return self.convert(">100+<divb()[48+.[-]]addb()>10+<divb()[48+.[-]]addb()48+.[-]")

	# Prints out the binary information A8
	# A8.
	def func_printbin8(self, values):
		return self.convert("repeat(8;48+.[-]>)8<")

	# Prints TRUE or FALSE respectively
	# A..
	def func_printbool(self, values):
		return self.convert("ifel(84+.2-.3+.16-.[-];70+.5-.11+.7+.14-.[-])")

	# Prints a line change
	# .
	def func_endl(self, values):
		return self.convert("10+.[-]")

	# Gets boolean value of AX
	# AX
	def func_boolbinx(self, values):
		return self.convert(f"{int(values[0]) - 1}>repeat({int(values[0]) - 1};<or())")

	# Gets not value of AX
	# AX..
	def func_notbinx(self, values):
		return self.convert(f"{values[0]}>repeat({values[0]};<not()upb(0))>downbs(8;0)<")

	# AX and BX
	# AXBX.
	def func_andbinx(self, values):
		return self.convert(f"x>repeat(x;<upb({int(values[0]) - 1})x>>++<eqb()downb({int(values[0]) - 1})x<)".replace('x', values[0]))

	# AX or BX
	# AXBX.
	def func_orbinx(self, values):
		return self.convert(f"x>repeat(x;<upb({int(values[0]) - 1})x>bool()downb({int(values[0]) - 1})x<)".replace('x', values[0]))
	
	# AX += BX
	# AXBX.........
	def func_addbinx(self, values):
		x = int(values[0])
		x1 = x + 9
		return self.convert(f"{x}>repeat({x};<upb({x+3}){x}>upb({6})>ifel(>ifel(>ifel(9<+{x}<+{x1}>;9<+9>)<;>ifel(9<+9>;{x1}<+{x1}>)<)<;>ifel(>ifel(9<+9>;{x1}<+{x1}>)<;>ifel({x1}<+{x1}>;)<)<){x + 1}<){x}>[-]{x}<")

	# AX -= BX
	# AXBX.........
	def func_subbinx(self, values):
		x = int(values[0])
		x1 = x + 9
		return self.convert(f"{x}>repeat({x};<upb({x+3}){x}>upb({6})>ifel(>ifel(>ifel(9<+{x}<+{x1}>;)<;>ifel(9<+9>;9<+{x}<+{x1}>)<)<;>ifel(>ifel(;{x1}<+{x1}>)<;>ifel(9<+{x}<+{x1}>;)<)<){x + 1}<){x}>[-]{x}<")

	def func_multbinx(self, values):
		return self.convert("")
	
	def func_divbinx(self, values):
		return self.convert("")

	def func_diffbinx(self, values):
		p0 = int(values[0])
		return self.convert("")

	def func_eqbinx(self, values):
		return self.convert("")
	
	def func_lessbinx(self, values):
		return self.convert("")
	
	def func_greatbinx(self, values):
		return self.convert("")
	
	def func_forbinx(self, values):
		return self.convert("")

	def func_moveupb(self, values):
		return self.convert("[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[->]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]>]")
	
	def func_movedownb(self, values):
		return self.convert("[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-[-<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]<]")

	# Initiates memory system
	# First bit/byte is saved for memory travel outpost
	# Next values[0]*2 + 11 bits/bytes are the memory address size plus the space needed to use the address
	# Each value stored in memory has 3 extra spaces to permit copies plus position data
	# Each binx value stored in memory has a preceding values[0] bits*4 to indicate the size of the occupied chunk for algorithms such as malloc
	# values[1] determines the number of memory bit/byte cells
	def func_mem(self, values):
		self.memory_address_size = int(values[0])
		self.has_memory = True
		return self.convert(f"-{1 + int(values[0])*2 + 9 + int(values[1])*4}>")

	# Looks up to find a cell equal to 255
	def func_searchup255(self, values):
		if not self.has_memory: raise MemoryError("Memory was never initiated.")
		return self.convert(">+[->+]-")

	# Looks down to find a cell equal to 255
	def func_searchdown255(self, values):
		if not self.has_memory: raise MemoryError("Memory was never initiated.")
		return self.convert("<+[-<+]-")
	
	# Sends a boolean up from memory
	# (no idea how to format this stack descriptor)
	def func_sendboolup(self, values):
		if not self.has_memory: raise MemoryError("Memory was never initiated.")
		return self.convert("+3<copyb(0)>ifel(-searchup255()++>-searchdown255();-searchup255()+>-searchdown255())>>")

	# Sends a boolean down to memory (if positioning is loaded)
	# A..
	def func_sendbooldown(self, values):
		if not self.has_memory: raise MemoryError("Memory was never initiated.")
		return self.convert("ifel(-searchdown255()+3<[-]+<-4>searchup255()+;-searchdown255()+3<[-]<-4>searchup255()+)")

	# Sends a boolean down to the memory address section
	# A..
	def func_sendbooldownaddress(self, values):
		if not self.has_memory: raise MemoryError("Memory was never initiated.")
		return self.convert("ifel(-searchdown255()++<->searchup255()+;-searchdown255()+<->searchup255()+)")

	# Moves an address down to be loaded into the memory address
	# AY.. (y is the default memory address size)
	def func_writeaddress(self, values):
		if not self.has_memory: raise MemoryError("Memory was never initiated.")
		return self.convert(f"{self.memory_address_size}>-searchdown255()+{self.memory_address_size}>-searchup255()+repeat({self.memory_address_size};<sendbooldownaddress())")

	def func_sendboolmemdownaddress(self, values):
		if not self.has_memory: raise MemoryError("Memory was never initiated.")
		return self.convert("+3<copyb(0)>ifel(-searchdown255()++>-searchup255();-searchdown255()+>-searchup255())>>")

	# Adds current prefix in memory to address buffer
	# 0{self.memory_address_size}
	def func_addmemprefix(self, values):
		if not self.has_memory: raise MemoryError("Memory was never initiated.")
		return self.convert(f"searchdown255(){self.memory_address_size + 1}>-repeat({self.memory_address_size};movetonextmeminternal()sendboolmemdownaddress())searchdown255()+searchup255()repeat({self.memory_address_size};movetoprevmeminternal())")

	def func_movememprefix(self, values):
		if not self.has_memory: raise MemoryError("Memory was never initiated.")
		return self.convert(f"searchdown255()>-searchup255()repeat({self.memory_address_size};movetonextmeminternal()sendboolmemdownaddress())searchdown255()+searchup255()repeat({self.memory_address_size};movetoprevmeminternal())")

	# Uses the loaded pointer to find the respective position in memory
	#0
	def func_movetoaddress(self, values):
		if not self.has_memory: raise MemoryError("Memory was never initiated.")
		return self.convert(f"-searchdown255()>{self.memory_address_size}>{self.memory_address_size}>9>3>-searchdown255()while(>copybs({self.memory_address_size};{self.memory_address_size - 1}){self.memory_address_size}>boolbinx({self.memory_address_size});{self.memory_address_size - 1}>+searchdown255()>subbinx({self.memory_address_size})searchup255()movetonextmeminternal()searchdown255())searchup255()searchup255()+")

	# Move the memory pointer right
	#0
	def func_movetonextmeminternal(self, values):
		if not self.has_memory: raise MemoryError("Memory was never initiated.")
		return self.convert("+4>-")

	# Move the memory pointer left
	#0
	def func_movetoprevmeminternal(self, values):
		if not self.has_memory: raise MemoryError("Memory was never initiated.")
		return self.convert("+4<-")

	# Move the memory pointer right
	#0
	def func_movetonextmem(self, values):
		if not self.has_memory: raise MemoryError("Memory was never initiated.")
		return self.convert("-searchdown255()movetonextmeminternal()searchup255()+")

	# Move the memory pointer left
	#0
	def func_movetoprevmem(self, values):
		if not self.has_memory: raise MemoryError("Memory was never initiated.")
		return self.convert("-searchdown255()movetoprevmeminternal()searchup255()+")
	
	# Ends access to memory
	#0
	def func_endmemaccess(self, values):
		if not self.has_memory: raise MemoryError("Memory was never initiated.")
		return self.convert("-searchdown255()+searchup255()+")

	# Reads binx from address BY
	# max(BY, binx)
	def func_loadbinx(self, values):
		if not self.has_memory: raise MemoryError("Memory was never initiated.")
		return self.convert(f"writeaddress()movetoaddress()-searchdown255()repeat({self.memory_address_size + 1};movetonextmeminternal())repeat({values[0]};sendboolup()movetonextmeminternal())+searchup255()+{values[0]}<")
	
	# Saves AX to address BY
	# AXBY..
	def func_savebinx(self, values):
		if not self.has_memory: raise MemoryError("Memory was never initiated.")
		return self.convert(f"{values[0]}>writeaddress()movetoaddress()-searchdown255()repeat({int(values[0]) + self.memory_address_size};movetonextmeminternal())searchup255()+repeat({values[0]};<sendbooldown())endmemaccess()")

	# Occupies the first memory chunk with sufficient size. Most likely will crash if no more space is left if memory
	# .Y (ie, empty stack input for the placement of the pointer) (specify in the params the size that is required)
	def func_mallocbinx(self, values):
		if not self.has_memory: raise MemoryError("Memory was never initiated.")
		return self.convert("")
	
	# Frees the memory chunk
	# AY..
	def func_free(self, values):
		if not self.has_memory: raise MemoryError("Memory was never initiated.")
		return self.convert(f"writeaddress()movetoaddress()-searchdown255()movememprefix()repeat({self.memory_address_size - 1};movetonextmeminternal())4>-searchdown255()searchdown255()while(>copybs({self.memory_address_size};{self.memory_address_size - 1}){self.memory_address_size}>boolbinx({self.memory_address_size});{self.memory_address_size - 1}>+searchdown255()>subbinx({self.memory_address_size})2searchup255()movetonextmeminternal()3<[-]3>2searchdown255())2searchup255()+searchdown255()2movetonextmeminternal()repeat({self.memory_address_size + 1};movetoprevmeminternal()3<[-]3>)+searchup255()+")

if __name__ == "__main__":
	Interpreter(Converter(input())).run()