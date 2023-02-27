# Brainfuck Compiler

The goal of this project is to develop a system that can convert simple C code to brainfuck using a pseudo-brainfuck that compiles to pure brainfuck.

## Points that constitute the essential ideas behind the system

* Pseudo-functions: An effective way of organizing data in memory is to use a stack. Stacks permit us to not have to worry about affecting data outside of the pseudo-functions scope. A pseudo-function in this stack accesses the last pieces of information and replaces them with the result of the execution. Additionally, I call these pseudo-functions since they function more like assembly macros. To implement true functions, we would need to be able to directly access and (possibly) manipulate the code. Therefore, a brainfuck interpreter written in brainfuck is actually not such a bad idea since one could write the code to the memory, read it, and maybe modify it, thus permitting the existence of more complicated jump structures rather tha just '[' and ']'.
* BinaryX: Due to the lack of registers or a separated memory tape, an efficient system requires certain memory landmarks to indicate the positioning of different sections. Because of this, not all of the 255 values available to each cell can be employed. Thus, data is saved as binary, setting each normal cell to 0 or to 1 (ie, all cells that do not function as landmarks or as io spaces). Ideally, we could create more efficient algorithms to be able to employ 64 values in each normal cell instead of 2. That is to say, all data could be saved in base 64. Or to an incredible extreme, base 254. Nevertheless, since brainfuck does not have internal binary manipulation commands. Because of this, saving data as binary makes the systems code much easier to associate to actual computers.
* Memory: Using landmarks, we can define a memory system. The first cell is set to 255 to indicate the start of the tape. The next cells are saved to manage addresses. After that, cells are dedicated for the memory itself (4 x number of bits), and finally the stack. +[->+]- and +[-<+]- describe gliders that search for the value 255 in memory by going up and down, respectively. This allows us to move between landmarks without losing our current position in the stack. When memory operations start, two 255 landmarks are added: one in the memory, to indicate the current bit; another in the stack, to indicate the place to return to after the memory command has been executed.

These three points permit the creation of an understandable program. Nevertheless, by making the program easier to conceptually understand, the code becomes much more inefficient in terms of brainfuck. This is why a lot of brainfuck programs avoid generalization.

## Limitations

* Without a brainfuck interpreter inside of the brainfuck code, there can be no true functions, only macros.
* No stack address system. While it is possible to implement using a similar paradigm to the way the base memory access system is structured, I think it is not work the effort to rewrite the whole stack system to be even more inefficient. In any case, the basic effects of transfering stack pointer information to pseudo-functions could be simulated by saving the data in the memory beforehand and providing the macro with the pointer in memory.
* No memory safety. That is to say, if you request too much memory the system behavior becomes undefined.

## What's left to do

* Fix bugs ;(
* Finish memory access system.
* Finish binx basic operations.
* Add a variable management system to the converter.
* Create some kind of test game/"complicated" program.
* Create a pseudo-brainfuck interpreter inside of brainfuck.
