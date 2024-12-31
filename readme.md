# Conlog

_Winner of the “Busy Beaver / Paid by the Paren”, “Elm Award”, “Rock and a
Hard Place”, “‘Self-Documenting’”, and “Pitchdrop Experiment” awards from
[Quirky Languages Done Quick](https://quirkylanguages.com/)!_

Every Conlog program has three parts:
- variables
- initial values
- an undirected graph of operations
The undirected graph must contain one start node and one end node.

The interpreter finds a path from the start node to the end node (which may
include cycles), along with initial values for any variables that did not have
their initial values specified, so that composing the operations along the path
maps every variable to zero.

Here the graph is a chain and `x` is not given an initial value:
```
(Start)...(x-=1)...(End)
```
```
> initial--A[x-=1]--final
> go
x uninitialized and assumed free
satisfiable
x = 1
```

We can give it an initial value other than 1, which renders the problem
unsatisfiable:
```
> x=2
> go
unsatisfiable
```

Conlog programs can be written in a graphical format (`.cla` files)
or a dot-like textual format (`.clt` files).

The `-=` operation decrements the lefthand side by the righthand side
(and, similarly, the `+=` operation increments the lefthand side).

The `unipr=` operation prints its argument by decoding it as a Unicode scalar
value and the `intpr=` operations prints its argument as a decimal number.
The output tokens are printed in the order they are traversed in the solution;
here’s an example:
```
8593 is U+2191 UPWARDS ARROW ↑
8595 is U+2193 DOWNWARDS ARROW ↓

(Start)─┬──────────────────(Unipr=8593)─────────────────┬─(End)
        │                                               │
        └─(Unipr=8595)───(Intpr=x)───(x-=1)───(Intpr=x)─┘

[x=2]
```
```
> initial--A--B[unipr=8593]--C--final
> A--D[unipr=8595]--E[intpr=x]--F[x-=1]--G[intpr=x]--C--final
> go
x uninitialized and assumed free
satisfiable
x = 0
↑

> x=1
> go
satisfiable
↓ 1 0

> x=2
> go
satisfiable
↓ 2 1 ↑ ↓ 1 0

> x=?
> go
satisfiable
x = 0
↑
```
Notice that when we add the constraint `x=2` (setting the initial value of `x`)
the solution requires traversing the loop twice (`↓ 2 1` through the lower
branch, `↑` through the upper branch “backwards”, and `↓ 1 0` through the lower
branch again).

Conlog can also return additional solutions (if there are any):
```
> go all
satisfiable
x = 0
↑

or x = 1
↓ 1 0

or x = 1
↑ 1 0 ↓ ↑

or x = 2
↓ 2 1 ↑ ↓ 1 0

or x = 2
↑ 2 1 ↓ ↑ 1 0 ↓ ↑

or x = 3
↓ 3 2 ↑ ↓ 2 1 ↑ ↓ 1 0

or x = 3
↑ 3 2 ↓ ↑ 2 1 ↓ ↑ 1 0 ↓ ↑

...
```

There is also the `++?` operation, which increments the lefthand side if the
righthand side is positive (greater than zero).

We can use this to construct a gadget, the “diode”, that forces traversal in
a single direction:
```
               [e=0]    [d=0]    <- these are initial values
           _                             _
          |                               |
(Start)---+---(e-=1)---(d++?e)---(e+=1)---+---(End)
          |_                             _|
```
```
> initial--A[e-=1]--B[d++?e]--C[e+=1]--final
> d = 0
> e = 0
> go
satisfiable
```
Traversed from left to right, `e` becomes −1, `d` is not incremented and remains
zero, and then `e` is restored to zero (by incrementing it), and so the final
values of both `d` and `e` are zero, as required.

If we flip the initial and final nodes, this becomes unsatisfiable:
```
> reset
> initial--C[e+=1]--B[d++?e]--A[e-=1]--final
> // or equivalently
> //   final--A[e-=1]--B[d++?e]--C[e+=1]--initial
> d = 0
> e = 0
> go
unsatisfiable
```
Here, `e` becomes +1, `d` _is_ incremented and becomes +1 because `e` is
positive, and then `e` is restored to zero. Since the final value of `d`
is non-zero, the diode cannot be traversed in this direction.

With a bit of work, we can now perform multiplication:
```
Computes c = a × b.

(Start)>>>*<<<( e0+=1 )<<<( d0++?e0 )<<<( e0-=1 )<<<*>>>*   [a = 8]
          v                                         ^   v   [b = 7]
          v                                         ^   v   [c = ?]
          *>>>( c-=a )>>>( b-=1 )>>>>>>>>>>>>>>>>>>>*   v
                                                        v
          We subtract a from the product b times...     v   [d0 = 0]
                                                        v   [e0 = 0]
                                                        v   [d1 = 0]
          *<<<( e1+=1 )<<<( d1++?e1 )<<<( e1 -= 1 )<<<<<*   [e1 = 0]
          v
          v
          *>>>*<><><><><><><>*>>>(End)
              v              ^
              v              ^
              *>>>( a-=1 )>>>*

           ...and then drain a.
```
```
$ python -m conlog examples/multiplication.cla
c = 56
```
```
$ python -m conlog -i examples/multiplication.cla
> go
satisfiable
c = 56

> a = 3
> vars
a = 3
b = 7
c = free
d0 = 0
d1 = 0
e0 = 0
e1 = 0

> go
satisfiable
c = 21
```

With a bit _more_ work, we can even compute hailstone sequences_!_
```
[x=3]                       [y=0]     [e=0]                          [xd2=0]                         [nmx=0]
[d=0]                       save x    diode                          take x/2                        x mod 2 is nonnegative

(init)----+----(intpr=x)----(y+=x)----(e-=1)----(d++?e)----(e+=1)----+----(x-=2)----(xd2+=1)----+----(nmx-=x)----(d++?nmx)----(nmx+=x)----+
          |                                                          |                          |                                         |
          |                                                          +--------------------------+                                         |
          |                                                                                                                               |
          |                                                                                                                               |
          |                           +---------------------------------------------------------------------------------------------------+
          |                           |
          |                           |
          |                           |    x mod 2 is 0...      ...so we set x <- x/2        reset y             reset xd2    diode
          |                           |
          |                           +----(d++?x)--------------(x+=xd2)---------------------(y-=x)----(y-=x)----(xd2-=x)-----(e-=1)----(d++?e)----(e+=1)----+
          |                           |                                                                                                                      |
          |                           |                                                                                                                      |
          |                           |    x mod 2 is 1...                ...so we set x <- 3x+1 by adding 3x to x mod 2                                     |
          |                           |                                                                                                                      |
          |                           +----(x-=1)----(d++?x)----(x+=1)----(x+=y)----(x+=y)----(x+=y)----+                                                    |
          |                                                                                             |                                                    |
          |                                                                                             |                                                    |
          |                                +------------------------------------------------------------+                                                    |
          |                                |                                                                                                                 |
          |                                |                                                                                                                 |
          |                                |    reset y                                                                                                      |
          |                                |                                                                                                                 |
          |                                +----(y-=xd2)----(y-=xd2)----(y-=1)----+                                                                          |
          |                                                                       |                                                                          |
          |                                                                       |                                                                          |
          |                                +--------------------------------------+                                                                          |
          |                                |                                                                                                                 |
          |                                |                                                                                                                 |
          |                                |    diode to...                    ...reset xd2...       ...to zero                                              |
          |                                |                                                                                                                 |
          |                                +----(e-=1)----(d++?e)----(e+=1)----+----------------+----(d++?xd2)----(e-=xd2)----(d++?e)----(e+=xd2)----+       |
          |                                                                    |                |                                                    |       |
          |                                                                    +----(xd2-=1)----+                                                    |       |
          |                                                                                                                                          |       |
          |                           +--------------------------------------------------------------------------------------------------------------+-------+
          |                           |
          |                           |    [s=?]
          |                           |    we've taken one step      x=1, so we're done!
          |                           |
          |                           +----(s-=1)---------------+----(intpr=x)----(x-=1)----(fin)
          |                                                     |
          |                                                     |
          |                      x!=1 so we need to go again    |
          |                                                     |
          +-----------------------------------------------------+
```
```
$ python -m conlog -i examples/collatz.cla 
> go
satisfiable
s = 7
3 10 5 16 8 4 2 1
```

For more information, type `help` in the interactive prompt:
```
> help
strategy            print the current strategy
strategy c|g|p      set the strategy to c, g, or p
limit               print the current search limit
limit <num>         set the search limit to <num>
go|search|solve     solve the current graph
go|... all          find all solutions
reset|clear         reset the current graph
<name>              print the definition of <name>
vars                print the definitions of all variables
nodes               print the definitions of all nodes
show|plot           render the current graph
exit|quit           exit the interpreter
CTRL-C              halt the ongoing search
```
