import re
import networkx
from conlog.datatypes import (
    Initial,
    Terminal,
    Addition,
    Subtraction,
    ConditionalIncrement,
    Node,
)

DISALLOW_SELF_MUTATION = True

#~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
# Text frontend (similar to DOT)
#
#   node = node-name ("[" var-name ("+=" | "-=") (var-name | const) "]")?
#        | node-name "[" "print" "]"
#
#   statement = var-name "=" (const | "?")
#             | node ("--" node)+
#
#   program = statement (";" statement)* ";"?
#
#   Variables that are not explicitly set to a constant or "?" are implictly
#   left free. Nodes that are never declared are assumed to be None nodes.
#
#   There are two special node names: "initial" and "final".

COMMENT   = '//'
GRP_SEPR  = '\''
OPERATORS = ['+=', '-=', '++?']
SYMBOLS   = [';', '[', ']', '=', '?', '--'] + OPERATORS

ws_regex   = re.compile(r"[ \n\r]+")
name_regex = re.compile(r"[a-zA-Z][a-zA-Z0-9]*'?")
num_regex  = re.compile(r"[+-]?\d+("+re.escape(GRP_SEPR)+r"\d+)*")
char_regex = re.compile(r"'.")

# The token kinds are "numeric", "character", "symbol", and "name".
class Token:
    def __init__(self, text, value, kind, line, column):
        self.text   = text
        self.value  = value
        self.kind   = kind
        self.line   = line
        self.column = column

    def __repr__(self):
        tk = "\x1B[38;5;42mToken\x1B[39m"
        if self.value is None:
            return f"{tk} : {self.kind} @ {self.line},{self.column}"
        value = repr(self.value) if self.kind == 'string' else self.value
        return f"{tk} {value} : {self.kind} @ {self.line},{self.column}"


def extract_tokens(obj):
    if isinstance(obj, Token):
        return [obj]
    if isinstance(obj, (list, tuple)):
        return sum((extract_tokens(x) for x in obj), [])
    raise RuntimeError(f"unable to extract tokens from {type(obj)}")


class FrontendError:
    def __init__(self, msg, hi):
        """
        msg -- string describing the failure
        hi  -- token or parse tree
        """
        self.message = msg
        self.highlight = hi

    def __repr__(self):
        return f"\x1B[91merror\x1B[39m: {self.message}"

    def show(self, log_lines):
        """
        log_lines -- a copy of the text (prior to tokenization) split into lines
        """
        if self.highlight is None:
            print(f"\x1B[91merror\x1B[39m: {self.message}")
            return
        tokens = extract_tokens(self.highlight)
        top = tokens[ 0].line - 1
        bot = tokens[-1].line - 1
        print(f"\x1B[91merror\x1B[39m: line {tokens[0].line}: " + self.message)
        if bot-top > 1:
            return  # not sure yet how to display multi-line errors
        line = log_lines[top]
        margin = "\x1B[2m\u2502\x1B[22m "
        print(margin)
        print(margin + line)
        print(margin, end='')
        left  = tokens[ 0].column - 1
        right = tokens[-1].column - 1 + len(tokens[-1].text)

        print(" "*left, end='')
        print("\x1B[91m^", end='')
        print("~"*(right-left-1), end='')
        print("\x1B[39m", end='')
        print()


