from enum import Enum
import EBNF
import VirtualParser as VP
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
    operators = [
        "not",
        "~",
        "**",
        "*",
        "/",
        "+",
        "-",
        "<<",
        ">>",
        "&",
        "|",
        "^",
        "==",
        "and",
        "or",
        "<",
        ">",
        "<=",
        ">=",
    ]
    types = ["num"]

    def __init__(self, stream, cache=False) -> None:
        self.stream = stream
        self.pos = 0
        self.do_cache = cache
        self.cache: dict[int, tuple[int, VP.Token]] = dict()

    # Consumes comments
    def process_comment(self) -> None:
        while (
            self.pos < len(self.stream)
            and self.stream[self.pos] not in self.comment_break_chars
        ):
            self.pos += 1
        self.pos += 1

    # Processes words
    def process_word(self) -> VP.Token:
        word = ""
        while self.pos < len(self.stream) and (
            self.stream[self.pos] in self.word_chars
            or self.stream[self.pos] in self.number_chars
        ):
            word += self.stream[self.pos]
            self.pos += 1
        if word in self.commands:
            return VP.Token(TokenType.Command, word)
        elif word in self.operators:
            return VP.Token(TokenType.Operator, word)
        elif word in self.types:
            return VP.Token(TokenType.Type, word)
        return VP.Token(TokenType.Word, word)

    # Processes numbers
    def process_number(self) -> VP.Token:
        number = 0
        while (
            self.pos < len(self.stream) and self.stream[self.pos] in self.number_chars
        ):
            number *= 10
            number += ord(self.stream[self.pos]) - ord("0")
            self.pos += 1
        if self.pos < len(self.stream) and self.stream[self.pos] in self.decimal_chars:
            decimal = 1.0
            self.pos += 1
            while (
                self.pos < len(self.stream)
                and self.stream[self.pos] in self.number_chars
            ):
                decimal /= 10
                number += decimal * (ord(self.stream[self.pos]) - ord("0"))
                self.pos += 1
        return VP.Token(TokenType.Number, str(number))

    # Processes operators
    def process_operators(self) -> VP.Token:
        operator = self.stream[self.pos]
        self.pos += 1
        while (
            self.pos < len(self.stream)
            and self.stream[self.pos] in self.operator_chars
            and operator + self.stream[self.pos] in self.operators
        ):
            operator += self.stream[self.pos]
            self.pos += 1
        if operator not in self.operators:
            if operator in self.commands:
                return VP.Token(TokenType.Command, operator)
        return VP.Token(TokenType.Operator, operator)

    # Gets the next token
    def next_token(self) -> VP.Token:
        start_pos = self.pos
        if not self.do_cache or self.pos not in self.cache:
            if self.pos >= len(self.stream):
                self.cache[start_pos] = (self.pos, VP.Token(TokenType.EOF, None))
            else:
                char = self.stream[self.pos]
                while True:
                    if char in self.ignore_chars:
                        self.pos += 1
                    elif char in self.comment_chars:
                        self.process_comment()
                    else:
                        break
                    if self.pos >= len(self.stream):
                        self.cache[start_pos] = (
                            self.pos,
                            VP.Token(TokenType.EOF, None),
                        )
                        break
                    char = self.stream[self.pos]
                if self.pos not in self.cache:
                    if char in self.word_chars:
                        r = self.process_word()
                        self.cache[start_pos] = (self.pos, r)
                    elif char in self.number_chars:
                        r = self.process_number()
                        self.cache[start_pos] = (self.pos, r)
                    elif char in self.operator_chars:
                        r = self.process_operators()
                        self.cache[start_pos] = (self.pos, r)
                    else:
                        self.pos += 1
                        if char in self.bracket_chars:
                            self.cache[start_pos] = (
                                self.pos,
                                VP.Token(TokenType.Bracket, char),
                            )
                        elif char in self.brace_chars:
                            self.cache[start_pos] = (
                                self.pos,
                                VP.Token(TokenType.Brace, char),
                            )
                        elif char in self.break_chars:
                            self.cache[start_pos] = (
                                self.pos,
                                VP.Token(TokenType.Breaker, None),
                            )
                        elif char in self.separator_chars:
                            self.cache[start_pos] = (
                                self.pos,
                                VP.Token(TokenType.Separator, None),
                            )
                        elif char in self.parenthesis_chars:
                            self.cache[start_pos] = (
                                self.pos,
                                VP.Token(TokenType.Parenthesis, char),
                            )
                        else:
                            raise KeyError(f"{char} is not a valid character.")
        self.pos = self.cache[start_pos][0]
        return self.cache[start_pos][1]

    def get_position(self) -> int:
        return self.pos

    def set_position(self, pos: int) -> None:
        self.pos = pos


