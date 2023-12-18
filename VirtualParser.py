from enum import Enum
from typing import Union


class TokenType(Enum):
    EOF = -1


class Token:
    def __init__(self, type: Enum, value: str) -> None:
        self.type = type
        self.value = value

    def __eq__(self, __value: object) -> bool:
        if type(__value) == Token:
            return (
                __value.type == self.type or __value.type.value == self.type.value
            ) and __value.value == self.value
        elif isinstance(__value, Enum):
            return __value == self.type or __value.value == self.type.value
        return False

    def __ne__(self, __value: object) -> bool:
        return not self.__eq__(__value)

    def __str__(self) -> str:
        return repr(self.type) + " " + repr(self.value)

    def __hash__(self) -> int:
        return hash(self.__str__())


class BaseLexer:
    def __init__(self) -> None:
        self.pos = 0

    def next_token(self) -> Token:
        raise NotImplementedError()

    def get_position(self) -> int:
        return self.pos

    def set_position(self, pos: int) -> None:
        self.pos = pos


class CountType(Enum):
    ZeroOrOne = 0
    ZeroOrMany = 1
    One = 2
    OneOrMany = 3


class IntermediateForm:
    pass


class Count(IntermediateForm):
    def __init__(
        self,
        node: Union["RuleRef", "Alter", "Concat", "Terminal"],
        count_type: CountType,
    ) -> None:
        self.node = node
        self.count_type = count_type


class Terminal(IntermediateForm):
    def __init__(self, data: Token | Enum) -> None:
        self.data = data


class Concat(IntermediateForm):
    def __init__(self, additions: list[IntermediateForm]) -> None:
        self.additions = additions


class Alter(IntermediateForm):
    def __init__(self, ors: list[IntermediateForm]) -> None:
        self.ors = ors


class RuleRef(IntermediateForm):
    def __init__(self, rule_name: str, spec: IntermediateForm) -> None:
        self.rule_name = rule_name
        self.spec = spec


class Grammar(IntermediateForm):
    def __init__(self, base: IntermediateForm, catch_eof=True) -> None:
        if catch_eof:
            self.base = Concat([base, Terminal(TokenType.EOF)])
        else:
            self.base = base


class ASTNode:
    def __init__(self, rule: str, children: list[Union["ASTNode", Token]]) -> None:
        self.rule = rule
        self.children = children


# DEBUG----------------
# TODO
# Temp
class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


print_level = [0]


def debug(func):
    def printer(self: "Matcher") -> list[ASTNode | Token] | None:
        print(bcolors.OKCYAN, "|  " * print_level[0], ">?", self.__class__.__name__)
        print_level[0] += 1
        result = func(self)
        if result == None:
            print(bcolors.FAIL, "|  " * print_level[0], "<!", self.__class__.__name__)
        else:
            print(
                bcolors.OKGREEN, "|  " * print_level[0], "<#", self.__class__.__name__
            )
        print_level[0] -= 1
        return result

    return printer


def debug_print(data):
    print(bcolors.ENDC, "|  " * print_level[0], ">:", data)


# DEBUG----------------


def call_index(func):
    def call(self: Matcher) -> list[ASTNode | Token] | None:
        self.call_index += 1
        result = func(self)
        self.call_index -= 1
        return result

    return call


class Matcher:
    def __init__(self) -> None:
        self.call_index = -1

    def start(self) -> None:
        pass

    @debug
    def next_match(self) -> list[ASTNode | Token] | None:
        raise NotImplementedError()


class EmptyMatcher(Matcher):
    def __init__(self) -> None:
        super().__init__()
        self.ready = []

    def start(self) -> None:
        self.ready.append(True)

    @debug
    def next_match(self) -> list[ASTNode | Token] | None:
        if self.ready[-1]:
            self.ready[-1] = False
            return []
        self.ready.pop()
        return None


