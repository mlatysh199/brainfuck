import sys, MacrofuckCompiler

# Runs brainfuck code
class Interpreter:
	def __init__(self, code : str, debug : bool=False, size : int=None):
		self.compiler = MacrofuckCompiler.Compiler(code)
		if not size: size = self.compiler.min_mem_size
		elif size < self.compiler.min_mem_size: raise IndexError(f"This program requires at least {self.compiler.min_mem_size} units of memory.")
		self.debug = debug
		self.code = self.compiler.get_bf()
		self.stack_trace_data = self.compiler.get_stack_trace_data()
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
	def __debug(self, ins : str):
		result = ""
		mem_text = list('  ' + '  '.join([str(i).rjust(3) for i in self.mem]) + '  ')
		mem_text[5 + self.ptr*5] = '#'
		if self.pc in self.stack_trace_data[0] and (ins != '[' or len(self.stack_trace) < len(self.stack_trace_data[0][self.pc]) or self.stack_trace[-len(self.stack_trace_data[0][self.pc]):] != self.stack_trace_data[0][self.pc]):
			result += "DEBUG: " + " > ".join(self.stack_trace) + ' '
			self.stack_trace += self.stack_trace_data[0][self.pc]
			result += ">>> " + " > ".join(self.stack_trace_data[0][self.pc]) + '\n'
		if self.pc in self.stack_trace_data[1] and (ins != ']' or not self.mem[self.ptr]):
			for _ in range(len(self.stack_trace_data[1][self.pc])): self.stack_trace.pop()
			result += "DEBUG: " + " > ".join(self.stack_trace) + " <<< " + " < ".join(self.stack_trace_data[1][self.pc]) + '\n'
		result += f"DEBUG: {str(self.pc).rjust(4)} {ins} {str(self.ptr).rjust(3)}  [{''.join(mem_text)}]"
		return result

	# Main runner system
	def run(self, interactive : bool=False, in_tape : str=""):
		length = len(self.code)
		result = ""
		if self.pc >= length: raise IndexError("The whole program has been executed. Execute Interpreter.reset to be able to restart the program.")
		while self.pc < length:
			ins = self.code[self.pc]
			if self.debug: print(self.__debug(ins))
			if ins == '<': self.ptr -= 1
			elif ins == '>': self.ptr += 1
			elif ins == '-': self.mem[self.ptr] = (self.mem[self.ptr] - 1)&255
			elif ins == '+': self.mem[self.ptr] = (self.mem[self.ptr] + 1)&255
			elif ins == '.':
				result += chr(self.mem[self.ptr])
				if interactive: print(chr(self.mem[self.ptr]), end='')
			elif ins == ',':
				char = ''
				if not interactive:
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
			if self.ptr < 0 or self.ptr >= self.size: raise MemoryError("Pointer exceeded designated memory: "+ " > ".join(self.stack_trace))
			self.pc += 1
		if self.debug: print(self.__debug(' '))
		return result

if __name__ == "__main__":
	Interpreter("0repeat(>)implant(8;53)0repeat(<)0repeat(>)copybinx(8;7)0repeat(<)8repeat(>)printbinx(8)8repeat(<)").run(True)