class Parser:
    terminal_dict = {
        VP.Token(EBNF.TokenType.Terminal, "fuck"): VP.Token(TokenType.Command, "fuck"),
        VP.Token(EBNF.TokenType.Terminal, "="): VP.Token(TokenType.Command, "="),
        VP.Token(EBNF.TokenType.Terminal, "("): VP.Token(TokenType.Parenthesis, "("),
        VP.Token(EBNF.TokenType.Terminal, ")"): VP.Token(TokenType.Parenthesis, ")"),
        VP.Token(EBNF.TokenType.Terminal, "["): VP.Token(TokenType.Bracket, "["),
        VP.Token(EBNF.TokenType.Terminal, "]"): VP.Token(TokenType.Bracket, "]"),
        VP.Token(EBNF.TokenType.Terminal, "{"): VP.Token(TokenType.Brace, "{"),
        VP.Token(EBNF.TokenType.Terminal, "}"): VP.Token(TokenType.Brace, "}"),
        VP.Token(EBNF.TokenType.Terminal, "num"): VP.Token(TokenType.Type, "num"),
    }
    rule_dict = {
        "string": TokenType.Word,
        "const": TokenType.Number,
        "separator": TokenType.Separator,
        "breaker": TokenType.Breaker,
        "const_op": TokenType.Operator,
        "u_const_op": TokenType.Operator,
    }
    terminal_set = {
        VP.Token(TokenType.Command, "fuck"),
        VP.Token(TokenType.Command, "="),
        TokenType.Bracket,
        TokenType.Brace,
        TokenType.Parenthesis,
        TokenType.Breaker,
        TokenType.Parenthesis,
    }
    rule_set = {}

    grammar = None
    with open("Varfuck.ebnf", "r") as f:
        p = EBNF.Parser(f.read())
        grammar = p.build_if()

    def __init__(self, data: str) -> None:
        self.lexer = Lexer(data)
        self.parser = VP.Parser(
            Parser.grammar,
            self.lexer,
            Parser.terminal_dict,
            Parser.rule_dict,
            Parser.terminal_set,
            Parser.rule_set,
        )

    def parse(self) -> VP.ASTNode:
        result = self.parser.parse()
        if (
            len(result) == 0
            or type(result[0]) != VP.ASTNode
            or result[0].rule != "grammar"
        ):
            raise SyntaxError(
                "Not a grammar based AST."
            )  # TODO replace with correct error
        return result[0]


class ASTNode:
    def __init__(self, name: str, data: list[Union["ASTNode", VP.Token]]) -> None:
        self.name = name
        self.data = data


class Cleaner:
    def __init__(self, tree: VP.ASTNode) -> None:
        if tree.rule != "grammar":
            raise SyntaxError(
                "Not a grammar based AST."
            )  # TODO replace with correct error
        self.tree = tree

    def __correct_const_expr(self, node: VP.ASTNode | VP.Token) -> ASTNode | VP.Token:
        if type(node) == VP.Token:
            return node
        if node.rule == "const_expr_p":
            if len(node.children) == 0:
                return ASTNode("temp", [])
            return ASTNode(
                "temp", [self.__correct_const_expr(i) for i in node.children]
            )
        back = self.__correct_const_expr(node.children[-1]).data
        if len(back) == 0:
            return ASTNode(
                "const_expr", [self.__correct_const_expr(i) for i in node.children[:-1]]
            )
        # Not as dynamic as I would like it to be, but we got to start hardcoding in some parts at some point
        return ASTNode(
            "const_expr",
            [
                ASTNode(
                    "const_expr",
                    [self.__correct_const_expr(i) for i in node.children[:-1]],
                ),
                back[0],
                back[1],
            ],
        )

    def __clean(self, node: VP.ASTNode | VP.Token) -> ASTNode | VP.Token:
        if type(node) == VP.Token:
            return node
        if node.rule == "const_expr":
            return self.__correct_const_expr(node)
        return ASTNode(node.rule, [self.__clean(i) for i in node.children])

    def clean(self) -> ASTNode:
        return self.__clean(self.tree)