class LiteralMatcher(Matcher):
    def __init__(
        self, lexer: BaseLexer, data: Token | Enum, forget: bool = False
    ) -> None:
        super().__init__()
        self.data = data
        self.positions = []
        self.forget = forget
        self.lexer = lexer
        self.ready = []

    def start(self) -> None:
        self.positions.append(self.lexer.get_position())
        self.ready.append(True)

    @debug
    def next_match(self) -> list[ASTNode | Token] | None:
        debug_print(f"data = {self.data}; position = {self.positions[-1]}")  # TODO
        self.lexer.set_position(self.positions[-1])
        token = self.lexer.next_token()
        debug_print(f"token = {token}")  # TODO
        if self.data == token and self.ready[-1]:
            self.ready[-1] = False
            return [token] if not self.forget else []
        self.lexer.set_position(self.positions[-1])
        self.ready.pop()
        self.positions.pop()
        return None


class ConcatMatcher(Matcher):
    def __init__(self, this: Matcher, next: Union["ConcatMatcher", None]) -> None:
        super().__init__()
        self.this = this
        self.next = next
        self.level: list[int] = []
        self.built: list[list] = []

    def start(self) -> None:
        if self.call_index == len(self.level) - 1:
            self.level.append(0)
            self.built.append([])
        self.level[self.call_index + 1] += 1
        self.this.start()

    @call_index
    @debug
    def next_match(self) -> list[ASTNode | Token] | None:
        if not self.level:
            return None
        if self.level[self.call_index] != len(self.built[self.call_index]):
            result = self.this.next_match()
            if result == None:
                self.level[self.call_index] -= 1
                if self.level[-1] == 0:
                    self.level.pop()
                    self.built.pop()
                return None
            self.built[self.call_index].append(result)
            if self.next == None:
                return self.built[self.call_index][-1]
            self.next.start()
        cindex = self.level[self.call_index] - 1
        result = None
        while True:
            if self.next != None:
                result = self.next.next_match()
            if result == None:
                result = self.this.next_match()
                if result == None:
                    self.level[self.call_index] -= 1
                    self.built[self.call_index].pop()
                    if self.level[-1] == 0:
                        self.level.pop()
                        self.built.pop()
                    return None
                self.built[self.call_index][cindex] = result
                if self.next == None:
                    return self.built[self.call_index][cindex]
                self.next.start()
                result = None
            else:
                return self.built[self.call_index][cindex] + result


class AlterMatcher(Matcher):
    def __init__(self, this: Matcher, next: Union["AlterMatcher", None]) -> None:
        super().__init__()
        self.this = this
        self.next = next
        self.selected: list[list] = []

    def start(self) -> None:
        if self.call_index == len(self.selected) - 1:
            self.selected.append([])
        self.selected[self.call_index + 1].append(True)
        self.this.start()

    @call_index
    @debug
    def next_match(self) -> list[ASTNode | Token] | None:
        if self.selected[self.call_index][-1]:
            result = self.this.next_match()
            if result != None:
                return result
            if self.next == None:
                self.selected[self.call_index].pop()
                if not len(self.selected[-1]):
                    self.selected.pop()
                return None
            self.selected[self.call_index][-1] = False
            self.next.start()
        result = self.next.next_match()
        if result == None:
            self.selected[self.call_index].pop()
            if not len(self.selected[-1]):
                self.selected.pop()
        return result


class RuleMatcher(Matcher):
    def __init__(
        self, rule_name: str, matcher: "CountMatcher", forget: bool = False
    ) -> None:
        super().__init__()
        self.rule_name = rule_name
        self.matcher = matcher
        self.forget = forget

    def start(self) -> None:
        self.matcher.start()

    @debug
    def next_match(self) -> list[ASTNode | Token] | None:
        debug_print(f"rule_name = {self.rule_name}")  # TODO
        result = self.matcher.next_match()
        if result == None:
            return None
        show_AST(ASTNode(self.rule_name, result))  # TODO
        return [ASTNode(self.rule_name, result)] if not self.forget else []


