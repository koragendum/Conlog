// Solve the conlog grid using BFS --  C

#include <stdio.h>
#include <stdlib.h>
#include "solver_c_fast.h"



static void * init_search_workspace_lowlevel(
    uint64_t num_fixed_values,
    uint64_t num_free_values,
    int64_t * fixed_values,
    uint64_t num_nodes,

    uint8_t * node_type_arr,
    int64_t * node_lhs_arr,  // Index of the lhs operand
    uint8_t * node_rhs_is_constant_arr,  // Whether rhs is a constant or an index (1 or 0)
    int64_t * node_rhs_arr,  // Index/value of the rhs operand

    uint8_t* adjacency_matrix,  // uint8_t[num_nodes * num_nodes]
    uint64_t limit,
    int64_t * lower_bounds,  // lower_bounds[num_values]
    int64_t * upper_bounds  // upper_bounds[num_values]
)
{
    //  printf("init_search_workspace_lowlevel called\n");

    CSearchWorkspace * the_workspace = malloc(sizeof(CSearchWorkspace));

    // Make the node array
    CNode * node_arr = malloc(sizeof(CNode) * num_nodes);
    for (uint64_t i=0; i < num_nodes; i++) {
        // Basics
        node_arr[i].node_type = node_type_arr[i];
        node_arr[i].node_i = i;
        node_arr[i].lhs = node_lhs_arr[i];
        node_arr[i].rhs_is_constant = node_rhs_is_constant_arr[i];
        node_arr[i].rhs = node_rhs_arr[i];
        node_arr[i].num_neighbors = 0;
    }

    for (uint64_t i=0; i < num_nodes; i++) {
        for (uint64_t j=0; j < num_nodes; j++) {
            if (adjacency_matrix[(i * num_nodes) + j]) {
                node_arr[i].neighbor_arr[node_arr[i].num_neighbors] = &(node_arr[j]);
                node_arr[i].num_neighbors ++;
                if (node_arr[i].num_neighbors >= MAX_DEGREE) {
                    printf("Degree too high\n");
                    return NULL;
                }
            }
        }
    }

    // Put the first node on the search queue; the terminal node
    uint8_t found_it = 0;
    for (uint64_t i=0; i < num_nodes; i++) {
        if (node_arr[i].node_type == Terminal) {
            found_it = 1;
            the_workspace->terminal_node = &(node_arr[i]);
        }
    }
    if (!found_it) {
        printf("Did not find terminal node\n");
        return NULL;
    }

    CSearchState first_search_state;

    first_search_state.node = the_workspace->terminal_node;
    first_search_state.last_node = NULL;
    for (uint64_t i=0; i<MAX_NUM_VALUES; i++) {
        first_search_state.values[i] = 0;
    }
    first_search_state.parent_search_state = NULL;

    the_workspace->search_queue_next_to_pop = &(the_workspace->search_queue[0]);
    the_workspace->search_queue_next_free = &(the_workspace->search_queue[0]);
    *(the_workspace->search_queue_next_free) = first_search_state;

    the_workspace->search_queue_next_free++;


    the_workspace->node_arr = node_arr;
    the_workspace->num_free_values = num_free_values;
    the_workspace->num_fixed_values = num_fixed_values;
    the_workspace->num_values = num_free_values + num_fixed_values;
    the_workspace->fixed_values = malloc(sizeof(uint64_t) * num_fixed_values);
    for (uint64_t i=0; i<num_fixed_values; i++) {
        the_workspace->fixed_values[i] = fixed_values[i];
    }
    the_workspace->iterations = 0;
    the_workspace->limit = limit;
    the_workspace->lower_bounds = lower_bounds;
    the_workspace->upper_bounds = upper_bounds;




    // // CSearchState search_queue[MAX_QUEUE_LENGTH];
    // // CNode * node_arr;
    // printf("search_queue: %lld\n", the_workspace->search_queue);
    // printf("search_queue_next_free: %lld\n", the_workspace->search_queue_next_free);
    // printf("search_queue_next_to_pop: %lld\n", the_workspace->search_queue_next_to_pop);
    // printf("num_values: %lld\n", the_workspace->num_values);
    // printf("num_free_values: %lld\n", the_workspace->num_free_values);
    // printf("num_fixed_values: %lld\n", the_workspace->num_fixed_values);
    // printf("fixed_values: %lld\n", the_workspace->fixed_values);
    // // CNode * terminal_node;;
    // printf("iterations: %lld\n", the_workspace->iterations);
    // printf("limit: %lld\n", the_workspace->limit);
    // printf("lower_bounds: %lld\n", the_workspace->lower_bounds);
    // printf("upper_bounds: %lld\n", the_workspace->upper_bounds);




    return the_workspace;
}