class ConstRef:
    def __init__(self, name: str) -> None:
        self.name = name

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.name


class ConstExpr:
    # math expressions
    def __init__(self, data: list[str | ConstRef], force_nnint=False) -> None:
        self.refs = {ref.name for ref in data if type(ref) == ConstRef}
        import math

        self.data: list[str | ConstRef] = (
            [str(eval(" ".join(data)))] if not len(self.refs) else data
        )
        self.force_nnint = force_nnint
        self.done = not len(self.refs)

    def __builder(base: ASTNode) -> list[str | ConstRef]:
        data = base.data
        # Once again, boring hardcoding
        if type(data[0]) == VP.Token:
            if data[0].type == TokenType.Number:
                return [data[0].value]
            if data[0].type == TokenType.Operator:
                return [data[0].value] + ConstExpr.__builder(data[1])
            if len(data) == 1:
                return [ConstRef(data[0].value)]
            return ["math.", data[0].value, "("] + ConstExpr.__builder(data[1]) + [")"]
        if len(data) == 1:
            return ["("] + ConstExpr.__builder(data[0]) + [")"]
        return (
            ConstExpr.__builder(data[0])
            + [data[1].value]
            + ConstExpr.__builder(data[2])
        )

    def builder(base: ASTNode) -> "ConstExpr":
        return ConstExpr(ConstExpr.__builder(base))

    def replace(self, name: str, expr: "ConstExpr") -> "ConstExpr":
        if name not in self.refs:
            return ConstExpr(self.data.copy(), self.force_nnint)
        cp = []
        for i in self.data:
            if type(i) == str or i.name != name:
                cp.append(i)
            else:
                cp.extend(expr.data)
        return ConstExpr(cp, self.force_nnint)

    def __add__(self, other: object) -> "ConstExpr":
        if type(other) != ConstExpr:
            raise TypeError(f"Cannot add ConstExpr with {type(other)}.")
        return ConstExpr(
            other.data + ["+"] + self.data, self.force_nnint or other.force_nnint
        )

    def __sub__(self, other: object) -> "ConstExpr":
        if type(other) != ConstExpr:
            raise TypeError(f"Cannot sub ConstExpr with {type(other)}.")
        return ConstExpr(
            self.data + ["-("] + other.data + [")"],
            self.force_nnint or other.force_nnint,
        )

    def __str__(self) -> str:
        if len(self.refs):
            raise ValueError(f"ConstExpr hasn't been fully built ({self.data}).")
        if self.force_nnint:
            e = eval(self.data[0])
            if int(e) != e or e < 0:
                raise ValueError(f"ConstExpr's forced NNINT, instead got {e}.")
        return self.data[0]

    def __repr__(self) -> str:
        return "(" + repr(self.data) + " : " + str(self.force_nnint) + ")"

    def __eq__(self, __value: object) -> bool:
        if type(__value) != ConstExpr:
            raise TypeError(f"Cannot compare ConstExpr with {type(__value)}.")
        return self.data == __value.data


class BinX:
    def __init__(self, name: str | None, size: ConstExpr) -> None:
        self.name = name if name != "" else None
        self.size = ConstExpr(size.data, True)


