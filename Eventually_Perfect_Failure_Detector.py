import math
import os
import json
import re
import csv
import shutil
from datetime import datetime

class node_class():
  def __init__(self, index, n, is_leader = False):
    self.T = 1 # Heartbeat time
    self.n = n # network size
    self.neighbors = []
    self.group_no = None
    self.index = index
    self.index_in_group = 0
    self.clock = 1
    self.group = None
    self.group_bag = {}
    self.group_lastHB = []
    self.group_suspect = []
    self.suspect = []
    # fill suspect list with False
    for i in range(n):
      self.suspect.append(False)
    self.group_timeout = []
    self.group_TTL = []

    self.is_leader = is_leader
    self.index_in_leaders = None
    self.leader_groups = {}
    self.leaders = []
    self.leader_lastHB = []
    self.leader_timeout = []
    self.leader_TTL = []

    self.local_leader_bag = []
    self.messages = []
    self.local_TTL = None
    self.local_is_outgoing = None

  def updateGroup(self, group, index_in_group):
    # update group info after network build
    self.group = group.copy()
    self.index_in_group = index_in_group
    for node in group:
      self.group_lastHB.append(0)
      self.group_suspect.append(False)
      self.group_timeout.append(self.T)
      self.group_TTL.append(1)

  def updateLeaders(self, leader_groups, leaders):
    # update leader info after network build
    self.leader_groups = leader_groups.copy()
    self.leaders = leaders.copy()
    for i in range(len(leaders)):
      self.leader_lastHB.append(0)
      self.leader_timeout.append(self.T)
      self.leader_TTL.append(0)

  def updateLeader(self, index_in_leaders):
    # update self to be a leader node
    self.is_leader = True
    self.index_in_leaders = index_in_leaders
  
  def groupSend(self):
    # Algorithm 5 Group Send function
    self.clock += self.T
    self.group_bag = {(self, len(self.group) - 1)}
    for index in range(len(self.group)):
      if self.group[index] != self:
        if self.group_suspect[index] == False and self.group_TTL[index] > 1:
          self.group_bag.add((self.group[index], (self.group_TTL[index] - 1)))
    for group_neighbor in list(set(self.group) & set(self.neighbors)):
      group_neighbor.groupReceive(self.group_bag, self)

  def groupReceive(self, gr_bag, sending_node):
    # Algorithm 5 Group Receive function
    for r, m in gr_bag:
      if r == sending_node or r not in self.neighbors:
        if self.group_TTL[r.index_in_group] <= m:
          self.group_TTL[r.index_in_group] = m
          if self.group_suspect[r.index_in_group] == True:
            self.group_suspect[r.index_in_group] = False
            # ESTIMATE_TIMEOUT
            if r in self.group:
              self.group_timeout[r.index_in_group] = 2 * self.group_timeout[r.index_in_group]
          self.group_lastHB[r.index_in_group] = self.clock

    for node in self.group:
      self.suspect[node.index] = self.group_suspect[node.index_in_group]

  def leaderSend(self):
    # Algorithm 2 Information Send function
    leader_bag = [(self, len(self.leaders) - 1, self.group_suspect)]
    for leader in [x for x in self.leaders if x != self]:
      if self.leader_TTL[leader.index_in_leaders] > 1:
        # GET_GROUP_SUSPECT
        external_group_suspect = []
        for node in leader.group:
          external_group_suspect.append(self.suspect[node.index])
        # END GET_GROUP_SUSPECT
        leader_bag.append((leader, self.leader_TTL[leader.index_in_leaders], external_group_suspect))

    # send to non-group neighbors
    for neighbor in [x for x in self.neighbors if x not in self.group]:
      neighbor.leaderBagReceiveNonGroup(self, leader_bag)

    # send to group neighbors
    for neighbor in [x for x in self.neighbors if x in self.group]:
      is_outgoing = True
      TTL = len(self.group) - 1
      neighbor.leaderBagReceiveGroup(self, leader_bag, TTL, is_outgoing)

  def leaderBagReceiveGroup(self, sending_node, lead_bag, TTL, is_outgoing):
    # When node recieves leader bag from within the group
    if (not is_outgoing) and self.is_leader:
      for r, m, array in [x for x in lead_bag if x == sending_node or x not in self.neighbors]:
        if self.leader_TTL[r.index_in_leaders] <= m:
          self.leader_TTL[r.index_in_leaders] = m
          for node in r.group:
            self.suspect[node.index] = array[node.index_in_group]
          if self.suspect[r.index]:
            self.suspect[r.index] = False
            # ESTIMATE_TIMEOUT
            if r in self.leaders:
              self.leader_timeout[r.index_in_leaders] = 2 * self.leader_timeout[r.index_in_leaders]
            # END ESTIMATE_TIMEOUT
          self.leader_lastHB[r.index_in_leaders] = self.clock

    if not self.is_leader:
      self.local_TTL = TTL

      # UNION lead_bag into local_leader_bag

      for lead_ind, lead_ent in enumerate(lead_bag):
        match_found = False
        for loc_ind, loc_ent in enumerate(self.local_leader_bag):
          if lead_ent[0] == loc_ent[0]:
            for index, update in enumerate(lead_ent[2]):
              if update == False and loc_ent[2][index] == True:
                loc_ent[2][index] = False
            match_found = True
        if not match_found:
          self.local_leader_bag.append(lead_ent)
      if len(self.local_leader_bag) < 1:
        self.local_leader_bag = lead_bag
      
      # UPDATE_SUSPECT
      for r, m, array in lead_bag:
        if self.leader_TTL[r.index_in_leaders] <= m:
          self.leader_TTL[r.index_in_leaders] = m
          for node in r.group:
            self.suspect[node.index] = array[node.index_in_group]
          if self.suspect[r.index]:
            self.suspect[r.index] = False
            # ESTIMATE_TIMEOUT
            if r in self.leaders:
              self.leader_timeout[r.index_in_leaders] = 2 * self.leader_timeout[r.index_in_leaders]
            # END ESTIMATE_TIMEOUT
          self.leader_lastHB[r.index_in_leaders] = self.clock
      # END UPDATE_SUSPECT
  
  def leaderBagReceiveNonGroup(self, sending_node, lead_bag):
    # When node receives leader bag from a node outside the group
    if self.is_leader:
      for r, m, array in [x for x in lead_bag if x == sending_node or x not in self.neighbors]:
        if self.leader_TTL[r.index_in_leaders] <= m:
          self.leader_TTL[r.index_in_leaders] = m
          for node in r.group:
            if self.suspect[node.index] == True and array[node.index_in_group] == False:
              self.suspect[node.index] = array[node.index_in_group]
          if self.suspect[r.index]:
            self.suspect[r.index] = False
            # ESTIMATE_TIMEOUT
            if r in self.leaders:
              self.leader_timeout[r.index_in_leaders] = 2 * self.leader_timeout[r.index_in_leaders]
            # END ESTIMATE_TIMEOUT
          self.leader_lastHB[r.index_in_leaders] = self.clock

    else:
      is_outgoing = False
      TTL = len(self.group) - 1
      self.messages.append((lead_bag, TTL, is_outgoing))

  def sendOverlays(self):
    # Algorithm 7 functions
    # Send to other groups
    # if is_outgoing
    if len(self.local_leader_bag) > 0:
      for neighbor in [x for x in self.neighbors if x not in self.group]:
        neighbor.leaderBagReceiveNonGroup(self, self.local_leader_bag)
      
    # Within-Group Send/Receive
    # if TTL > 1
    if True:
      for neighbor in [x for x in self.neighbors if x in self.group]:
        neighbor.leaderBagReceiveGroup(self, self.local_leader_bag, len(self.group) - 1, False)

    # Send messages
    if len(self.messages) > 0:
      for neighbor in [x for x in self.neighbors if x in self.group]:
        for message in self.messages:
          neighbor.leaderBagReceiveGroup(self, message[0], message[1], message[2])

