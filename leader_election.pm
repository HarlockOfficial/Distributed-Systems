/* Definition of a leader election algorithm in a mesh network
 * The leader election algorithm is a simple algorithm that allows a
 * set of nodes to elect a special node called leader that will be able to make decisions
 * The nodes are arranged in a mesh topology provided as initial system
 * The algorithm is based on the following rules:
 *  1) Each Node has a unique ID (there are no duplicate nodes identifiers)
 *  2) Each Node sends its ID to its neighbors with a probability "message_rate"
 *  3) Each Node compares its ID with the IDs received from its neighbors
 *  4) If the ID of the Node is greater than all the IDs received from its neighbors, then the Node is a Leader
 *  5) If the ID of the Node is smaller or equal than any of the IDs received from its neighbors, the node becomes a Follower
 *  6) Any follower will follow the node with the higher id
 *  7) Originally in the system there are only nodes
 *  8) The system is a mesh, so each Node has an undefined number of neighbors, N at most
 *  9) The communication in the mesh is bidirectional, so each Node can send and receive messages from its neighbors */

/* The following value is just a placeholder, this file is meant to be run by the python script
 * with parameter node_amount equal to the max identifier of a node in the input graph */
param node_amount = 0.0;

/*Node*/
species N of [0,node_amount];

/*Leader*/
species L of [0,node_amount];

/*Follower i of node j, where i is the original node id and j is the suspected leader id
 *                      i           j     */
species F of [0,node_amount]*[0, node_amount];

/*connection between i and j when i and j are two original node ids
 *                  i               j     */
species C of [0,node_amount]*[0,node_amount]; /*Connection*/

/* rate of sending messages, assumed 1 since if two nodes are connected
 * they should not have any problems in communicating at each timestep */
param message_rate = 1.0;

/* rate of inverting the communication indexes, adjusted to 0.3 to not occur too often */
param communication_inversion_rate = 0.3;

/* Node i meets Node j */
rule meet_node_node for i in [0,node_amount] and j in [0,node_amount] {
    N[i]|C[i, j]|N[j] -[ message_rate ]-> F[((i<=j)?i:j), ((i<=j)?j:i)]|C[i, j]|L[((i<=j)? j: i)]
}

/* Node i meets Follower j */
rule meet_node_follower for i in [0,node_amount] and j in [0,node_amount] and k in [0,node_amount] when (i<=k) {
    N[i]|C[i, j]|F[j, k] -[ message_rate ]-> F[i, k]|C[i, j]|F[j, k]
}
/* Node i meets Follower j */
rule meet_node_follower_2 for i in [0,node_amount] and j in [0,node_amount] and k in [0,node_amount] when (i>k) {
    N[i]|C[i, j]|F[j, k] -[ message_rate ]-> L[i]|C[i, j]|F[j, i]
}

/* Follower i meets Follower j */
rule meet_follower_follower for i in [0,node_amount] and j in [0,node_amount] and k in [0,node_amount] and l in [0,node_amount] {
    F[i, k]|C[i, j]|F[j, l] -[ message_rate ]-> F[i, ((k<=l)?l:k)]|C[i, j]|F[j, ((k<=l)?l:k)]
}

/* Leader i meets Leader j */
rule meet_leader_leader for i in [0,node_amount] and j in [0,node_amount] {
    L[i]|C[i, j]|L[j] -[ message_rate ]-> F[((i<=j)?i:j), ((i<=j)?j:i)]|C[i, j]|L[((i<=j)?j:i)]
}

/* Leader i meets Follower j */
rule meet_leader_follower for i in [0,node_amount] and j in [0,node_amount] and k in [0, node_amount] when (i>k) {
    L[i]|C[i, j]|F[j, k] -[ message_rate ]-> L[i]|C[i, j]|F[j, i]
}
/* Leader i meets Follower j */
/* Note, here is "when (i<k)" and not "when (i<=k)" because i might be the effective leader
 * and using <= might change the last leader to a follower*/
rule meet_leader_follower_2 for i in [0,node_amount] and j in [0,node_amount] and k in [0, node_amount] when (i<k) {
    L[i]|C[i, j]|F[j, k] -[ message_rate ]-> F[i, k]|C[i, j]|F[j, k]
}

/* Leader i meets Node j */
rule meet_leader_node for i in [0,node_amount] and j in [0,node_amount] {
    L[i]|C[i, j]|N[j] -[ message_rate ]-> L[((i<=j)?j:i)]|C[i, j]|F[((i<=j)?i:j), ((i<=j)?j:i)]
}

/* The Following rule is to invert the Communication indexes and avoid problems related to
 * the indexes order in bidirectional communications */
rule invert_communication_indexes for i in [0,node_amount] and j in [0,node_amount] {
    C[i, j] -[ communication_inversion_rate ]-> C[j, i]
}

system initial=N[i for i in [0, node_amount]]|C[i, ((i+1)%node_amount) for i in [0, node_amount]];