class CountMatcher(Matcher):
    def __init__(self, matcher: Matcher, count_type: CountType) -> None:
        super().__init__()
        self.matcher = matcher
        self.count_type = count_type
        self.data: list[list[list[ASTNode | Token]]] = []
        self.level = []

    def start(self) -> None:
        if self.call_index == len(self.level) - 1:
            self.level.append(0)
            self.data.append([])
        self.level[self.call_index + 1] += 1

    @call_index
    @debug
    def next_match(self) -> list[ASTNode | Token] | None:
        debug_print(f"type = {self.count_type}")
        if len(self.data[self.call_index]) != self.level[self.call_index]:
            debug_print("Starting count...")
            self.matcher.start()
            result = self.matcher.next_match()
            build = []
            if result == None:
                if (
                    self.count_type == CountType.One
                    or self.count_type == CountType.OneOrMany
                ):
                    self.level[self.call_index] -= 1
                    if self.level[-1] == 0:
                        self.level.pop()
                        self.data.pop()
                    return None
            else:
                if (
                    self.count_type == CountType.One
                    or self.count_type == CountType.ZeroOrOne
                ):
                    build.append(result)
                else:
                    while result != None:
                        build.append(result)
                        self.matcher.start()
                        result = self.matcher.next_match()
            self.data[self.call_index].append(build)
            result = []
            for i in build:
                result += i
            return result
        build = self.data[self.call_index][-1]
        if not len(build):
            self.level[self.call_index] -= 1
            self.data[self.call_index].pop()
            if not self.level[-1]:
                self.level.pop()
                self.data.pop()
            return None
        build.pop()
        result = self.matcher.next_match()
        if self.count_type == CountType.One or self.count_type == CountType.ZeroOrOne:
            if result != None:
                build.append(result)
        else:
            while result != None:
                build.append(result)
                self.matcher.start()
                result = self.matcher.next_match()
        if len(build):
            result = []
            for i in build:
                result += i
            return result
        if self.count_type == CountType.One or self.count_type == CountType.OneOrMany:
            self.level[self.call_index] -= 1
            self.data[self.call_index].pop()
            if not self.level[-1]:
                self.level.pop()
                self.data.pop()
            return None
        return []


class GrammarMatcher(Matcher):
    def __init__(self, matcher: ConcatMatcher) -> None:
        super().__init__()
        self.matcher = matcher

    def start(self) -> None:
        self.matcher.start()

    @debug
    def next_match(self) -> list[ASTNode | Token] | None:
        return self.matcher.next_match()