def buildNetwork(size: int, connections: list, groups: list, leaders: list):
  # Builds network as defined by input arguments to define topology
  nodes = []

  # Create node object for each node
  for i in range(size):
    nodes.append(node_class(i, size))
  # Connect nodes that are neighbors as defined by connections
  for index in range(len(connections)):
    for neighbor in connections[index]:
      if nodes[neighbor] not in nodes[index].neighbors:
        nodes[index].neighbors.append(nodes[neighbor])

  # Create node groups and add appropriate nodes
  node_groups = []
  for group in groups:
    temp_group = []
    for node_i in group:
      temp_group.append(nodes[node_i])
    node_groups.append(temp_group)

  # Create leader list and add appropriate leader nodes
  node_leaders = []
  for leader_i in leaders:
    node_leaders.append(nodes[leader_i])
  
  # Update all nodes' information about groups and leaders
  for group in node_groups:
    for node_i, node in enumerate(group):
      node.updateGroup(group, node_i)
      node.updateLeaders(node_groups, node_leaders)

  # Update leader nodes so they know they are leaders
  for leader_i, leader in enumerate(node_leaders):
    leader.updateLeader(leader_i)

  # Return the constructed network
  return {
    "nodes": nodes,
    "groups": node_groups,
    "leaders": node_leaders
  }

