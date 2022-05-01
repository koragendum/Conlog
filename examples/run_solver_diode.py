from conlog.evaluator import evaluate
from conlog.frontends import GridError, convert_to_grid, make_grid_program
from conlog.solver    import solve_graph_bfs


test1 = """

    (Start)----##(y-=1)##(z++?y)##(y+=1)#####---(y-=1)--(End)
    [y=1]
    [z=0]

"""


test2 = """

    (Start)----##(y-=1)##(z++?y)##(y+=1)#####---(y-=1)--(End)
    [z=0]      |                            |
    [n=6]      |                            |
    [y=1]   (n-=1)                          |
    [T=?]      |                            |
               +-------(T-=n)---------------+

"""


for test in [test1, test2]:
    grid = convert_to_grid(test)
    if isinstance(grid, GridError):
        grid.show()
    program = make_grid_program(grid)
    if isinstance(program, GridError):
        program.show(grid)
        exit()
    for line in grid:
        print(line)
    print('\x1B[1mNodes\x1B[22m')
    program.show('nodes')
    print('\x1B[1mVariables\x1B[22m')
    program.show('vars')

    graph = program.graph()
    solve_result = solve_graph_bfs(graph)
    if solve_result is None:
        print('unsatisfiable')
        exit()

    print('\x1B[1mSolution\x1B[22m')
    answer, path = solve_result
    solution = evaluate([x.node for x in path], answer.values)
    for (name, value) in solution.assignment.items():
        if program.variables[name] in ('free', None):
            print(f"\x1B[95m{name}\x1B[39m = \x1B[95m{value}\x1B[39m")