static uint64_t * get_next_solution_lowlevel(
    void * the_workspace_ptr  // Really it's a CSearchWorkspace * .. void* so I don't have to explain that to caller
) {
    /**
     * Doc: Returns an int64_t * ptr. It's an array of length at least 1, specced as follows:
     *
     *   [arr_size values0 values1 ... values{N-1} node_id0 node_id1 ... node_id{arr_size-1}]
     *
     * The elements are the node ids of the solution path.
     *
     * (note that it has arr_size+num_values+1 elements, if arr_size >= 0)
     *
     * If arr_size < 0, search failed. The malloc'd array is of length 1, eg.:
     *
     *   [-1]
     */

    CSearchWorkspace * the_workspace = (CSearchWorkspace *) the_workspace_ptr;

    // printf("get_next_solution_lowlevel called\n");

    CSearchState * queue_end = &(the_workspace->search_queue[MAX_QUEUE_LENGTH - MAX_DEGREE - 1]);

    uint64_t iterations = the_workspace->iterations;
    uint64_t limit = the_workspace->limit;
    uint64_t num_values = the_workspace->num_values;
    int64_t * fixed_values = the_workspace->fixed_values;
    uint64_t num_fixed_values = the_workspace->num_fixed_values;
    CSearchState * search_queue_next_to_pop = the_workspace->search_queue_next_to_pop;
    CSearchState * search_queue_next_free = the_workspace->search_queue_next_free;
    int64_t * lower_bounds = the_workspace->lower_bounds;
    int64_t * upper_bounds = the_workspace->upper_bounds;

    int64_t new_values[MAX_NUM_VALUES];

    uint8_t found_solution = 0;
    CSearchState answer_search_head;
    while ((search_queue_next_free < queue_end) && (search_queue_next_to_pop < search_queue_next_free) && (iterations < limit) && (!found_solution)) {
        iterations++;

        CSearchState current_state = *search_queue_next_to_pop;

        // // For debugging/profiling
        // if (iterations == ((iterations >> 18) << 18)) {
        //     printf("\n");
        //     printf("%lld\n", iterations);
        //     printf("\n");
        // }

        // // Trace of search execution
        // if (1) {  //(iterations == ((iterations >> 15) << 15)) {
        //     switch (current_state.node->node_type) {
        //         case Initial:
        //             printf("Initial\n");  // (%d)", current_state.node->node_i);
        //             break;
        //         case Terminal:
        //             printf("Terminal\n");  // (%d)", current_state.node->node_i);
        //             break;
        //         case Addition:
        //             printf("Addition\n");  // (%d)", current_state.node->node_i);
        //             break;
        //         case IntegerPrint:
        //             printf("IntegerPrint\n");  // (%d)", current_state.node->node_i);
        //             break;
        //         case UnicodePrint:
        //             printf("UnicodePrint\n");  // (%d)", current_state.node->node_i);
        //             break;
        //         case Subtraction:
        //             printf("Subtraction\n");  // (%d)", current_state.node->node_i);
        //             break;
        //         case ConditionalIncrement:
        //             printf("ConditionalIncrement\n");  // (%d)", current_state.node->node_i);
        //             break;
        //         case ConditionalDecrement:
        //             printf("ConditionalDecrement\n");  // (%d)", current_state.node->node_i);
        //             break;
        //         case NoneType:
        //             printf("NoneType\n");  // (%d)", current_state.node->node_i);
        //             break;
        //     }
        // }
        // for (uint64_t i=0; i < num_fixed_values; i++) {
        //     printf("%d ", current_state.values[i]);
        // }
        // printf("\n");
        // for (uint64_t i=num_fixed_values; i < num_values; i++) {
        //     printf("%d ", current_state.values[i]);
        // }
        // printf("\n");

        // Create new values for this state

        for (uint64_t i=0; i < num_values; i++) {
            new_values[i] = current_state.values[i];
        }

        switch (current_state.node->node_type) {
            case Addition:
            case Subtraction:
            case ConditionalIncrement:
            case ConditionalDecrement:
                ;  // Required because next line is a statement
                int64_t rhs;
                if (current_state.node->rhs_is_constant) {
                    rhs = current_state.node->rhs;
                } else {
                    rhs = current_state.values[current_state.node->rhs];
                }

                int64_t rvalue = -1;  // reverse-search, so reverse the operation

                switch (current_state.node->node_type) {
                    case Subtraction:
                    case ConditionalDecrement:
                        rvalue *= -1;
                }
                switch (current_state.node->node_type) {
                    case Addition:
                    case Subtraction:
                        rvalue *= rhs;
                }
                switch (current_state.node->node_type) {
                    case ConditionalIncrement:
                    case ConditionalDecrement:
                        if (rhs <= 0) {
                            rvalue = 0;  // Do nothing if condition not satisfied
                        }
                }

                new_values[current_state.node->lhs] += rvalue;
        }

        uint8_t keep_going_from_here = 1;

        if ((current_state.node->node_type == Terminal) && (current_state.last_node != NULL)) {
            // Terminal nodes terminate this search path, unless it's the first node
            keep_going_from_here = 0;
        }

        for (uint64_t i=0; i<num_values; i++) {
            if ((new_values[i] < lower_bounds[i]) || (new_values[i] > upper_bounds[i])) {
                keep_going_from_here = 0;
                // Bounds violation.
                break;
            }
        }

        if (keep_going_from_here) {
            // Make all successor states (this is where the LOGIC happens!)
            for (uint64_t ii=0; ii < current_state.node->num_neighbors; ii++) {
                CNode * neighbor_node = current_state.node->neighbor_arr[ii];

                if (neighbor_node == current_state.last_node) {
                    // printf("Neighbor!\n");
                    continue;  // No backtracking allowed
                }

                CSearchState next_search_state;

                next_search_state.node = neighbor_node;
                next_search_state.last_node = current_state.node;
                for (uint64_t i=0; i < num_values; i++) {
                    next_search_state.values[i] = new_values[i];
                }
                next_search_state.parent_search_state = search_queue_next_to_pop;

                *search_queue_next_free = next_search_state;
                search_queue_next_free++;
            }
        }

        if (current_state.node->node_type == Initial) {
            uint8_t fixed_equal = 1;
            // printf("Checking..  ");
            for (uint64_t i=0; i<num_fixed_values; i++) {
                // printf("%lld=?%lld  ", current_state.values[i], fixed_values[i]);
                if (current_state.values[i] != fixed_values[i]) {
                    fixed_equal = 0;
                }
            }
            // printf("\n");
            if (fixed_equal) {
                found_solution = 1;
                answer_search_head = current_state;
            }
        }

        search_queue_next_to_pop++;
    }

    int64_t * ans;

    if (found_solution) {
        // Traverse the `SearchState`s to find the length of the answer. Then malloc + copy node ids
        CSearchState * current_search_head;

        uint64_t soln_len = 1;
        current_search_head = &(answer_search_head);
        while (current_search_head->parent_search_state != NULL) {
            current_search_head = current_search_head->parent_search_state;
            soln_len += 1;
        }

        ans = malloc(sizeof(int64_t) * (1 + num_values + soln_len));

        uint64_t offset = 0;

        ans[offset] = soln_len;
        offset++;

        for (uint64_t i=0; i<num_values; i++) {
            ans[offset] = answer_search_head.values[i];
            offset++;
        }
        current_search_head = &(answer_search_head);  // One more time through, now that we've malloc'd ans at the proper length
        ans[offset] = current_search_head->node->node_i;
        offset++;
        while (current_search_head->parent_search_state != NULL) {
            current_search_head = current_search_head->parent_search_state;
            ans[offset] = current_search_head->node->node_i;
            offset++;
        }

    } else {
        if (search_queue_next_free >= queue_end) {
            printf("Search terminated: Out of queue space\n");
        }
        if (search_queue_next_to_pop >= search_queue_next_free) {
            printf("Search terminated: Out of nodes to search\n");
        }
        if (iterations >= limit) {
            // printf("Search terminated: Reached iteration limit\n"); // Not informative.
        }

        // This special array will make it clear we failed.
        ans = malloc(sizeof(uint64_t));
        ans[0] = -1;
    }

    the_workspace->iterations = iterations;
    the_workspace->search_queue_next_to_pop = search_queue_next_to_pop;
    the_workspace->search_queue_next_free = search_queue_next_free;

    return ans;

}