class TokenStream:
    def __init__(self, text, more = None):
        """
        text -- text to be tokenized
        more -- nullary function that will be called to get more text
        """
        self.text   = text
        self.more   = more
        self.line   = 1
        self.column = 1
        self.log = text

    def _advance(self, string):
        newlines = string.count('\n')
        if newlines == 0:
            self.column = self.column + len(string)
        else:
            self.line = self.line + newlines
            self.column = len(string) - string.rindex('\n')

    def __next__(self):
        while True:
            # Strip leading whitespace
            match = ws_regex.match(self.text)
            if match is not None:
                tok_line, tok_column = self.line, self.column

                whitespace = match.group()
                self._advance(whitespace)
                self.text = self.text[match.end():]

            # Is the text empty?
            if len(self.text) == 0:
                if self.more is None:
                    return None
                addendum = self.more()
                self.text += addendum
                self.log  += addendum
                continue

            # Is this a comment?
            if self.text.startswith(COMMENT):
                while True:
                    if '\n' in self.text:
                        end_of_comment = self.text.index('\n')
                        self._advance(self.text[:end_of_comment])
                        self.text = self.text[end_of_comment:]
                        break
                    else:
                        self._advance(self.text)
                        self.text = ""
                        if self.more is None:
                            return None
                        addendum = self.more()
                        self.text += addendum
                        self.log  += addendum
                continue

            tok_line, tok_column = self.line, self.column

            # Is this a symbol?
            if (prefix := self.text[:3]) in SYMBOLS \
            or (prefix := self.text[:2]) in SYMBOLS \
            or (prefix := self.text[:1]) in SYMBOLS:
                self._advance(prefix)
                self.text = self.text[len(prefix):]
                return Token(prefix, prefix, 'symbol', tok_line, tok_column)

            # Is this a name?
            match = name_regex.match(self.text)
            if match is not None:
                name_text = match.group()
                self._advance(name_text)
                self.text = self.text[match.end():]
                return Token(name_text, name_text, 'name', tok_line, tok_column)

            # Is this a number?
            match = num_regex.match(self.text)
            if match is not None:
                num_text = match.group()
                self._advance(num_text)
                self.text = self.text[match.end():]
                constant = int(num_text.replace(GRP_SEPR, ''))
                return Token(num_text, constant, 'numeric', tok_line, tok_column)

            # Is this a character?
            match = char_regex.match(self.text)
            if match is not None:
                char_text = match.group()
                self._advance(char_text)
                self.text = self.text[match.end():]
                return Token(char_text, char_text[1:], 'character', tok_line, tok_column)

            err_tok = Token(self.text[0], None, None, tok_line, tok_column)
            self._advance(self.text)
            self.text = ""
            return FrontendError("unable to tokenize", [err_tok])

    def readline(self):
        buf = []
        while True:
            tok = next(self)
            if isinstance(tok, FrontendError):
                return tok
            if tok is None:
                return buf
            if tok.kind == 'symbol' and tok.value == ';':
                return buf
            buf.append(tok)


