from conlog.datatypes import Operation, Initial, Terminal, Addition, Print, Subtraction, Node, Graph


"""
Graph that computes either T=triangle_sum(x) or T=triangle_sum(x-1)
depending on the first path taken. (no one-way gadget used)

    Initial----------------None---DecrF---Terminal
       |                    |
       '--DecrX----SubFbyX--'

"""
either_trisum_d = {
    'initial': Node(Initial(free=('T',), fixed=(('n', '4'),))),
    'decr_x': Node(Subtraction('n', '1')),
    'sub_t_x': Node(Subtraction('T', 'n')),
    'none': Node(None),
    'decr_t': Node(Subtraction('T', '1')),
    'terminal': Node(Terminal()),
}

either_trisum_graph = Graph(
    nodes=list(either_trisum_d.values()),
    edges=[
        (either_trisum_d['initial'], either_trisum_d['decr_x']),
        (either_trisum_d['decr_x'], either_trisum_d['sub_t_x']),
        (either_trisum_d['sub_t_x'], either_trisum_d['none']),
        (either_trisum_d['none'], either_trisum_d['initial']),
        (either_trisum_d['none'], either_trisum_d['decr_t']),
        (either_trisum_d['decr_t'], either_trisum_d['terminal']),
    ],
)

print(either_trisum_graph)

