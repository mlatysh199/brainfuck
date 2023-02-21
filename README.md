# Brainfuck Compiler

The goal of this project is to develop a system that can convert simple C code to brainfuck using a pseudo-brainfuck that compiles to pure brainfuck.

The following points constitute the essential ideas behind the system:
* Functions: An effective way of organising data in memory is to use a stack. Stacks permit us to not have to worry about affecting data outside of the functions scope. A function in this stack accesses the last pieces of information and replaces them with the result of the execution.
* BinaryX: Due to the lack of registers or a separated memory tape, an efficient system requires certain memory landmarks to indicate the positioning of different sections. Because of this, not all of the 255 values available to each cell can be employed. Thus, data is saved as binary, setting each normal cell to 0 or to 1 (ie, all cells that do not function as landmarks or as io spaces). Ideally, we could create more efficient algorithms to be able to employ 64 values in each normal cell instead of 2. That is to say, all data could be saved in base 64. Or to an incredible extreme, base 254. Nevertheless, since brainfuck does not have internal binary manipulation commands. Because of this, saving data as binary makes the systems code much easier to associate to actual computers.
* Memory: Using landmarks, we can define a memory system. The first cell is set to 255 to indicate the start of the tape. The next cells are saved to manage addresses. After that, cells are dedicated for the memory itself (4 x number of bits), and finally the stack. +[->+]- and +[-<+]- describe gliders that search for the value 255 in memory by going up and down, respectively. This allows us to move between landmarks without losing our current position in the stack. When memory operations start, two 255 landmarks are added: one in the memory, to indicate the current bit; another in the stack, to indicate the place to return to after the memory command has been executed.

These three points permit the creation of an understandable program. Nevertheless, by making the program easier to conceptually understand, the code becomes much more inefficient in terms of brainfuck. This is why a lot of brainfuck programs avoid generalization.

What's left to do:
* Fix bugs ;(
* Finish memory access system
* Finish binx basic operations
* Add a variable management system to the converter
* Create some kind of test game