class TextProgram:
    def __init__(self):
        self.variables = dict() # name -> initial value
        self.nodes     = dict() # name -> operation
        self.edges     = set()  # (name, name)


    def show(self, query=None):
        if query is None:
            names = sorted(set(self.variables.keys()) | set(self.nodes.keys()))
        elif query == 'vars':
            names = sorted(self.variables.keys())
        elif query == 'nodes':
            names = sorted(self.nodes.keys())
        elif isinstance(query, (list, tuple)):
            names = query
        else:
            names = [query]

        for name in names:
            if query != 'nodes' and name in self.variables:
                status = self.variables[name]
                if status is None:
                    print(f"\x1B[95m{name}\x1B[39m uninitialized")
                else:
                    print(f"\x1B[95m{name}\x1B[39m = \x1B[95m{status}\x1B[39m")
            if query != 'vars' and name in self.nodes:
                operation = self.nodes[name]
                if operation is None:
                    print(f"\x1B[94m{name}\x1B[39m", end='')
                else:
                    lhs, op, rhs = operation
                    desc = f"\x1B[95m{lhs}\x1B[39m{op}\x1B[95m{rhs}\x1B[39m"
                    print(f"\x1B[94m{name}\x1B[39m [{desc}]", end='')
                left_adjuncts  = [edge[0] for edge in self.edges if edge[1] == name]
                right_adjuncts = [edge[1] for edge in self.edges if edge[0] == name]
                adjuncts = sorted(left_adjuncts + right_adjuncts)
                if len(adjuncts) > 0:
                    print(' --', ', '.join(f"\x1B[94m{a}\x1B[39m" for a in adjuncts), end='')
                print()


    def add_node(self, seq):
        """
        Returns (number of tokens consumed, node name) or instance of FrontendError.
        seq -- nonempty list of Tokens
        """
        if seq[0].kind != 'name':
            return FrontendError("expected node name", seq[0])

        node_name = seq[0].value

        if len(seq) == 1 or not (seq[1].kind == 'symbol' and seq[1].value == '['):
            if node_name not in self.nodes:
                self.nodes[node_name] = None
            return (1, node_name)

        if len(seq) < 6:
            return FrontendError("incomplete node definition", seq)

        if node_name in ('initial', 'final'):
            return FrontendError("cannot define node operation for initial or final", seq[0])

        if seq[2].kind != 'name':
            return FrontendError("expected variable name", seq[2])

        if not (seq[3].kind == 'symbol' and seq[3].value in OPERATORS):
            return FrontendError("expected operator", seq[3])

        if seq[4].kind not in ('numeric', 'character', 'name'):
            return FrontendError("expected literal or variable name", seq[4])

        if seq[3].value == "++?" and seq[4].kind != 'name':
            return FrontendError("expected variable name", seq[4])

        if not (seq[5].kind == 'symbol' and seq[5].value == ']'):
            return FrontendError("expected a closing bracket", seq[5])

        if node_name in self.nodes and self.nodes[node_name] is not None:
            return FrontendError("node operation has already been defined", seq[1:6])

        if DISALLOW_SELF_MUTATION and seq[4].kind == 'name' and (seq[2].value == seq[4].value):
            return FrontendError("variable automutation is forbidden", [seq[2], seq[4]])

        lhs = seq[2].value
        if lhs not in self.variables:
            self.variables[lhs] = None

        if seq[4].kind == 'name':
            rhs_name = seq[4].value
            if rhs_name not in self.variables:
                self.variables[rhs_name] = None

        if seq[4].kind == 'numeric':
            rhs = seq[4].value
        elif seq[4].kind == 'character':
            rhs = ord(seq[4].value)
        else:
            rhs = seq[4].value

        op = seq[3].value
        self.nodes[node_name] = (lhs, op, rhs)
        return (6, node_name)


    def add_statement(self, seq, allow_reinit=False) -> None:
        """
        Returns None or instance of FrontendError.
        seq -- nonempty list of Tokens
        """
        if seq[0].kind != 'name':
            return FrontendError("statement must begin with a name", seq[0])

        name = seq[0].value
        if len(seq) < 3:
            return FrontendError("incomplete statement", seq)

        # Variable initialization
        if seq[1].kind == 'symbol' and seq[1].value == '=':
            if len(seq) < 3:
                return FrontendError("incomplete variable initialization", seq)
            if len(seq) > 3:
                return FrontendError("extraneous characters in variable intialization", seq[3:])
            is_literal = seq[2].kind in ('numeric', 'character')
            is_free    = seq[2].kind == 'symbol' and seq[2].value == '?'
            if not (is_literal or is_free):
                return FrontendError("variable must be initialized to a constant or marked free", seq[2])
            if not allow_reinit and name in self.variables:
                if self.variables[name] is not None:
                    return FrontendError("variable has already been initialized", seq[0])
            if is_free:
                self.variables[name] = 'free'
            elif seq[2].kind == 'numeric':
                self.variables[name] = seq[2].value
            elif seq[2].kind == 'character':
                self.variables[name] = ord(seq[2].value)
            return

        # Node and edge declarations
        index = 0
        last_node = None
        while True:
            result = self.add_node(seq[index:])
            if isinstance(result, FrontendError):
                return result

            consumed, this_node = result
            if last_node is not None:
                if this_node == last_node:
                    return FrontendError("cannot make edge from a node to itself", seq[index])
                canonical = tuple(sorted((last_node, this_node)))
                self.edges.add(canonical)
            last_node = this_node

            index += consumed
            if index >= len(seq):
                return
            if not (seq[index].kind == 'symbol' and seq[index].value == '--'):
                return FrontendError("expected edge", seq[index])
            index += 1

    def uninitialized(self) -> list[str]:
        return sorted(name for (name, constraint) in self.variables.items() if constraint is None)

    def graph(self):
        """
        Assumes initial and final nodes exist and that all variables are initialized.
        """
        graph_nodes = {}
        for (name, operation) in self.nodes.items():
            match name:
                case 'initial':
                    free = tuple(name for (name, constraint) in self.variables.items() if constraint is None or constraint == 'free')
                    fixed = tuple(var for var in self.variables.items() if isinstance(var[1], int))
                    graph_nodes[name] = Node('initial', Initial(free=free, fixed=fixed))
                case 'final':
                    graph_nodes[name] = Node('final', Terminal())
                case _:
                    if operation is None:
                        graph_nodes[name] = Node(name, None)
                    else:
                        lhs, op, rhs = operation
                        match op:
                            case '+=':
                                graph_op = Addition(lhs, rhs)
                            case '-=':
                                graph_op = Subtraction(lhs, rhs)
                            case '++?':
                                graph_op = ConditionalIncrement(lhs, rhs)
                            case _:
                                raise Exception(f"unknown operation {op}")
                        graph_nodes[name] = Node(name, graph_op)

        graph = networkx.Graph()
        graph.add_edges_from([(graph_nodes[n1], graph_nodes[n2]) for (n1, n2) in self.edges])
        return graph


#~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
# ASCII graph frontend
#
# TODO