class BinXManager:
    def __init__(self, data: list[BinX], ret: list[ConstExpr]) -> None:
        self.ret = ret
        self.params = data
        self.size = ConstExpr(["0"], True)
        self.call_stack: list[ConstExpr] = []
        self.var_stack: list[list[str]] = []
        self.pos_table: dict[str, ConstExpr] = dict()
        self.size_table: dict[str, ConstExpr] = dict()
        self.order_table: dict[str, int] = dict()
        self.add_section()
        self.vcount = 0
        for i in data:
            self.add_var(i)
            self.size += i.size
        self.ret_pos = self.size
        self.ret_size = ConstExpr(["0"], True)
        for i in range(len(self.ret)):
            self.add_var(BinX(str(i), ret[i]), False)
            self.size += ret[i]
            self.ret_size += ret[i]
        self.code: list[str | ConstExpr | MacroInvocation] = []
        self.pos = self.var_stack[-1][0] if len(self.var_stack[-1]) else None

    def add(self, data: Union[str, ConstExpr, "MacroInvocation"]) -> None:
        self.code.append(data)

    def goto(self, pos: str | None | ConstExpr) -> None:
        if pos != None and pos not in self.pos_table:
            raise NameError(f"No such variable defined as {pos}.")
        if pos == self.pos:
            return
        a = self.pos_table[self.pos] if self.pos != None else self.size
        b = self.pos_table[pos] if pos != None else self.size
        if self.pos == None or (
            (not (pos == None)) and self.order_table[pos] < self.order_table[self.pos]
        ):
            # go right
            self.add(a - b)
            self.add("<")
        else:
            # go left
            self.add(b - a)
            self.add(">")
        self.pos = pos

    def add_section(self) -> None:
        self.call_stack.append(self.size)
        self.var_stack.append([])

    def pop_section(self) -> None:
        self.goto(None)
        dif = self.size - self.call_stack[-1]
        self.add(dif)
        self.add("repeat(<[-])")
        self.size = self.call_stack.pop()
        for i in self.var_stack.pop():
            self.del_var(i)

    def add_var(self, var: BinX, include=True) -> None:
        if var.name == None:
            raise NameError("Variable names must be complete.")
        if var.name in self.pos_table:
            raise NameError("Variable names must be non repeating.")
        self.size_table[var.name] = var.size
        self.pos_table[var.name] = self.size
        self.order_table[var.name] = self.vcount
        self.vcount += 1
        if include:
            self.var_stack[-1].append(var.name)

    def del_var(self, name: str) -> None:
        self.pos_table.pop(name)
        self.size_table.pop(name)
        self.order_table.pop(name)
        self.vcount -= 1

    def clear_var(self, name: str) -> None:
        self.goto(name)
        self.add(self.size_table[name])
        self.add("repeat([-]>)")
        self.add(self.size_table[name])
        self.add("<")

    # Copy up
    def load_var(self, name: str) -> None:
        self.goto(name)
        dif = self.size - self.pos_table[name] - ConstExpr(["1"])
        self.add("copybinx(")
        self.add(self.size_table[name])
        self.add(";")
        self.add(dif)
        self.add(")")

    # Move down
    def push_var(self, name: str) -> None:
        self.goto(None)
        dif = self.size - self.pos_table[name] - ConstExpr(["1"])
        self.add("downbinx(")
        self.add(self.size_table[name])
        self.add(";")
        self.add(dif)
        self.add(")")

    def clear_size(self, size: ConstExpr) -> None:
        self.add(size)
        self.add("repeat([-]>)")
        self.add(size)
        self.add("<")

    def goup(self, size: ConstExpr) -> None:
        self.add(size)
        self.add(">")

    def do_call(
        self,
        mac: "MacroInvocation",
        param_data: list[str | None],
        params: list[ConstExpr],
        ret_data: list[str | None],
        ret: list[ConstExpr],
    ) -> None:
        base = self.size
        if len(param_data) != len(params):
            raise TypeError(
                f"Expected {len(params)} parameters but got {len(param_data)}."
            )
        comp_param = []
        for i in range(len(param_data)):
            if param_data[i] != None:
                self.load_var(param_data[i])
                comp_param.append(self.size_table[param_data[i]])
            else:
                comp_param.append(params[i])
            self.size += params[i]
        mac.set_v_params(comp_param)
        self.size = base
        self.goto(None)
        self.add(mac)
        if len(ret_data) != len(ret):
            raise TypeError(
                f"Expected {len(ret)} return parameters but got {len(ret_data)}."
            )
        comp_ret = []
        for i in range(len(ret)):
            if ret_data[i] != None:
                if ret_data[i] in self.order_table:
                    self.clear_var(ret_data[i])
                    self.push_var(ret_data[i])
                else:
                    self.add_var(BinX(ret_data[i], ret[i]))
                comp_ret.append(self.size_table[ret_data[i]])
            else:
                comp_ret.append(ret[i])
                self.clear_size(ret[i])
            self.size += ret[i]
            self.goup(ret[i])
        mac.set_ret(comp_ret)

    def fuck(self, data: list[str]) -> None:
        if len(data) == 0:
            return
        for i in range(len(data)):
            if data[i] == None:
                continue
            self.load_var(data[i])
            self.clear_var(str(i))
            self.goto(None)
            self.push_var(str(i))

    def end(self) -> None:
        if len(self.var_stack) != 1:
            raise OverflowError(
                f"Can't end macro while stack is not sufficiently empty."
            )
        # This should bring the stack pointer all the way down to 0
        rev = self.var_stack.pop()
        for i in range(len(rev) - 1, -1, -1):
            self.clear_var(rev[i])
            if i:
                self.goto(rev[i - 1])
            else:
                self.goto(None)
            self.del_var(rev[i])
        if not len(self.params):
            return
        self.add(self.size)
        self.add("<")
        dif = self.ret_pos - ConstExpr(["1"])
        self.add(self.ret_pos)
        self.add(">")
        self.add("downbinx(")
        self.add(self.ret_size)
        self.add(";")
        self.add(dif)
        self.add(")")
        self.add(self.ret_pos)
        self.add("<")

    def start_repeat(self, num: ConstExpr) -> None:
        self.add(num)
        self.add("repeat(")

    def end_repeat(self) -> None:
        self.add(")")

    def start_while(self, name: str) -> None:
        self.add("while(")
        self.load_var(name)
        self.goto(None)
        self.add("boolbinx(")
        self.add(self.size_table[name])
        self.add(")")
        self.add(";")
        self.add_section()
        self.size += ConstExpr(["2"]) + self.size_table[name]
        self.goup(ConstExpr(["2"]) + self.size_table[name])

    def end_while(self) -> None:
        self.pop_section()
        self.goto(None)
        self.add(")")

    def start_if(self, name: str) -> None:
        self.add_section()
        self.load_var(name)
        self.goto(None)
        self.size += ConstExpr("2")
        self.add_section()
        self.add("boolbinx(")
        self.add(self.size_table[name])
        self.add(")ifel(")

    def continue_if(self) -> None:
        self.pop_section()
        self.add_section()
        self.goto(None)
        self.add(";")

    def end_if(self) -> None:
        self.pop_section()
        self.goto(None)
        self.add(")")
        self.size = self.call_stack[-1]
        self.pop_section()


