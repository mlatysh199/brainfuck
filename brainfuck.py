def interpreter(size, code, in_tape="", stack_trace_data=dict()):
	ptr = 0
	in_tape_pos = 0
	mem = [0]*size
	length = len(code)
	pc = 0
	return_stack = []
	result = ""
	stack_trace = ["start"]
	while pc < length:
		ins = code[pc]
		if ins == '<': ptr -= 1
		elif ins == '>': ptr += 1
		elif ins == '-': mem[ptr] = (mem[ptr] - 1)&255
		elif ins == '+': mem[ptr] = (mem[ptr] + 1)&255
		elif ins == '.':
			result += chr(mem[ptr])
			if not in_tape: print(chr(mem[ptr]), end='')
		elif ins == ',':
			char = ''
			if in_tape:
				char = in_tape[in_tape_pos]
				in_tape_pos += 1
			else: char = input()[0]
			mem[ptr] = ord(char)&255
		elif ins == '[':
			return_stack.append(pc)
			if not mem[ptr]:
				brks = 1
				while brks:
					pc += 1
					brks = brks + (code[pc] == '[') - (code[pc] == ']')
				pc -= 1
		elif ins == ']':
			ret = return_stack.pop()
			if mem[ptr]: pc = ret - 1
		if stack_trace_data:
			mem_text = list('  ' + '  '.join([str(i).rjust(3) for i in mem]) + '  ')
			mem_text[5 + ptr*5] = '#'
			print("DEBUG:", str(pc).rjust(4), ins, str(ptr).rjust(3), '[' + ''.join(mem_text) + "]")
			if pc in stack_trace_data:
				print("DEBUG:", " > ".join(stack_trace), end=" ")
				if stack_trace and stack_trace_data[pc][-1] == stack_trace[-1]:
					print("<<<")
					for _ in range(len(stack_trace_data[pc])): stack_trace.pop()
				else:
					stack_trace += stack_trace_data[pc]
					print(">>> " + " > ".join(stack_trace_data[pc]))
		pc += 1
	return result

# TODO
import traceback

