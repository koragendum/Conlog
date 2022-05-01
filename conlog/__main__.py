from conlog.evaluator    import evaluate
from conlog.frontends    import FrontendError, TokenStream, TextProgram
from conlog.solver_astar import solve_graph_bfs

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

while True:
    seq = stream.readline()
    if isinstance(seq, FrontendError):
        log_lines = stream.log.split('\n')
        seq.show(log_lines)
        continue
    if len(seq) == 0:
        continue

    if len(seq) < 3 and seq[0].kind == 'name' and seq[0].value in ('solve', 'go'):
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
        if strategy == 'g':
            solve_result = solve_graph_bfs(graph)
            if solve_result is None:
                print('unsatisfiable')
                continue
            answer, path = solve_result
            solution = evaluate([x.node for x in path], answer.values)
            for (name, value) in solution.assignment.items():
                if program.variables[name] in ('free', None):
                    print(f"\x1B[95m{name}\x1B[39m = \x1B[95m{value}\x1B[39m")
            nodes = [f"\x1B[94m{node.name}\x1B[39m" for node in solution.path]
            print(' -- '.join(nodes))

    if len(seq) < 3 and seq[0].kind == 'name' and seq[0].value == 'strategy':
        if len(seq) == 1:
            print(f"strategy is \x1B[93m{strategy}\x1B[39m")
        else:
            if seq[1].kind != 'name' or seq[1].value not in ('g', 'p'):
                log_lines = stream.log.split('\n')
                FrontendError("unknown strategy", seq).show(log_lines)
            else:
                strategy = seq[1].value
        continue

    if len(seq) == 1 and seq[0].kind == 'name' and seq[0].value == 'clear':
        program = TextProgram()

    if len(seq) == 1 and seq[0].kind == 'name':
        program.show(seq[0].value)
        continue

    result = program.add_statement(seq, allow_reinit=True)
    if isinstance(result, FrontendError):
        log_lines = stream.log.split('\n')
        result.show(log_lines)
        continue
