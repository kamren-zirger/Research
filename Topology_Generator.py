import json
import os

def main():
  network_sizes = [50, 100, 150]
  group_sizes = [5, 10, 15]

  # Make inputs/ directory if not present
  os.makedirs(os.path.dirname('inputs/test.txt'), exist_ok=True)

  for network_size in network_sizes:
    for group_size in group_sizes:
      # Check we can fit groups into node len
      if group_size < network_size:

        generateChain(network_size, group_size)

        generateFullyConnected(network_size, group_size)

        generateChainClustersFullLeaders(network_size, group_size)

        generateAvgClustersAvgLeaders(network_size, group_size)

        generateFullClustersFullLeaders(network_size, group_size)

        generateFullClustersAvgLeaders(network_size, group_size)

        generateAvgClustersFullLeaders(network_size, group_size)

def generateChain(network_size, group_size):
  # Generate Chain
  filename = 'inputs/chain_' + str(network_size) + '_' + str(group_size) + '.txt'
  fptr = open(filename, 'w')

  connections = []
  groups = []
  leaders = []
  node_ind = 0
  in_group_ind = 0
  group_ind = 0

  # Set first node (only one neighbor)
  connections.append([1])
  groups.append([0])
  leaders.append(0)
  node_ind += 1
  in_group_ind += 1

  # Middle nodes
  while node_ind < network_size - 1:
    if in_group_ind >= group_size:
      group_ind += 1
      in_group_ind = 0
      groups.append([])
    connections.append([node_ind - 1, node_ind + 1])
    groups[group_ind].append(node_ind)

    node_ind += 1
    in_group_ind += 1
  
  # Last node (only one neighbor)
  connections.append([node_ind - 1])
  groups[group_ind].append(node_ind)

  for group in groups:
    leaders.append(group[-1])

  ret_list = [network_size, connections, groups, leaders]

  json.dump(ret_list, fptr)
  fptr.close()

def generateFullyConnected(network_size, group_size):
  # Generate Fully Connected
  filename = 'inputs/fully_connected_' + str(network_size) + '_' + str(group_size) + '.txt'
  fptr = open(filename, 'w')

  connections = []
  groups = []
  leaders = []
  node_ind = 0
  in_group_ind = group_size
  group_ind = -1

  # Generate all nodes with all other nodes as neighbors
  while node_ind < network_size:
    if in_group_ind >= group_size:
      group_ind += 1
      in_group_ind = 0
      groups.append([])
      leaders.append(node_ind)
    connections.append([x for x in range(network_size) if x != node_ind])
    groups[group_ind].append(node_ind)

    node_ind += 1
    in_group_ind += 1

  ret_list = [network_size, connections, groups, leaders]

  json.dump(ret_list, fptr)
  fptr.close()

def generateChainClustersFullLeaders(network_size, group_size):
  # Generate Chain Clusters Fully Connected Leaders
  filename = 'inputs/chain_clusters_fully_connected_' + str(network_size) + '_' + str(group_size) + '.txt'
  fptr = open(filename, 'w')

  connections = []
  groups = []
  leaders = []
  node_ind = 0
  in_group_ind = group_size
  group_ind = 0

  while node_ind < network_size - 1:
    if in_group_ind >= group_size:
      # First node in each chain cluster
      group_ind += 1
      in_group_ind = 0
      groups.append([])
      connections.append([node_ind + 1])
    elif in_group_ind == group_size - 1:
      # Last node in each chain cluster
      connections.append([node_ind - 1])
    else:
      # Middle nodes in each chain cluster
      connections.append([node_ind - 1, node_ind + 1])
    groups[group_ind].append(node_ind)

    node_ind += 1
    in_group_ind += 1
  
  # Last node
  connections.append([node_ind - 1])
  groups[group_ind].append(node_ind)

  # Set leaders for each group
  for group in groups:
    leaders.append(group[-1])

  # Fully connect leaders
  for leader in leaders:
    for node in [x for x in leaders if x != leader]:
      connections[leader].append(node)

  ret_list = [network_size, connections, groups, leaders]

  json.dump(ret_list, fptr)
  fptr.close()