class Macro:
    def __init__(
        self,
        name: str,
        c_params: list[tuple[str, Any]],
        params: list[BinX],
        ret: list[ConstExpr],
    ) -> None:
        self.name = name
        self.params = c_params
        self.data = BinXManager(params, ret)

    def build(
        name: str,
        c_params: list[tuple[str, Any]],
        params: list[BinX],
        ret: list[ConstExpr],
        include: list[ConstExpr] | None = None,
    ) -> "Macro":
        base = Macro(name, c_params, params, ret)
        base.data.add(name)
        base.data.add("(")
        if include != None:
            first = True
            for i in include:
                i.force_nnint = True
                if first:
                    first = False
                else:
                    base.data.add(";")
                base.data.add(i)
        base.data.add(")")
        return base

    def invoke(self, params: list[ConstExpr]) -> str:
        for i in range(len(params)):
            if not params[i].done:
                raise NameError(f"The {i}th parameter hasn't been completed.")
        code = self.data.code.copy()
        for i in range(len(code)):
            if type(code[i]) == ConstExpr:
                for j in range(len(params)):
                    if type(code[i]) == ConstExpr:
                        code[i] = code[i].replace(self.params[j][0], params[j])
            if type(code[i]) == MacroInvocation:
                code[i].prepare(
                    [(self.params[j][0], params[j]) for j in range(len(params))]
                )
        return "".join(map(str, code))


