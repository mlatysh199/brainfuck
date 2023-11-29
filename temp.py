# This file was generated on Fri May 19, 2023 08:24 (UTC-06) by REx v5.56 which is Copyright (c) 1979-2023 by Gunther Rademacher <grd@gmx.net>
# REx command line: temp.ebnf -python -tree -main

import sys

class temp:

  class ParseException(Exception):

    def __init__(self, b, e, s, o, x):
      self.begin = b
      self.end = e
      self.state = s
      self.offending = o
      self.expected = x

    def error(self):
      if self.offending < 0:
        return "lexical analysis failed"
      else:
        return "syntax error"

    def serialize(self, eventHandler):
      pass

    def getBegin(self):
      return self.begin

    def getEnd(self):
      return self.end

    def getState(self):
      return self.state

    def getOffending(self):
      return self.offending

    def getExpected(self):
      return self.expected

    def isAmbiguousInput(self):
      return False

  class TopDownTreeBuilder:

    def reset(self, inputString):
      self.input = inputString
      self.stack = []
      self.top = -1

    def startNonterminal(self, name, begin):
      nonterminal = temp.Nonterminal(name, begin, begin)
      if self.top >= 0:
        self.addChild(nonterminal)
      self.top += 1
      self.stack[self.top] = nonterminal

    def endNonterminal(self, _, end):
      self.stack[self.top].end = end
      if self.top > 0:
        self.top -= 1

    def terminal(self, name, begin, end):
      self.addChild(temp.Terminal(name, begin, end))

    def whitespace(self, begin, end):
      pass

    def addChild(self, s):
      current = self.stack[self.top]
      current.addChild(s)

    def serialize(self, e):
      e.reset(self.input)
      self.stack[0].send(e)

  class Symbol:

    def __init__(self, name, begin, end):
      self.name = name
      self.begin = begin
      self.end = end

    def getName(self):
      return self.name

    def getBegin(self):
      return self.begin

    def getEnd(self):
      return self.end

  class Nonterminal(Symbol):

    def __init__(self, name, begin, end, children):
      super().__init__(name, begin, end)
      self.children = children

    def addChild(self, s):
      self.children = self.children.append(s)

    def send(self, e):
      e.startNonterminal(self.getName(), self.getBegin())
      pos = self.getBegin()
      for c in self.children:
        if pos < c.getBegin():
          e.whitespace(pos, c.getBegin())
        c.send(e)
        pos = c.getEnd()
      if pos < self.getEnd():
        e.whitespace(pos, self.getEnd())
      e.endNonterminal(self.getName(), self.getEnd())

  class Terminal(Symbol):

    def __init__(self, name, begin, end):
      super().__init__(name, begin, end)

    def send(self, e):
      e.terminal(self.getName(), self.getBegin(), self.getEnd())

  class XmlSerializer:

    def reset(self, inputString):
      sys.stdout.reconfigure(encoding="utf-8")
      print("<?xml version=\"1.0\" encoding=\"UTF-8\"?>", end="")
      self.input = inputString
      self.delayedTag = None
      self.hasChildElement = False
      self.depth = 0

    def startNonterminal(self, tag, _):
      if self.delayedTag != None:
        print("<", end="")
        print(self.delayedTag, end="")
        print(">", end="")
      self.delayedTag = tag
      if self.indent:
        print()
        for _ in range(self.depth):
          print("  ", end="")
      self.hasChildElement = False
      self.depth += 1

    def endNonterminal(self, tag, _):
      self.depth -= 1
      if self.delayedTag != None:
        self.delayedTag = None
        print("<", end="")
        print(tag, end="")
        print("/>", end="")
      else:
        if self.indent:
          if self.hasChildElement:
            print()
            for _ in range(self.depth):
              print("  ", end="")
        print("</", end="")
        print(tag, end="")
        print(">", end="")
      self.hasChildElement = True

    def whitespace(self, b, e):
      self.characters(b, e)

    def characters(self, b, e):
      if b < e:
        if self.delayedTag != None:
          print("<", end="")
          print(self.delayedTag, end="")
          print(">", end="")
          self.delayedTag = None
        i = b
        while i < e:
          c = self.input[i]
          i += 1
          if c == '&':
            print("&amp;", end="")
          elif c == '<':
            print("&lt;", end="")
          elif c == '>':
            print("&gt;", end="")
          else:
            print(str(c), end="")

    def terminal(self, tag, b, e):
      if tag[0] == '\'':
        tag = "TOKEN"
      self.startNonterminal(tag, b)
      self.characters(b, e)
      self.endNonterminal(tag, e)

  def __init__(self, inputString, t):
    self.initialize(inputString, t)

  def initialize(self, source, parsingEventHandler):
    self.eventHandler = parsingEventHandler
    self.input = source
    self.size = len(source)
    self.reset(0, 0, 0)

  def getInput(self):
    return self.input

  def getTokenOffset(self):
    return self.b0

  def getTokenEnd(self):
    return self.e0

  def reset(self, l, b, e):
    self.b0 = b; self.e0 = b
    self.l1 = l; self.b1 = b; self.e1 = e
    self.end = e
    self.eventHandler.reset(self.input)

  @staticmethod
  def getOffendingToken(e):
    if e.getOffending() < 0:
      return ""
    else:
      return temp.TOKEN[e.getOffending()]

  @staticmethod
  def getExpectedTokenSet(e):
    if e.expected < 0:
      return temp.getTokenSet(- e.state)
    else:
      return [temp.TOKEN[e.expected]]

  def getErrorMessage(self, e):
    message = e.error()
    found = temp.getOffendingToken(e)
    if found != "":
      message += ", found "
      message += found
    expected = temp.getExpectedTokenSet(e)
    message += "\nwhile expecting "
    delimiter = ""
    if len(expected) != 1:
      delimiter = "["
    for token in expected:
      message += delimiter
      message += token
      delimiter = ", "
    if len(expected) != 1:
      message += "]"
    message += "\n"
    size = e.getEnd() - e.getBegin()
    if size != 0 and found == "":
      message += "after successfully scanning "
      message += str(size)
      message += " characters beginning "
    line = 1
    column = 1
    for i in range(e.getBegin()):
      if self.input[i] == '\n':
        line += 1
        column = 1
      else:
        column += 1
    message += "at line "
    message += str(line)
    message += ", column "
    message += str(column)
    message += ":\n..."
    end = e.getBegin() + 64
    if end > len(self.input):
      end = len(self.input)
    message += self.input[e.getBegin() : end]
    message += "..."
    return message

  def parse_breaker(self):
    self.eventHandler.startNonterminal("breaker", self.e0)
    self.lookahead1(2)              # ';' | '\n'
    if self.l1 == 48:               # '\n'
      self.consume(48)              # '\n'
    else:
      self.consume(19)              # ';'
    self.eventHandler.endNonterminal("breaker", self.e0)

  def parse_const_op(self):
    self.eventHandler.startNonterminal("const_op", self.e0)
    self.lookahead1(4)              # '&' | '*' | '**' | '+' | '-' | '/' | '<<' | '>>' | '^' | '|'
    if self.l1 == 4:                # '**'
      self.consume(4)               # '**'
    elif self.l1 == 3:              # '*'
      self.consume(3)               # '*'
    elif self.l1 == 8:              # '/'
      self.consume(8)               # '/'
    elif self.l1 == 5:              # '+'
      self.consume(5)               # '+'
    elif self.l1 == 7:              # '-'
      self.consume(7)               # '-'
    elif self.l1 == 20:             # '<<'
      self.consume(20)              # '<<'
    elif self.l1 == 21:             # '>>'
      self.consume(21)              # '>>'
    elif self.l1 == 2:              # '&'
      self.consume(2)               # '&'
    elif self.l1 == 77:             # '|'
      self.consume(77)              # '|'
    else:
      self.consume(49)              # '^'
    self.eventHandler.endNonterminal("const_op", self.e0)

  def parse_u_const_op(self):
    self.eventHandler.startNonterminal("u_const_op", self.e0)
    self.lookahead1(1)              # '-' | '~'
    if self.l1 == 78:               # '~'
      self.consume(78)              # '~'
    else:
      self.consume(7)               # '-'
    self.eventHandler.endNonterminal("u_const_op", self.e0)

  def parse_const_name(self):
    self.eventHandler.startNonterminal("const_name", self.e0)
    self.parse_string()
    self.eventHandler.endNonterminal("const_name", self.e0)

  def parse_separator(self):
    self.eventHandler.startNonterminal("separator", self.e0)
    self.lookahead1(0)              # ','
    self.consume(6)                 # ','
    self.eventHandler.endNonterminal("separator", self.e0)

  def parse_result(self):
    self.eventHandler.startNonterminal("result", self.e0)
    self.lookahead1(8)              # '-' | '0' | '1' | '2' | '3' | '4' | '5' | '6' | '7' | '8' | '9' | 'A' | 'B' |
                                    # 'C' | 'D' | 'E' | 'F' | 'G' | 'H' | 'I' | 'J' | 'K' | 'L' | 'M' | 'N' | 'O' |
                                    # 'P' | 'Q' | 'R' | 'S' | 'T' | 'U' | 'V' | 'W' | 'X' | 'Y' | 'Z' | '_' | 'a' |
                                    # 'b' | 'c' | 'd' | 'e' | 'f' | 'g' | 'h' | 'i' | 'j' | 'k' | 'l' | 'm' | 'n' |
                                    # 'o' | 'p' | 'q' | 'r' | 's' | 't' | 'u' | 'v' | 'w' | 'x' | 'y' | 'z'
    if (self.l1 == 7 or             # '-'
        self.l1 == 9 or             # '0'
        self.l1 == 10 or            # '1'
        self.l1 == 11 or            # '2'
        self.l1 == 12 or            # '3'
        self.l1 == 13 or            # '4'
        self.l1 == 14 or            # '5'
        self.l1 == 15 or            # '6'
        self.l1 == 16 or            # '7'
        self.l1 == 17 or            # '8'
        self.l1 == 18):             # '9'
      self.parse_const()
    else:
      self.parse_string()
    self.eventHandler.endNonterminal("result", self.e0)

  def parse_nzdigit(self):
    self.eventHandler.startNonterminal("nzdigit", self.e0)
    self.lookahead1(3)              # '1' | '2' | '3' | '4' | '5' | '6' | '7' | '8' | '9'
    if self.l1 == 10:               # '1'
      self.consume(10)              # '1'
    elif self.l1 == 11:             # '2'
      self.consume(11)              # '2'
    elif self.l1 == 12:             # '3'
      self.consume(12)              # '3'
    elif self.l1 == 13:             # '4'
      self.consume(13)              # '4'
    elif self.l1 == 14:             # '5'
      self.consume(14)              # '5'
    elif self.l1 == 15:             # '6'
      self.consume(15)              # '6'
    elif self.l1 == 16:             # '7'
      self.consume(16)              # '7'
    elif self.l1 == 17:             # '8'
      self.consume(17)              # '8'
    else:
      self.consume(18)              # '9'
    self.eventHandler.endNonterminal("nzdigit", self.e0)

  def parse_digit(self):
    self.eventHandler.startNonterminal("digit", self.e0)
    if self.l1 == 9:                # '0'
      self.consume(9)               # '0'
    else:
      self.parse_nzdigit()
    self.eventHandler.endNonterminal("digit", self.e0)

  def parse_const(self):
    self.eventHandler.startNonterminal("const", self.e0)
    if self.l1 == 9:                # '0'
      self.consume(9)               # '0'
    else:
      if self.l1 == 7:              # '-'
        self.consume(7)             # '-'
      self.parse_nzdigit()
      while True:
        self.lookahead1(5)          # END | '0' | '1' | '2' | '3' | '4' | '5' | '6' | '7' | '8' | '9'
        if self.l1 == 1:            # END
          break
        self.parse_digit()
    self.eventHandler.endNonterminal("const", self.e0)

  def parse_chars(self):
    self.eventHandler.startNonterminal("chars", self.e0)
    self.lookahead1(6)              # 'A' | 'B' | 'C' | 'D' | 'E' | 'F' | 'G' | 'H' | 'I' | 'J' | 'K' | 'L' | 'M' |
                                    # 'N' | 'O' | 'P' | 'Q' | 'R' | 'S' | 'T' | 'U' | 'V' | 'W' | 'X' | 'Y' | 'Z' |
                                    # '_' | 'a' | 'b' | 'c' | 'd' | 'e' | 'f' | 'g' | 'h' | 'i' | 'j' | 'k' | 'l' |
                                    # 'm' | 'n' | 'o' | 'p' | 'q' | 'r' | 's' | 't' | 'u' | 'v' | 'w' | 'x' | 'y' | 'z'
    if self.l1 == 22:               # 'A'
      self.consume(22)              # 'A'
    elif self.l1 == 23:             # 'B'
      self.consume(23)              # 'B'
    elif self.l1 == 24:             # 'C'
      self.consume(24)              # 'C'
    elif self.l1 == 25:             # 'D'
      self.consume(25)              # 'D'
    elif self.l1 == 26:             # 'E'
      self.consume(26)              # 'E'
    elif self.l1 == 27:             # 'F'
      self.consume(27)              # 'F'
    elif self.l1 == 28:             # 'G'
      self.consume(28)              # 'G'
    elif self.l1 == 29:             # 'H'
      self.consume(29)              # 'H'
    elif self.l1 == 30:             # 'I'
      self.consume(30)              # 'I'
    elif self.l1 == 31:             # 'J'
      self.consume(31)              # 'J'
    elif self.l1 == 32:             # 'K'
      self.consume(32)              # 'K'
    elif self.l1 == 33:             # 'L'
      self.consume(33)              # 'L'
    elif self.l1 == 34:             # 'M'
      self.consume(34)              # 'M'
    elif self.l1 == 35:             # 'N'
      self.consume(35)              # 'N'
    elif self.l1 == 36:             # 'O'
      self.consume(36)              # 'O'
    elif self.l1 == 37:             # 'P'
      self.consume(37)              # 'P'
    elif self.l1 == 38:             # 'Q'
      self.consume(38)              # 'Q'
    elif self.l1 == 39:             # 'R'
      self.consume(39)              # 'R'
    elif self.l1 == 40:             # 'S'
      self.consume(40)              # 'S'
    elif self.l1 == 41:             # 'T'
      self.consume(41)              # 'T'
    elif self.l1 == 42:             # 'U'
      self.consume(42)              # 'U'
    elif self.l1 == 43:             # 'V'
      self.consume(43)              # 'V'
    elif self.l1 == 44:             # 'W'
      self.consume(44)              # 'W'
    elif self.l1 == 45:             # 'X'
      self.consume(45)              # 'X'
    elif self.l1 == 46:             # 'Y'
      self.consume(46)              # 'Y'
    elif self.l1 == 47:             # 'Z'
      self.consume(47)              # 'Z'
    elif self.l1 == 51:             # 'a'
      self.consume(51)              # 'a'
    elif self.l1 == 52:             # 'b'
      self.consume(52)              # 'b'
    elif self.l1 == 53:             # 'c'
      self.consume(53)              # 'c'
    elif self.l1 == 54:             # 'd'
      self.consume(54)              # 'd'
    elif self.l1 == 55:             # 'e'
      self.consume(55)              # 'e'
    elif self.l1 == 56:             # 'f'
      self.consume(56)              # 'f'
    elif self.l1 == 57:             # 'g'
      self.consume(57)              # 'g'
    elif self.l1 == 58:             # 'h'
      self.consume(58)              # 'h'
    elif self.l1 == 59:             # 'i'
      self.consume(59)              # 'i'
    elif self.l1 == 60:             # 'j'
      self.consume(60)              # 'j'
    elif self.l1 == 61:             # 'k'
      self.consume(61)              # 'k'
    elif self.l1 == 62:             # 'l'
      self.consume(62)              # 'l'
    elif self.l1 == 63:             # 'm'
      self.consume(63)              # 'm'
    elif self.l1 == 64:             # 'n'
      self.consume(64)              # 'n'
    elif self.l1 == 65:             # 'o'
      self.consume(65)              # 'o'
    elif self.l1 == 66:             # 'p'
      self.consume(66)              # 'p'
    elif self.l1 == 67:             # 'q'
      self.consume(67)              # 'q'
    elif self.l1 == 68:             # 'r'
      self.consume(68)              # 'r'
    elif self.l1 == 69:             # 's'
      self.consume(69)              # 's'
    elif self.l1 == 70:             # 't'
      self.consume(70)              # 't'
    elif self.l1 == 71:             # 'u'
      self.consume(71)              # 'u'
    elif self.l1 == 72:             # 'v'
      self.consume(72)              # 'v'
    elif self.l1 == 73:             # 'w'
      self.consume(73)              # 'w'
    elif self.l1 == 74:             # 'x'
      self.consume(74)              # 'x'
    elif self.l1 == 75:             # 'y'
      self.consume(75)              # 'y'
    elif self.l1 == 76:             # 'z'
      self.consume(76)              # 'z'
    else:
      self.consume(50)              # '_'
    self.eventHandler.endNonterminal("chars", self.e0)

  def parse_string(self):
    self.eventHandler.startNonterminal("string", self.e0)
    while True:
      self.parse_chars()
      self.lookahead1(7)            # END | 'A' | 'B' | 'C' | 'D' | 'E' | 'F' | 'G' | 'H' | 'I' | 'J' | 'K' | 'L' |
                                    # 'M' | 'N' | 'O' | 'P' | 'Q' | 'R' | 'S' | 'T' | 'U' | 'V' | 'W' | 'X' | 'Y' |
                                    # 'Z' | '_' | 'a' | 'b' | 'c' | 'd' | 'e' | 'f' | 'g' | 'h' | 'i' | 'j' | 'k' |
                                    # 'l' | 'm' | 'n' | 'o' | 'p' | 'q' | 'r' | 's' | 't' | 'u' | 'v' | 'w' | 'x' |
                                    # 'y' | 'z'
      if self.l1 == 1:              # END
        break
    self.eventHandler.endNonterminal("string", self.e0)

  def consume(self, t):
    if self.l1 == t:
      self.eventHandler.terminal(temp.TOKEN[self.l1], self.b1, self.e1)
      self.b0 = self.b1; self.e0 = self.e1; self.l1 = 0
    else:
      self.error(self.b1, self.e1, 0, self.l1, t)

  def lookahead1(self, tokenSetId):
    if self.l1 == 0:
      self.l1 = self.match(tokenSetId)
      self.b1 = self.begin
      self.e1 = self.end

  def error(self, b, e, s, l, t):
    raise temp.ParseException(b, e, s, l, t)

  def match(self, tokenSetId):
    self.begin = self.end
    current = self.end
    result = temp.INITIAL[tokenSetId]
    state = 0

    code = result & 15
    while code != 0:
      if current < self.size:
        c0 = ord(self.input[current])
      else:
        c0 = 0
      current += 1
      if c0 < 0x80:
        charclass = temp.MAP0[c0]
      elif c0 < 0xd800:
        c1 = c0 >> 5
        charclass = temp.MAP1[(c0 & 31) + temp.MAP1[(c1 & 31) + temp.MAP1[c1 >> 5]]]
      else:
        charclass = 0

      state = code
      i0 = (charclass << 4) + code - 1
      code = temp.TRANSITION[(i0 & 3) + temp.TRANSITION[i0 >> 2]]
      if code > 15:
        result = code
        code &= 15
        self.end = current

    result >>= 4
    if result == 0:
      self.end = current - 1
      return self.error(self.begin, self.end, state, -1, -1)

    if self.end > self.size:
      self.end = self.size
    return (result & 127) - 1

  @staticmethod
  def getTokenSet(tokenSetId):
    if tokenSetId < 0:
      s = - tokenSetId
    else:
      s = temp.INITIAL[tokenSetId] & 15
    tokenSet = []
    size = 0
    for i in range(0, 79, 32):
      j = i
      i0 = (i >> 5) * 12 + s - 1
      f = temp.EXPECTED[i0]
      while f != 0:
        if (f & 1) != 0:
          tokenSet.append(temp.TOKEN[j])
          size += 1
        j += 1
        f >>= 1
    return tokenSet

  MAP0 = [                                                                                                         #   0
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, #  37
    0, 76, 0, 0, 0, 1, 2, 3, 4, 0, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 0, 16, 17, 0, 18, 0, 0, 19, 20, 21, 22,  #  69
    23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 0, 45, 0, 46, 47, 0,   #  97
    48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 0, 74, # 125
    0, 75, 0]

  MAP1 = [                                                                                                         #   0
    54, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58,    #  27
    58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58, 58,    #  54
    153, 179, 90, 122, 153, 153, 153, 153, 153, 153, 153, 153, 153, 153, 153, 153, 153, 153, 153, 153, 153, 153,   #  76
    153, 153, 153, 153, 153, 153, 153, 153, 153, 153, 153, 153, 153, 153, 0, 19, 20, 21, 22, 23, 24, 25, 26, 27,   # 100
    28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 0, 45, 0, 46, 47, 0, 48, 49, 50, 51, 52,   # 128
    53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 0, 74, 0, 75, 0, 0, 0, 0,  # 157
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 76, 0, 0, 0, 1, 2, 3, 4,   # 193
    0, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 0, 16, 17, 0, 18, 0]

  INITIAL = [                                                                                                      #   0
    1, 2, 3, 4, 5, 38, 7, 39, 8]

  TRANSITION = [                                                                                                   #   0
    309, 309, 309, 309, 309, 308, 314, 309, 309, 320, 309, 309, 325, 309, 309, 309, 330, 331, 309, 309, 309, 335,  #  22
    309, 309, 309, 340, 309, 309, 310, 344, 309, 309, 321, 348, 309, 309, 326, 352, 309, 309, 336, 356, 309, 309,  #  44
    381, 360, 309, 309, 393, 364, 309, 309, 498, 368, 309, 309, 563, 372, 309, 309, 616, 376, 309, 309, 622, 309,  #  66
    309, 309, 309, 380, 385, 309, 309, 392, 627, 309, 309, 388, 309, 309, 309, 397, 309, 309, 309, 401, 309, 309,  #  88
    309, 405, 309, 309, 309, 409, 309, 309, 309, 413, 309, 309, 309, 417, 309, 309, 309, 421, 309, 309, 309, 425,  # 110
    309, 309, 309, 429, 309, 309, 309, 433, 309, 309, 309, 437, 309, 309, 309, 441, 309, 309, 309, 445, 309, 309,  # 132
    309, 449, 309, 309, 309, 453, 309, 309, 309, 457, 309, 309, 309, 461, 309, 309, 309, 465, 309, 309, 309, 469,  # 154
    309, 309, 309, 473, 309, 309, 309, 477, 309, 309, 309, 481, 309, 309, 309, 485, 309, 309, 309, 489, 309, 309,  # 176
    309, 493, 309, 309, 316, 309, 309, 309, 309, 497, 309, 309, 309, 502, 309, 309, 309, 506, 309, 309, 309, 510,  # 198
    309, 309, 309, 514, 309, 309, 309, 518, 309, 309, 309, 522, 309, 309, 309, 526, 309, 309, 309, 530, 309, 309,  # 220
    309, 534, 309, 309, 309, 538, 309, 309, 309, 542, 309, 309, 309, 546, 309, 309, 309, 550, 309, 309, 309, 554,  # 242
    309, 309, 309, 558, 562, 309, 309, 567, 309, 309, 309, 571, 309, 309, 309, 575, 309, 309, 309, 579, 309, 309,  # 264
    309, 583, 309, 309, 309, 587, 309, 309, 309, 591, 309, 309, 309, 595, 309, 309, 309, 599, 309, 309, 309, 603,  # 286
    309, 309, 309, 607, 309, 309, 309, 611, 309, 309, 309, 615, 309, 309, 620, 309, 309, 309, 309, 626, 309, 309,  # 308
    74, 0, 0, 0, 0, 176, 0, 80, 0, 0, 9, 0, 96, 0, 0, 0, 192, 112, 0, 0, 0, 208, 0, 128, 0, 0, 128, 144, 0, 0, 0,  # 339
    224, 0, 160, 0, 160, 0, 176, 0, 176, 0, 192, 0, 192, 0, 208, 0, 208, 0, 224, 0, 224, 0, 240, 0, 240, 0, 256,   # 366
    0, 256, 0, 272, 0, 272, 0, 288, 0, 288, 0, 304, 0, 304, 11, 0, 0, 0, 240, 0, 0, 336, 0, 0, 368, 368, 12, 0, 0, # 395
    0, 256, 0, 0, 384, 384, 0, 0, 400, 400, 0, 0, 416, 416, 0, 0, 432, 432, 0, 0, 448, 448, 0, 0, 464, 464, 0, 0,  # 423
    480, 480, 0, 0, 496, 496, 0, 0, 512, 512, 0, 0, 528, 528, 0, 0, 544, 544, 0, 0, 560, 560, 0, 0, 576, 576, 0,   # 450
    0, 592, 592, 0, 0, 608, 608, 0, 0, 624, 624, 0, 0, 640, 640, 0, 0, 656, 656, 0, 0, 672, 672, 0, 0, 688, 688,   # 477
    0, 0, 704, 704, 0, 0, 720, 720, 0, 0, 736, 736, 0, 0, 752, 752, 0, 0, 768, 768, 800, 0, 0, 0, 272, 0, 0, 816,  # 505
    816, 0, 0, 832, 832, 0, 0, 848, 848, 0, 0, 864, 864, 0, 0, 880, 880, 0, 0, 896, 896, 0, 0, 912, 912, 0, 0,     # 532
    928, 928, 0, 0, 944, 944, 0, 0, 960, 960, 0, 0, 976, 976, 0, 0, 992, 992, 0, 0, 1008, 1008, 0, 0, 1024, 1024,  # 558
    0, 0, 1040, 1040, 784, 0, 0, 0, 288, 0, 0, 1056, 1056, 0, 0, 1072, 1072, 0, 0, 1088, 1088, 0, 0, 1104, 1104,   # 583
    0, 0, 1120, 1120, 0, 0, 1136, 1136, 0, 0, 1152, 1152, 0, 0, 1168, 1168, 0, 0, 1184, 1184, 0, 0, 1200, 1200, 0, # 608
    0, 1216, 1216, 0, 0, 1232, 1232, 1248, 0, 0, 0, 304, 0, 1264, 0, 0, 320, 0, 48, 0, 0, 0, 352]

  EXPECTED = [                                                                                                     #   0
    64, 128, 524288, 523264, 3146172, 523776, -4194304, -3670400, 0, 16, 1048576, 2097152, 0, 0, 65536, 0, 131072, #  17
    0, -196609, -196609, 65536, 0, 0, 0, 0, 16384, 0, 0, 8192, 0, 8191, 8191, 0, 0, 0, 0]

  TOKEN = [
      "(0)",
      "END",
      "'&'",
      "'*'",
      "'**'",
      "'+'",
      "','",
      "'-'",
      "'/'",
      "'0'",
      "'1'",
      "'2'",
      "'3'",
      "'4'",
      "'5'",
      "'6'",
      "'7'",
      "'8'",
      "'9'",
      "';'",
      "'<<'",
      "'>>'",
      "'A'",
      "'B'",
      "'C'",
      "'D'",
      "'E'",
      "'F'",
      "'G'",
      "'H'",
      "'I'",
      "'J'",
      "'K'",
      "'L'",
      "'M'",
      "'N'",
      "'O'",
      "'P'",
      "'Q'",
      "'R'",
      "'S'",
      "'T'",
      "'U'",
      "'V'",
      "'W'",
      "'X'",
      "'Y'",
      "'Z'",
      "'\\n'",
      "'^'",
      "'_'",
      "'a'",
      "'b'",
      "'c'",
      "'d'",
      "'e'",
      "'f'",
      "'g'",
      "'h'",
      "'i'",
      "'j'",
      "'k'",
      "'l'",
      "'m'",
      "'n'",
      "'o'",
      "'p'",
      "'q'",
      "'r'",
      "'s'",
      "'t'",
      "'u'",
      "'v'",
      "'w'",
      "'x'",
      "'y'",
      "'z'",
      "'|'",
      "'~'"]

def read(arg):
  if arg.startswith("{") and arg.endswith("}"):
    return arg[1:len(arg) - 1]
  else:
    with open(arg, "r", encoding="utf-8") as file:
      content = file.read()
    if len(content) > 0 and content[0] == "\ufeff":
      content = content[1:]
    return content

def main(args):
  if len(args) < 2:
    sys.stderr.write("Usage: python temp.py [-i] INPUT...\n")
    sys.stderr.write("\n")
    sys.stderr.write("  parse INPUT, which is either a filename or literal text enclosed in curly braces\n")
    sys.stderr.write("\n")
    sys.stderr.write("  Option:\n")
    sys.stderr.write("    -i     indented parse tree\n")
  else:
    indent = False
    for arg in args[1:]:
      if arg == "-i":
        indent = True
        continue
      s = temp.XmlSerializer()
      s.indent = indent
      inputString = read(arg)
      parser = temp(inputString, s)
      try:
        parser.parse_result()
      except temp.ParseException as pe:
        raise Exception ("ParseException while processing " + arg + ":\n" + parser.getErrorMessage(pe)) from pe

if __name__ == '__main__':
  sys.exit(main(sys.argv))

# End
