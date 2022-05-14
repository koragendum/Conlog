// Solve the conlog grid using BFS --  C

#include <stdint.h>

#define MAX_DEGREE 16
#define MAX_QUEUE_LENGTH 110000000


#define Initial 1
#define Terminal 2
#define Addition 3
#define IntegerPrint 4
#define UnicodePrint 5
#define Subtraction 6
#define ConditionalIncrement 7
#define ConditionalDecrement 8
#define NoneType 9


typedef struct CNode {
    uint8_t node_type;
    uint64_t node_i;
    int64_t lhs;  // Index of the lhs operand
    uint8_t rhs_is_constant;  // (bool) Whether rhs is a constant or an index
    int64_t rhs;  // Index/value of the rhs operand
    uint8_t num_neighbors;  // Number of neighbors of this node
    struct CNode * neighbor_arr[MAX_DEGREE];  // (Yes, a POINTER ARRAY)
} CNode;


typedef struct CSearchState {
    CNode * node;
    int64_t * values;
    struct CSearchState * parent_search_state;
} CSearchState;


typedef struct CSearchWorkspace {
    CSearchState search_queue[MAX_QUEUE_LENGTH];
    CSearchState * search_queue_next_free;  // Add things via: *search_queue_next_free = thing; search_queue_next_free++
    CSearchState * search_queue_next_to_pop;  // Add things via: thing = *search_queue_next_to_pop; search_queue_next_to_pop++
    CNode * node_arr;  // CNode[num_nodes]
    uint64_t num_values;  // Number of values of the graph
    uint64_t num_free_values;  // Number of free values of the graph
    uint64_t num_fixed_values;  // Number of fixed values of the graph
    int64_t * fixed_values;  // int64_t[num_fixed_values]  The values themselves
    CNode * terminal_node;  // CNode *
    uint64_t iterations;
    uint64_t limit;
    int64_t * lower_bounds;
    int64_t * upper_bounds;
} CSearchWorkspace;

