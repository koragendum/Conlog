from conlog.brute     import interpret
from conlog.evaluator import evaluate
from conlog.frontends import FrontendError, TokenStream, TextProgram
from conlog.solver    import solve_graph_bfs

AUTO_SEMICOLON = True

#~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
# Read from file

#~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
# Interactive prompt

def prompt():
    print("\x1B[2mconlog:\x1B[22m", end=' ')
    try:
        line = input()
    except KeyboardInterrupt:
        print()
        exit()
    except EOFError:
        print('^D')
        exit()
    if line in ['exit', 'quit', ':q']:
        exit()
    if AUTO_SEMICOLON:
        stripped = line.rstrip()
        if len(stripped) > 0 and stripped[-1] != ';':
            line += ';'
    return line + '\n'

stream = TokenStream("", prompt)
program = TextProgram()
strategy = 'g'
limit = 65536

while True:
    seq = stream.readline()
    if isinstance(seq, FrontendError):
        log_lines = stream.log.split('\n')
        seq.show(log_lines)
        continue
    if len(seq) == 0:
        continue

    if len(seq) < 3 and seq[0].kind == 'name' and seq[0].value == 'strategy':
        if len(seq) == 1:
            print(f"strategy is \x1B[93m{strategy}\x1B[39m")
        else:
            if seq[1].kind != 'name' or seq[1].value not in ('g', 'p'):
                log_lines = stream.log.split('\n')
                FrontendError("unknown strategy", seq[1]).show(log_lines)
            else:
                strategy = seq[1].value
        continue

    if len(seq) < 3 and seq[0].kind == 'name' and seq[0].value == 'limit':
        if len(seq) == 1:
            print(f"limit is \x1B[93m{limit}\x1B[39m")
        else:
            if seq[1].kind != 'numeric':
                log_lines = stream.log.split('\n')
                FrontendError("limit must be numeric", seq[1]).show(log_lines)
            else:
                limit = seq[1].value
        continue

    is_command = (len(seq) == 1 and seq[0].kind == 'name')

    if is_command and seq[0].value in ('solve', 'go'):
        has_initial = 'initial' in program.nodes
        has_final   = 'final'   in program.nodes
        if not (has_initial and has_final):
            if not has_initial:
                print("\x1B[91merror\x1B[39m: missing initial node")
            if not has_final:
                print("\x1B[91merror\x1B[39m: missing final node")
            continue
        uninit = program.uninitialized()
        if len(uninit) > 0:
            uninit_names = ', '.join(f"\x1B[95m{name}\x1B[39m" for name in uninit)
            print(uninit_names, "uninitialized and assumed free")

        graph = program.graph()
        try:
            if strategy == 'g':
                solve_result = solve_graph_bfs(graph, limit=limit)
                if solve_result is None:
                    print('unsatisfiable')
                    continue
                answer, path = solve_result
                solution = evaluate([x.node for x in path], answer.values)
            if strategy == 'p':
                interpreter = interpret(graph)
                solution = next(interpreter)
        except KeyboardInterrupt:
            print('\rinterrupted')
            continue
        for (name, value) in solution.assignment.items():
            if program.variables[name] in ('free', None):
                print(f"\x1B[95m{name}\x1B[39m = \x1B[95m{value}\x1B[39m")
        nodes = [f"\x1B[94m{node.name}\x1B[39m" for node in solution.path]
        if len(nodes) > 15:
            nodes = nodes[:7] + ["..."] + nodes[-7:]
        print(' -- '.join(nodes))

    if is_command and seq[0].value == 'help':
        print("strategy            print the current strategy")
        print("strategy g|p        set the strategy to g or p")
        print("limit               print the current search limit")
        print("limit <num>         set the search limit to <num>")
        print("solve|go            solve the current graph")
        print("reset|clear         reset the current graph")
        print("<name>              print the definition of <name>")
        print("vars                print the definitions of all variables")
        print("nodes               print the definitions of all nodes")
        print("exit|quit           exit the interpreter")

    if is_command and seq[0].value in ('clear', 'reset'):
        program = TextProgram()
        continue

    if is_command:
        program.show(seq[0].value)
        continue

    result = program.add_statement(seq, allow_reinit=True)
    if isinstance(result, FrontendError):
        log_lines = stream.log.split('\n')
        result.show(log_lines)
        continue