class MacroInvocation:
    def __init__(self, macro: Macro, params: list[ConstExpr]) -> None:
        if len(params) != len(macro.params):
            raise TypeError(
                f"The macro {macro.name} takes {len(macro.params)} positional arguments but {len(params)} were provided."
            )
        for i in range(len(params)):
            if type(params[i]) != macro.params[i][1]:
                raise TypeError(
                    f"The macro {macro.name} in argument position {i} has type {macro.params[i][1]} but the type {type(params[i])} was provided."
                )
        self.macro = macro
        self.params = params
        self.current = None
        self.v_params = []
        self.ret = []

    def set_v_params(self, v_params: list[ConstExpr]) -> None:
        self.v_params = v_params

    def set_ret(self, ret: list[ConstExpr]) -> None:
        self.ret = ret

    def prepare(self, params: list[tuple[str, ConstExpr]]) -> None:
        self.current = self.params.copy()
        v_params = self.v_params.copy()
        ret = self.ret.copy()
        for i in range(len(self.current)):
            for j in range(len(params)):
                self.current[i] = self.current[i].replace(params[j][0], params[j][1])
        for i in range(len(v_params)):
            for j in range(len(params)):
                v_params[i] = v_params[i].replace(params[j][0], params[j][1])
        for i in range(len(ret)):
            for j in range(len(params)):
                ret[i] = ret[i].replace(params[j][0], params[j][1])
        t_v_params = self.test_params()
        t_ret = self.test_ret()
        for i in range(len(t_v_params)):
            for j in range(len(params)):
                t_v_params[i] = t_v_params[i].replace(params[j][0], params[j][1])
        for i in range(len(t_ret)):
            for j in range(len(params)):
                t_ret[i] = t_ret[i].replace(params[j][0], params[j][1])
        if t_v_params != v_params:
            raise TypeError(
                f"Expected expressions to be the same but got {v_params} and {t_v_params}."
            )
        if ret != t_ret:
            raise TypeError(
                f"Expected expressions to be the same but got {ret} and {t_ret}."
            )

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
        "implant": Macro.build(
            "implant",
            [("x", ConstExpr), ("v", ConstExpr)],
            [],
            [ConstExpr([ConstRef("x")])],
            [ConstExpr([ConstRef("x")]), ConstExpr([ConstRef("v")])],
        ),
        "printbinx": Macro.build(
            "printbinx",
            [("x", ConstExpr)],
            [BinX("binx", ConstExpr([ConstRef("x")]))],
            [],
            [ConstExpr([ConstRef("x")])],
        ),
        "kill": Macro.build("kill", [], [], [], []),
        "endl": Macro.build("endl", [], [], [], []),
        "space": Macro.build("space", [], [], [], []),
        "printintbinx": Macro.build(
            "printcleanintbinx",
            [("x", ConstExpr)],
            [BinX("binx", ConstExpr([ConstRef("x")]))],
            [],
            [ConstExpr([ConstRef("x")])],
        ),
        "addbinx": Macro.build(
            "addbinx",
            [("x", ConstExpr)],
            [
                BinX("a", ConstExpr([ConstRef("x")])),
                BinX("b", ConstExpr([ConstRef("x")])),
            ],
            [ConstExpr([ConstRef("x")])],
            [ConstExpr([ConstRef("x")])],
        ),
        "subbinx": Macro.build(
            "subbinx",
            [("x", ConstExpr)],
            [
                BinX("a", ConstExpr([ConstRef("x")])),
                BinX("b", ConstExpr([ConstRef("x")])),
            ],
            [ConstExpr([ConstRef("x")])],
            [ConstExpr([ConstRef("x")])],
        ),
        "multbinx": Macro.build(
            "multbinx",
            [("x", ConstExpr)],
            [
                BinX("a", ConstExpr([ConstRef("x")])),
                BinX("b", ConstExpr([ConstRef("x")])),
            ],
            [ConstExpr([ConstRef("x")])],
            [ConstExpr([ConstRef("x")])],
        ),
        "divbinx": Macro.build(
            "divbinx",
            [("x", ConstExpr)],
            [
                BinX("a", ConstExpr([ConstRef("x")])),
                BinX("b", ConstExpr([ConstRef("x")])),
            ],
            [ConstExpr([ConstRef("x")])],
            [ConstExpr([ConstRef("x")])],
        ),
        "lshiftbinx": Macro.build(
            "lshiftbinx",
            [("x", ConstExpr)],
            [BinX("binx", ConstExpr([ConstRef("x")]))],
            [ConstExpr([ConstRef("x")])],
            [ConstExpr([ConstRef("x")])],
        ),
        "rshiftbinx": Macro.build(
            "rshiftbinx",
            [("x", ConstExpr)],
            [BinX("binx", ConstExpr([ConstRef("x")]))],
            [ConstExpr([ConstRef("x")])],
            [ConstExpr([ConstRef("x")])],
        ),
        "eqbinx": Macro.build(
            "eqbinx",
            [("x", ConstExpr)],
            [
                BinX("binx", ConstExpr([ConstRef("x")])),
                BinX("biny", ConstExpr([ConstRef("x")])),
            ],
            [ConstExpr(["1"])],
            [ConstExpr([ConstRef("x")])],
        ),
        "diffbinx": Macro.build(
            "diffbinx",
            [("x", ConstExpr)],
            [
                BinX("binx", ConstExpr([ConstRef("x")])),
                BinX("biny", ConstExpr([ConstRef("x")])),
            ],
            [ConstExpr(["1"])],
            [ConstExpr([ConstRef("x")])],
        ),
        "lessbinx": Macro.build(
            "lessbinx",
            [("x", ConstExpr)],
            [
                BinX("binx", ConstExpr([ConstRef("x")])),
                BinX("biny", ConstExpr([ConstRef("x")])),
            ],
            [ConstExpr(["1"])],
            [ConstExpr([ConstRef("x")])],
        ),
        "greatbinx": Macro.build(
            "greatbinx",
            [("x", ConstExpr)],
            [
                BinX("binx", ConstExpr([ConstRef("x")])),
                BinX("biny", ConstExpr([ConstRef("x")])),
            ],
            [ConstExpr(["1"])],
            [ConstExpr([ConstRef("x")])],
        ),
        "orbinx": Macro.build(
            "orbinx",
            [("x", ConstExpr)],
            [
                BinX("binx", ConstExpr([ConstRef("x")])),
                BinX("biny", ConstExpr([ConstRef("x")])),
            ],
            [ConstExpr([ConstRef("x")])],
            [ConstExpr([ConstRef("x")])],
        ),
        "andbinx": Macro.build(
            "andbinx",
            [("x", ConstExpr)],
            [
                BinX("binx", ConstExpr([ConstRef("x")])),
                BinX("biny", ConstExpr([ConstRef("x")])),
            ],
            [ConstExpr([ConstRef("x")])],
            [ConstExpr([ConstRef("x")])],
        ),
        "notbinx": Macro.build(
            "notbinx",
            [("x", ConstExpr)],
            [BinX("binx", ConstExpr([ConstRef("x")]))],
            [ConstExpr([ConstRef("x")])],
            [ConstExpr([ConstRef("x")])],
        ),
        "boolbinx": Macro.build(
            "boolbinx",
            [("x", ConstExpr)],
            [BinX("binx", ConstExpr([ConstRef("x")]))],
            [ConstExpr(["1"])],
            [ConstExpr([ConstRef("x")])],
        ),
        "orbool": Macro.build(
            "or",
            [],
            [BinX("binx", ConstExpr(["1"])), BinX("biny", ConstExpr(["1"]))],
            [ConstExpr(["1"])],
            [],
        ),
        "andbool": Macro.build(
            "and",
            [],
            [BinX("binx", ConstExpr(["1"])), BinX("biny", ConstExpr(["1"]))],
            [ConstExpr(["1"])],
            [],
        ),
        "notbool": Macro.build(
            "not", [], [BinX("binx", ConstExpr(["1"]))], [ConstExpr(["1"])], []
        ),
        "copy": Macro.build(
            "fakecopy",
            [("x", ConstExpr)],
            [BinX("binx", ConstExpr([ConstRef("x")]))],
            [ConstExpr([ConstRef("x")])],
            [],
        ),
        "getintbinx": Macro.build(
            "getintbinx",
            [("x", ConstExpr)],
            [],
            [ConstExpr([ConstRef("x")])],
            [ConstExpr([ConstRef("x")])],
        ),
    }

    def __init__(self, tree: VP.ASTNode) -> None:
        self.tree = Cleaner(tree).clean()
        self.macros: dict[str, Macro] = dict()
        self.consts: dict[str, Any] = dict()
        self.local_consts: dict[str, Any] = dict()

    def __const_expr(self, node: ASTNode) -> ConstExpr:
        result = ConstExpr.builder(node)
        for i, j in self.local_consts.items():
            result = result.replace(i, j)
        for i, j in self.consts.items():
            result = result.replace(i, j)
        return result

    def __const_def(self, node: ASTNode) -> tuple[str, Any]:
        if node.data[0].data[0].value == "num":
            return node.data[1].value, self.__const_expr(node.data[2])
        raise TypeError(f"Unkown type {node.data[0].data[0].value}.")

    def __const_param_struct(self, node: ASTNode) -> list[tuple[str, Any]]:
        data = []
        for i in range(0, len(node.data), 3):
            if node.data[i].data[0].value == "num":
                data.append((node.data[i + 1].value, ConstExpr))
            else:
                raise TypeError(f"Unkown type {node.data[i].data[0].value}.")
        return data

    def __const_struct(self, node: ASTNode) -> list[ConstExpr]:
        data = []
        for i in range(0, len(node.data), 2):
            data.append(self.__const_expr(node.data[i]))
        return data

    def __param_struct(self, node: ASTNode) -> list[BinX]:
        data = []
        for i in range(0, len(node.data), 3):
            data.append(BinX(node.data[i + 1].value, self.__const_expr(node.data[i])))
        return data

    def __var_struct(self, node: ASTNode) -> list[str | None]:
        data = []
        pos = 0
        while pos < len(node.data):
            if node.data[pos].type == TokenType.Separator:
                data.append(None)
            else:
                data.append(node.data[pos].value)
                pos += 1
            pos += 1
        return data

    def __call(
        self, node: ASTNode
    ) -> tuple[MacroInvocation, list[str | None], list[str | None]]:
        name = node.data[1].value
        if name in self.macros:
            mi = MacroInvocation(
                self.macros[node.data[1].value], self.__const_struct(node.data[0])
            )
        elif name in Processor.inbuilt_macros:
            mi = MacroInvocation(
                Processor.inbuilt_macros[node.data[1].value],
                self.__const_struct(node.data[0]),
            )
        else:
            raise NameError(f"The macro {name} is undefined.")
        return mi, self.__var_struct(node.data[2]), self.__var_struct(node.data[3])

    def __macro_def(self, node: ASTNode) -> tuple[str, Macro]:
        name = node.data[1].value
        self.local_consts = dict()
        mac = Macro(
            name,
            self.__const_param_struct(node.data[0]),
            self.__param_struct(node.data[3]),
            self.__const_struct(node.data[2]),
        )

        def process_block(data: ASTNode) -> None:
            for i in data.data:
                stmt: ASTNode = i.data[0]
                if stmt.name == "const_def":
                    cdef = self.__const_def(stmt)
                    self.local_consts[cdef[0]] = cdef[1]
                elif stmt.name == "call":
                    invc = self.__call(stmt)
                    if invc[0].macro.name == "lessbinx":
                        mac.data.goto(None)
                        mac.data.add("@")
                    mac.data.do_call(
                        invc[0],
                        invc[2],
                        invc[0].test_params(),
                        invc[1],
                        invc[0].test_ret(),
                    )
                    if invc[0].macro.name == "lessbinx":
                        mac.data.goto(None)
                        mac.data.add("@")
                elif stmt.name == "return":
                    s = []
                    if len(stmt.data) == 1:
                        s = self.__var_struct(stmt.data[0])
                    mac.data.fuck(s)
                elif stmt.name == "ifel":
                    expr = self.__const_expr(stmt.data[0])
                    if (
                        len(expr.data) == 1
                        and type(expr.data[0]) == ConstRef
                        and expr.data[0].name in mac.data.pos_table
                    ):
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
                    if (
                        len(expr.data) == 1
                        and type(expr.data[0]) == ConstRef
                        and expr.data[0].name in mac.data.pos_table
                    ):
                        mac.data.start_while(expr.data[0].name)
                        process_block(stmt.data[1])
                        mac.data.end_while()
                    else:
                        mac.data.start_repeat(expr)
                        process_block(stmt.data[1])
                        mac.data.end_repeat()
                else:
                    raise SyntaxError(f"{stmt.name}???")

        process_block(node.data[4])
        mac.data.end()
        return name, mac

    def process(self) -> None:
        for i in self.tree.data[:-1]:
            if i.name == "const_def":
                cdef = self.__const_def(i)
                self.consts[cdef[0]] = cdef[1]
            elif i.name == "macro_def":
                mdef = self.__macro_def(i)
                self.macros[mdef[0]] = mdef[1]
            else:
                raise SyntaxError(f"{i.name}???")
        self.start = self.__call(self.tree.data[-1])[0]

    def build(self) -> str:
        self.start.prepare([])
        return str(self.start)


# TODO temp
def show_AST(node: ASTNode | VP.Token, level=0):
    print(level * "\t", end="")
    if type(node) == VP.Token:
        print(node.type, repr(str(node.value)))
    else:
        print("> ", node.name)
        for i in node.data:
            show_AST(i, level + 1)


if __name__ == "__main__":
    with open("naipes.vk", "r") as f:
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
    print("\n=======================\nBrainfuck code\n=======================")
    import BrainfuckInterpreter

    b = BrainfuckInterpreter.Interpreter(proc.build(), False)
    print(b.code)
    print("\n=======================\nCode size\n=======================")
    print(len(b.code))
    print("\n=======================\nStarting Varfuck code\n=======================")
    print(t)
    print("\n=======================\nRunning code...\n=======================")
    b.run(True)
