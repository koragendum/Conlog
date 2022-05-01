import re

#~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
# Text frontend (similar to DOT)
#
#   node = node-name ("[" var-name ("+=" | "-=") (var-name | const) "]")?
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

COMMENT  = '//'
GRP_SEPR = '\''
SYMBOLS  = [';', '[', ']', '=', '?', '+=', '-=', '--']

ws_regex   = re.compile(r"[ \n\r]+")
name_regex = re.compile(r"[a-zA-Z][a-zA-Z0-9]*'?")
num_regex  = re.compile(r"\d+("+re.escape(GRP_SEPR)+r"\d+)*")
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
            if (prefix := self.text[:2]) in SYMBOLS or (prefix := self.text[:1]) in SYMBOLS:
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
            return FrontendError("unable to tokenize", [err_tok])


class TextProgram:
    def __init__(self):
        self.unknown   = set()
        self.variables = dict() # name -> initial value
        self.nodes     = dict() # name -> operation
        self.edges     = set()  # (name, name)


    def add_node(self, seq):
        """
        Returns (number of tokens consumed, node name) or instance of FrontendError.
        seq -- nonempty list of Tokens
        """
        if seq[0].kind != 'name':
            return FrontendError("expected node name", seq[0])

        node_name = seq[0].value
        if node_name in self.variables:
            return FrontendError("variable with this name already exists", seq[0])

        if len(seq) == 1 or not (seq[1].kind == 'symbol' and seq[1].value == '['):
            if node_name in self.unknown:
                self.unknown.remove(node_name)
            if node_name not in self.nodes:
                self.nodes[node_name] = None
            return (1, node_name)

        if len(seq) < 6:
            return FrontendError("incomplete node definition", seq)

        if seq[2].kind != 'name':
            return FrontendError("expected variable name", seq[2])

        if not (seq[3].kind == 'symbol' and seq[3].value in ('+=', '-=')):
            return FrontendError("expected increment or decrement", seq[3])

        if seq[4].kind not in ('numeric', 'character', 'name'):
            return FrontendError("expected literal or variable name", seq[5])

        if not (seq[5].kind == 'symbol' and seq[5].value == ']'):
            return FrontendError("expected a closing bracket", seq[5])

        if seq[2].value in self.nodes or seq[2].value == node_name:
            return FrontendError("label refers to an existing node", seq[2])

        if seq[4].kind == 'name' and (seq[4].value in self.nodes or seq[4].value == node_name):
            return FrontendError("label refers to an existing node", seq[4])

        if node_name in self.nodes and self.nodes[node_name] is not None:
            return FrontendError("node mutation has already been defined", seq[1:6])

        lhs = seq[2].value
        if lhs in self.unknown:
            self.unknown.remove(lhs)
        if lhs not in self.variables:
            self.variables[lhs] = None

        if seq[4].kind == 'name':
            rhs_name = seq[4].value
            if rhs_name in self.unknown:
                self.unknown.remove(seq[4].value)
            if rhs_name not in self.variables:
                self.variables[rhs_name] = None

        if seq[4].kind == 'numeric':
            rhs = seq[4].value
        elif seq[4].kind == 'character':
            rhs = ord(seq[4].value)
        else:
            rhs = seq[4].value

        op = {'+=': 'inc', '-=': 'dec'}[seq[3].value]

        if node_name in self.unknown:
            self.unknown.remove(node_name)

        self.nodes[node_name] = (lhs, op, rhs)

        return (6, node_name)


    def add_statement(self, seq):
        """
        Returns None or instance of FrontendError.
        seq -- nonempty list of Tokens
        """
        if seq[0].kind != 'name':
            return FrontendError("statement must begin with a name", seq[0])

        # Simple declaration
        name = seq[0].value
        if len(seq) == 1:
            if name not in self.variables and name not in self.nodes:
                self.unknown.add(name)
            return

        # Variable initialization
        if seq[1].kind == 'symbol' and seq[1].value == '=':
            if len(seq) < 3:
                return FrontendError("incomplete variable initialization", seq)
            is_literal = seq[2].kind in ('numeric', 'character')
            is_free    = seq[2].kind == 'symbol' and seq[2].value == '?'
            if not (is_literal or is_free):
                return FrontendError("variable must be initialized to a constant or marked free", seq[2])
            if len(seq) > 3:
                return FrontendError("extraneous characters in variable intialization", seq[3:])
            if name in self.nodes:
                return FrontendError("node with this label already exists", seq[0])
            if name in self.variables:
                if self.variables[name] is not None:
                    return FrontendError("variable has already been initialized", seq[0])
            if name in self.unknown:
                self.unknown.remove(name)
            if is_free:
                self.variables[name] = None
            elif seq[2].kind == 'character':
                self.variables[name] = ord(seq[2].value)
            else:
                self.variables[name] = seq[2].value
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

    def validate(self):
        """
        Checks whether there are unused variables, whether there are initial and final nodes.
        """
        return None


if __name__ == '__main__':

    def readline(stream):
        buf = []
        while True:
            tok = next(stream)
            if isinstance(tok, FrontendError):
                return tok
            if tok is None:
                return None if len(buf) == 0 else buf
            if tok.kind == 'symbol' and tok.value == ';':
                return buf
            buf.append(tok)

    def prompt():
        print("\x1B[2mconlog:\x1B[22m", end=' ')
        line = input()
        if line in ['exit', 'quit']:
            exit()
        return line + "\n"

    stream = TokenStream("", prompt)
    program = TextProgram()

    while True:
        seq = readline(stream)
        if isinstance(seq, FrontendError):
            log_lines = stream.log.split('\n')
            seq.show(log_lines)
            stream.text = ""
            continue
        result = program.add_statement(seq)
        if isinstance(result, FrontendError):
            log_lines = stream.log.split('\n')
            result.show(log_lines)
        print('Unk:   ', program.unknown)
        print('Vars:  ', program.variables)
        print('Nodes: ', program.nodes)
        print('Edges: ', program.edges)