class Converter:
	def __init__(self, code):
		self.functions = {"repeat(" : self.func_repeat,
			"upb(" : self.func_upb,
			"downb(" : self.func_downb,
			"copyb(" : self.func_copyb,
			"addb(" : self.func_addb,
			"subb(" : self.func_subb,
			"multb(" : self.func_multb,
			"divb(" : self.func_divb,
			"diffb(" : self.func_diffb,
			"eqb(" : self.func_eqb,
			"lessb(" : self.func_lessb,
			"greatb(" : self.func_greatb,
			"bool(" : self.func_bool,
			"not(" : self.func_not,
			"and(" : self.func_and,
			"or(" : self.func_or,
			"ifel(" : self.func_ifel,
			"bin8tobyte(" : self.func_bin8tobyte,
			"bytetobin8(" : self.func_bytetobin8,
			"upbin8(" : self.func_upbin8,
			"downbin8(" : self.func_downbin8,
			"copybin8(" : self.func_copybin8,
			"notbin8(" : self.func_notbin8,
			"andbin8(" : self.func_andbin8,
			"orbin8(" : self.func_orbin8,
			"addbin8c(" : self.func_addbin8c,
			"addbin8(" : self.func_addbin8,
			"subbin8c(" : self.func_subbin8c,
			"subbin8(" : self.func_subbin8,
			"printb(" : self.func_printb,
			"printbin8(" : self.func_printbin8,
			"endl(" : self.func_endl}
		self.commands = ['<', '>', '-', '+', '.', ',', '[', ']']
		self.skip = [' ', '\n', '\t']
		self.numbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
		self.pc = 0
		self.stack_trace_data = dict()
		self.bf = self.convert(code)
		print(self.stack_trace_data)

	def get_bf(self):
		return self.bf

	def get_stack_trace_data(self):
		return self.stack_trace_data

	def convert(self, code):
		result = ""
		pos = 0
		number = 0
		number_mode = False
		while pos < len(code):
			if code[pos] in self.commands:
				result += code[pos]*(number + (number == 0 and not number_mode))
				number = 0
				self.pc += (number + (number == 0 and not number_mode))
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
				if self.pc not in self.stack_trace_data:
					self.stack_trace_data[self.pc] = []
				self.stack_trace_data[self.pc].append(function[:-1])
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
				result += self.functions[function](params)*(number + (number == 0 and not number_mode))
				if self.pc not in self.stack_trace_data:
					self.stack_trace_data[self.pc] = []
				self.stack_trace_data[self.pc].insert(0, function[:-1])
			if code[pos] not in self.numbers: number_mode = False
			pos += 1
		return result
	
	# Repeats code x number of times: repeat(x;code)
	def func_repeat(self, values):
		return self.convert(values[1]*int(values[0]))

	# Move byte up to x distance
	# A<x>B
	def func_upb(self, values):
		return self.convert("[-x>>+x<<]".replace('x', values[0]))

	# B<x>A
	# Move byte down to x distance
	def func_downb(self, values):
		return self.convert("[-x<<+x>>]".replace('x', values[0]))

	# B = A
	# A<x>B..
	def func_copyb(self, values):
		return self.convert("[-x>>+>+<<x<]x>>>[-x<<<+x>>>]x<<<".replace('x', values[0]))

	# A += B
	# AB
	def func_addb(self, values):
		return self.convert(">downb(0)<")

	# A -= B
	# AB
	def func_subb(self, values):
		return self.convert(">[-<->]<")

	# A *= B
	# AB...
	def func_multb(self, values):
		return self.convert(">[-<copyb(1)>]<[-]>>downb(1)<<")

	# A = A/B, B = A%B
	# AB.........
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
		return self.convert("repeat(2;copyb(1)>)diffb()ifel(4<upb(3)>upb(3)3>lessb()not()downb(3);4<[-]>[-]3>)<<")

	# A > 0
	# A.
	def func_bool(self, values):
		#[print(i.strip()) for i in traceback.format_stack()]
		return self.convert("[[-]>+<]addb()")

	# not A
	# A.
	def func_not(self, values):
		return self.convert("bool()-[+>+<]addb()")

	# A && B
	# AB
	def func_and(self, values):
		return self.convert("repeat(2;bool()>)<<addb()>++<eqb()")

	# A || B
	# AB
	def func_or(self, values):
		return self.convert("addb()bool()")

	# If not cond the execute code one, otherwise code 2
	# ?..
	def func_ifel(self, values):
		return self.convert(f"bool()copyb(0)[->>{values[0]}<<]>-[+<+>]<[->>{values[1]}<<]")

	# Constructs a byte from binary data and puts it into A
	# ABCDEFGH.....
	def func_bin8tobyte(self, values):
		return self.convert("[-8>128+8<]>[-7>64+7<]>[-6>32+6<]>[-5>16+5<]>[-4>8+4<]>[-3>4+3<]>[->>2+<<]>[->1+<]>downb(7)8<")

	# Constructs binary information from A
	# ABCDEFGH.......
	def func_bytetobin8(self, values):
		return self.convert(">128+<divb()>>64+<divb()>>32+<divb()>>16+<divb()>>8+<divb()>>4+<divb()>>2+<divb()6<")

	# Moves binary information up
	# ABCDEFGH<x>........
	def func_upbin8(self, values):
		return self.convert(f"repeat(8;upb({values[0]}>)8<)")

	# Moves binary information down
	# ........<x>ABCDEFGH
	def func_downbin8(self, values):
		return self.convert(f"repeat(8;downb({values[0]}>)8<)")

	# Copies binary information
	# ABCDEFGH<x>..........
	def func_copybin8(self, values):
		return self.convert(f"repeat(8;copyb({values[0]}>)8<)")

	# Negates an 8 bit value
	def func_notbin8(self, values):
		return self.convert("repeat(8;not()>)8<")

	# A8 &= B8
	# A8B8..
	def func_andbin8(self, values):
		return self.convert("upb(15)8>upb(8)8>and()downbb(15)15<upb(14)8>upb(7)7>and()downb(14)14<upb(13)8>upb(6)6>and()downb(13)13<upb(12)8>upb(5)5>and()downb(12)12<upb(11)8>upb(4)4>and()downb(11)11<upb(10)8>upb(3)3>and()downb(10)10<upb(9)8>upb(2)2>and()downb(9)9<upb(8)8>upb(1)>and()downb(8)16<")

	# A8 |= B8
	# A8B8..
	def func_orbin8(self, values):
		return self.convert("upb(15)8>upb(8)8>or()downb(15)15<upb(14)8>upb(7)7>or()downb(14)14<upb(13)8>upb(6)6>or()downb(13)13<upb(12)8>upb(5)5>or()downb(12)12<upb(11)8>upb(4)4>or()downb(11)11<upb(10)8>upb(3)3>or()downb(10)10<upb(9)8>upb(2)2>or()downb(9)9<upb(8)8>upb(1)>or()downb(8)16<")

	# A8 += B8
	# A8B8..........
	def func_addbin8c(self, values):
		return self.convert("8>repeat(8;<upb(12)8>upb(8)>ifel(>>ifel(>>ifel(19<+8>+11>;11<+11>)<<;>>ifel(11<+11>;19<+19>)<<)<<;>>ifel(>>ifel(11<+11>;19<+19>)<<;>>ifel(19<+19>;)<<)<<)9<)")

	# A8 += B8 (remove carry bit)
	# A8B8..........
	def func_addbin8(self, values):
		return self.func_addbin8c(values) + self.convert("8>[-]8<")

	# A8 -= B8 
	# A8B8..........
	def func_subbin8c(self, values):
		return self.convert("8>repeat(8;<upb(12)8>upb(8)>ifel(>>ifel(>>ifel(19<+8>+11>;)<<;>>ifel(11<+11>;19<+8>+11>)<<)<<;>>ifel(>>ifel(;19<+19>)<<;>>ifel(19<+8>+11>;)<<)<<)9<)")

	# A8 - B8 (remove carry bit)
	# A8B8..........
	def func_subbin8(self, values):
		return self.func_subbin8c(values) + self.convert("8>[-]8<")

	# Prints out the byte A
	# A........
	def func_printb(self, values):
		return self.convert(">100+<divb()48+.[-]addb()>10+<divb()48+.[-]addb()48+.[-]")

	# Prints out the binary information A8
	# A8
	def func_printbin8(self, values):
		return self.convert("repeat(8;48+.[-]>)8<")

	# Prints a line change
	# .
	def func_endl(self, values):
		return self.convert("10+.[-]")

if __name__ == "__main__":
	interpreter(int(input()), Converter(input()).get_bf())