class Parser:
    def __init__(
        self,
        tree: Grammar,
        lexer: BaseLexer,
        terminal_token_table: dict[Token | Enum, Token | Enum],
        rule_token_table: dict[str, Token | Enum] = dict(),
        terminal_forget_set: set[Token | Enum] = set(),
        rule_forget_set: set[str] = set(),
    ) -> None:
        self.tree = tree
        self.lexer = lexer
        self.terminal_token_table = terminal_token_table
        self.rule_token_table = rule_token_table
        self.rule_forget_set = rule_forget_set
        self.terminal_forget_set = terminal_forget_set

    def __get_matcher_literal(self, data: Token | Enum) -> LiteralMatcher:
        if data in self.terminal_token_table:
            data = self.terminal_token_table[data]
        forget = data in self.terminal_forget_set
        if not forget and type(data) == Token:
            forget = data.type in self.terminal_forget_set
        return LiteralMatcher(self.lexer, data, forget)

    def __get_matcher_terminal(self, terminal: Terminal) -> LiteralMatcher:
        if terminal not in self.matchers:
            self.matchers[terminal] = self.__get_matcher_literal(terminal.data)
        return self.matchers[terminal]

    def __get_matcher_concat(self, concat: Concat) -> ConcatMatcher:
        if concat not in self.matchers:
            matcher = None
            for i in reversed(concat.additions):
                matcher = ConcatMatcher(self.__get_matcher(i), matcher)
            self.matchers[concat] = matcher
        return self.matchers[concat]

    def __get_matcher_alter(self, alter: Alter) -> AlterMatcher:
        if alter not in self.matchers:
            matcher = None
            for i in reversed(alter.ors):
                matcher = AlterMatcher(self.__get_matcher(i), matcher)
            self.matchers[alter] = matcher
        return self.matchers[alter]

    def __get_matcher_rule(self, rule: RuleRef) -> RuleMatcher | LiteralMatcher:
        if rule not in self.matchers:
            matcher = None
            if rule.rule_name in self.rule_token_table:
                matcher = self.__get_matcher_literal(
                    self.rule_token_table[rule.rule_name]
                )
            else:
                matcher = RuleMatcher(rule.rule_name, None)
                self.matchers[rule] = matcher
                matcher.matcher = self.__get_matcher(rule.spec)
            self.matchers[rule] = matcher
        return self.matchers[rule]

    def __get_matcher_count(self, count: Count) -> CountMatcher:
        if count not in self.matchers:
            self.matchers[count] = CountMatcher(
                self.__get_matcher(count.node), count.count_type
            )
        return self.matchers[count]

    def __get_matcher_grammar(self, grammar: Grammar) -> GrammarMatcher:
        return GrammarMatcher(self.__get_matcher(grammar.base))

    def __get_matcher(self, IF: IntermediateForm) -> Matcher:
        t = type(IF)
        if t == Count:
            return self.__get_matcher_count(IF)
        elif t == RuleRef:
            return self.__get_matcher_rule(IF)
        elif t == Terminal:
            return self.__get_matcher_terminal(IF)
        elif t == Alter:
            return self.__get_matcher_alter(IF)
        elif t == Concat:
            return self.__get_matcher_concat(IF)
        elif t == Grammar:
            return self.__get_matcher_grammar(IF)
        elif t == IntermediateForm:
            return EmptyMatcher()
        else:
            raise SyntaxError(
                "Wrong IF structure."
            )  # TODO put correct error (SyntaxError should only happen during parsing????)

    def create_matchers(self, grammar: Grammar) -> GrammarMatcher:
        self.matchers = dict()
        return self.__get_matcher_grammar(grammar)

    def parse(self) -> list[ASTNode | Token]:
        matcher = self.create_matchers(self.tree)
        matcher.start()
        try:
            result = matcher.next_match()
        except RecursionError as e:
            raise SyntaxError("Left recursion grammar failed to be parsed.")
        if result == None:
            raise SyntaxError("Invalid syntax.")
        return result

    def reset(self) -> None:
        self.lexer.set_position(0)


def show_AST(node: ASTNode | Token, level=0):
    print(level * "\t", end="")
    if type(node) == Token:
        print(node.type, repr(str(node.value)))
    else:
        print("> ", node.rule)
        for i in node.children:
            show_AST(i, level + 1)


def show_IF(
    data: IntermediateForm, level=0, showed: list[IntermediateForm] = []
) -> None:
    if data in showed:
        if type(data) == RuleRef:
            print(level * "  ", end="")
            print("Rule", data.rule_name, "...")
        return
    print(level * "  ", end="")
    t = type(data)
    showed.append(data)
    if t == Terminal:
        print(data.data)
    else:
        print("> ", end="")
        if t == Alter:
            print("Alter")
            for i in data.ors:
                show_IF(i, level + 1)
        elif t == Concat:
            print("Concat")
            for i in data.additions:
                show_IF(i, level + 1)
        elif t == RuleRef:
            print("Rule", data.rule_name)
            show_IF(data.spec, level + 1)
        elif t == Count:
            print("Count", data.count_type)
            show_IF(data.node, level + 1)
        elif t == Grammar:
            print("Grammar")
            show_IF(data.base, level + 1)