def runHeartbeat(network, iter):
  # Heartbeat pattern that runs in 3 phases to prevent overlap
  # between functionallity that can't occur on the same heartbeat
  # from happening at once
  if iter % 3 == 0:
    for leader in network["leaders"]:
      # Run information send from all leader nodes
      leader.leaderSend()
  elif iter % 3 == 1:
    for node in network["nodes"]:
      # Run group send from all nodes
      node.groupSend()
  else:
    for node in network["nodes"]:
      # Simulate the overlay network
      node.sendOverlays()

def checkConverged(network):
  # Checks if all suspicions are set to False in network
  for node in network["nodes"]:
    if True in node.suspect:
      return False
  return True

def buildTopologyList(size, connections, groups, leaders):
  # Builds several versions of each topology to simulate both
  # unclustered and clustered algorithms.

  topologies = []

  default_groups = [range(size)]

  default_leaders = [0]

  node_to_sus = math.floor(size * 0.75)

  # non-clustered algorithm

  # Single suspect

  temp_network = buildNetwork(size, connections, default_groups, default_leaders)

  temp_network["nodes"][0].suspect[node_to_sus] = True
  temp_network["nodes"][0].group_suspect[node_to_sus] = True

  topologies.append(temp_network)

  # Each suspects one node

  temp_network = buildNetwork(size, connections, default_groups, default_leaders)

  for node in temp_network["nodes"]:

    node.suspect[node_to_sus] = True
    node.group_suspect[node_to_sus] = True

  topologies.append(temp_network)

  # Each suspects every other

  temp_network = buildNetwork(size, connections, default_groups, default_leaders)

  for node in temp_network["nodes"]:
    for group_member in range(len(node.group)):
      node.group_suspect[group_member] = True
    for network_member in range(node.n):
      node.suspect[network_member] = True

  topologies.append(temp_network)

  # clustered algorithm

  # Single suspect

  temp_network = buildNetwork(size, connections, groups, leaders)

  temp_network["nodes"][0].suspect[node_to_sus] = True

  topologies.append(temp_network)

  # Each suspects one node

  temp_network = buildNetwork(size, connections, groups, leaders)

  for node in temp_network["nodes"]:

    node.suspect[node_to_sus] = True
    if temp_network["nodes"][node_to_sus] in node.group:
      node.group_suspect[temp_network["nodes"][node_to_sus].index_in_group] = True

  topologies.append(temp_network)

  # Each suspects every other

  temp_network = buildNetwork(size, connections, groups, leaders)

  for node in temp_network["nodes"]:
    for group_member in range(len(node.group)):
      node.group_suspect[group_member] = True
    for network_member in range(node.n):
      node.suspect[network_member] = True

  topologies.append(temp_network)
      
  return topologies

def main():

  # Create and open csv file
  headers = ['file', 'number_nodes', 'number_groups', 'average_degree', 'non-cluster_one_suspect_one', 'non-cluster_every_suspect_same_one', 'non-cluser_every_suspect_every', 'cluster_one_suspect_node', 'cluster_every_suspect_same_one', 'cluster_every_suspect_every']
  csv_file = open('output.csv', 'w')
  csv_writer = csv.writer(csv_file, lineterminator='\n')
  csv_writer.writerow(headers)

  # Open the inputs folder
  directory = os.fsencode('inputs')

  # For each input, run simulation
  for file in os.listdir(directory):
    row = []

    filename = os.fsdecode(file)
    filename_list = re.split('_|\.', filename)
    if filename_list[-1] == 'txt':
      # If file is .txt extension
      print("\n----------\n")
      print(filename)
      row.append(filename)

      in_file = open('inputs/' + filename, 'r')
      input = json.load(in_file)

      # Store network info in csv file
      print(input[0], " nodes")
      print(len(input[2]), " groups")
      print("")
      row.append(input[0])
      row.append(len(input[2]))
      num_connections = 0
      for node in input[1]:
        num_connections += len(node)
      row.append((num_connections / 2.0) / input[0])

      # Build the topologies to simulate
      topologies = buildTopologyList(*input)
      # Simulate each topology
      for error_index, network in enumerate(topologies):
        iter = 0
        while not checkConverged(network):
          # Increment counter and run each heartbeat
          iter += 1
          runHeartbeat(network, iter)
        print("Converged after: " + str(iter) + " heartbeats")
        row.append(iter)

      # Store information for this topology
      csv_writer.writerow(row)

  # Close csv file
  csv_file.close()
  timestamp_filename = 'outputs/output' + str(datetime.now().strftime('_%Y_%m_%d_%H_%M_%S')) + '.csv'

  # Copy output file to archive directory
  os.makedirs(os.path.dirname(timestamp_filename), exist_ok=True)
  shutil.copy('output.csv', timestamp_filename)

if __name__ == '__main__':
  main()