def generateAvgClustersAvgLeaders(network_size, group_size):
  # Generate Average Clusters Average Leaders
  filename = 'inputs/avg_clusters_avg_leaders_' + str(network_size) + '_' + str(group_size) + '.txt'
  fptr = open(filename, 'w')

  connections = []
  groups = []
  leaders = []
  node_ind = 0
  in_group_ind = group_size
  group_ind = -1

  # Add each node to its group
  while node_ind < network_size:
    if in_group_ind >= group_size:
      group_ind += 1
      in_group_ind = 0
      groups.append([])
      leaders.append(node_ind)
    groups[group_ind].append(node_ind)
    connections.append([])

    node_ind += 1
    in_group_ind += 1

  # Connect each group node to 3 other group nodes
  for group in groups:
    for idx, node in enumerate(group):
      if node - 1 in group:
        connections[node].append(node - 1)
        connections[node - 1].append(node)
      if node + 1 in group:
        connections[node].append(node + 1)
        connections[node + 1].append(node)
      other_ind = int(node + (len(group) / 2)) % len(group)
      connections[node].append(other_ind)
      connections[other_ind].append(node)

  # Connect leaders to 3 other leaders
  for idx, leader in enumerate(leaders):
    connections[leader].append(leaders[(idx + 1) % len(leaders)])
    connections[leaders[(idx + 1) % len(leaders)]].append(leader)
    connections[leader].append(leaders[(idx - 1) % len(leaders)])
    connections[leaders[(idx - 1) % len(leaders)]].append(leader)
    connections[leader].append(leaders[(idx + int(len(leaders) / 2)) % len(leaders)])
    connections[leaders[(idx + int(len(leaders) / 2)) % len(leaders)]].append(leader)

  ret_list = [network_size, connections, groups, leaders]

  json.dump(ret_list, fptr)
  fptr.close()

def generateFullClustersFullLeaders(network_size, group_size):
  # Generate Fully Connected Clusters Fully Connected Leaders
  filename = 'inputs/full_clusters_full_leaders_' + str(network_size) + '_' + str(group_size) + '.txt'
  fptr = open(filename, 'w')

  connections = []
  groups = []
  leaders = []
  node_ind = 0
  in_group_ind = group_size
  group_ind = -1

  # Add each node to its group
  while node_ind < network_size:
    if in_group_ind >= group_size:
      group_ind += 1
      in_group_ind = 0
      groups.append([])
      leaders.append(node_ind)
    connections.append([])
    groups[group_ind].append(node_ind)

    node_ind += 1
    in_group_ind += 1
  
  # Fully connect groups
  for group in groups:
    for node in group:
      for neighbor in [x for x in group if x!= node]:
        connections[node].append(neighbor)

  # Fully connect leaders
  for leader in leaders:
    for node in [x for x in leaders if x != leader]:
      connections[leader].append(node)

  ret_list = [network_size, connections, groups, leaders]

  json.dump(ret_list, fptr)
  fptr.close()

def generateFullClustersAvgLeaders(network_size, group_size):
  # Generate Fully Connected Clusters Avg Connected Leaders
  filename = 'inputs/full_clusters_avg_leaders_' + str(network_size) + '_' + str(group_size) + '.txt'
  fptr = open(filename, 'w')

  connections = []
  groups = []
  leaders = []
  node_ind = 0
  in_group_ind = group_size
  group_ind = -1

  # Add each node to its group
  while node_ind < network_size:
    if in_group_ind >= group_size:
      group_ind += 1
      in_group_ind = 0
      groups.append([])
    connections.append([])
    groups[group_ind].append(node_ind)

    node_ind += 1
    in_group_ind += 1

  for group in groups:
    leaders.append(group[-1])
  
  # Fully connect groups
  for group in groups:
    for node in group:
      for neighbor in [x for x in group if x!= node]:
        connections[node].append(neighbor)

  # Avg connect leaders
  leader_connection_round = 0
  while leader_connection_round < (len(leaders) * len(leaders)) / 2:
    for idx, leader in enumerate(leaders):
      connections[leader].append(leaders[(idx + leader_connection_round + 1) % len(leaders)])
      connections[leaders[(idx + leader_connection_round + 1) % len(leaders)]].append(leader)
    leader_connection_round += 1

  ret_list = [network_size, connections, groups, leaders]

  json.dump(ret_list, fptr)
  fptr.close()

def generateAvgClustersFullLeaders(network_size, group_size):
  # Generate Average Clusters Full Leaders
  filename = 'inputs/avg_clusters_full_leaders_' + str(network_size) + '_' + str(group_size) + '.txt'
  fptr = open(filename, 'w')

  connections = []
  groups = []
  leaders = []
  node_ind = 0
  in_group_ind = group_size
  group_ind = -1

  # Add each node to its group
  while node_ind < network_size:
    if in_group_ind >= group_size:
      group_ind += 1
      in_group_ind = 0
      groups.append([])
      leaders.append(node_ind)
    groups[group_ind].append(node_ind)
    connections.append([])

    node_ind += 1
    in_group_ind += 1

  # Average connect each group member to other group members
  for group in groups:
    for idx, node in enumerate(group):
      if node - 1 in group:
        connections[node].append(node - 1)
        connections[node - 1].append(node)
      if node + 1 in group:
        connections[node].append(node + 1)
        connections[node + 1].append(node)
      other_ind = int(node + (len(group) / 2)) % len(group)
      connections[node].append(other_ind)
      connections[other_ind].append(node)

  # Fully connect leaders
  for leader in leaders:
    for node in [x for x in leaders if x != leader]:
      connections[leader].append(node)

  ret_list = [network_size, connections, groups, leaders]

  json.dump(ret_list, fptr)
  fptr.close()

if __name__ == '__main__':
  main()