# Author: K. Zirger
# 2022

class node_class():
  def __init__(self, index, n, is_leader = False):
    self.T = 1 # Heartbeat time
    self.n = n
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
    self.group = group.copy()
    self.index_in_group = index_in_group
    for node in group:
      self.group_lastHB.append(0)
      # suspect default to true for testing?
      self.group_suspect.append(False)
      self.group_timeout.append(self.T)
      self.group_TTL.append(1)

  def updateLeaders(self, leader_groups, leaders):
    self.leader_groups = leader_groups.copy()
    self.leaders = leaders.copy()
    for i in range(len(leaders)):
      self.leader_lastHB.append(0)
      self.leader_timeout.append(self.T)
      self.leader_TTL.append(0)

  def updateLeader(self, index_in_leaders):
    self.is_leader = True
    self.index_in_leaders = index_in_leaders
  
  def groupSend(self):
    self.clock += self.T
    self.group_bag = {(self, len(self.group) - 1)}
    for index in range(len(self.group)):
      if self.group[index] != self:
        if self.group_suspect[index] == False and self.group_TTL[index] > 1:
          self.group_bag.add((self.group[index], (self.group_TTL[index] - 1)))
    for group_neighbor in list(set(self.group) & set(self.neighbors)):
      group_neighbor.groupReceive(self.group_bag, self)

  def groupReceive(self, gr_bag, sending_node):
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
    leader_bag = [(self, len(self.leaders) - 1, self.group_suspect)]
    for leader in [x for x in self.leaders if x != self]:
      if self.leader_TTL[leader.index_in_leaders] > 1:
        # GET_GROUP_SUSPECT
        external_group_suspect = []
        for node in leader.group:
          external_group_suspect.append(self.suspect[node.index])
        # END GET_GROUP_SUSPECT
        leader_bag.append((leader, self.leader_TTL[leader.index_in_leaders] - 1, external_group_suspect))

    # send to non-group neighbors
    for neighbor in [x for x in self.neighbors if x not in self.group]:
      neighbor.leaderBagReceiveNonGroup(self, leader_bag)

    # send to group neighbors
    for neighbor in [x for x in self.neighbors if x in self.group]:
      is_outgoing = True
      TTL = len(self.group) - 1
      neighbor.leaderBagReceiveGroup(self, leader_bag, TTL, is_outgoing)

  def leaderBagReceiveGroup(self, sending_node, lead_bag, TTL, is_outgoing):
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
            self.local_leader_bag[loc_ind] = lead_ent
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
    if self.is_leader:
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

    else:
      is_outgoing = False
      TTL = len(self.group) - 1
      self.messages = (lead_bag, TTL, is_outgoing)

  def sendOverlays(self):
    # Send to other groups
    # if is_outgoing
    if len(self.local_leader_bag) > 0:
      for neighbor in [x for x in self.neighbors if x not in self.group]:
        neighbor.leaderBagReceiveNonGroup(self, self.local_leader_bag)
      
    # Within-Group Send/Receive
    # if TTL > 1
    if True:
      for neighbor in [x for x in self.neighbors if x in self.group]:
        neighbor.leaderBagReceiveGroup(self, self.local_leader_bag, 0, self.local_is_outgoing)

    # Send messages
    if len(self.messages) > 0:
      for neighbor in [x for x in self.neighbors if x in self.group]:
        neighbor.leaderBagReceiveGroup(self, self.messages[0], self.messages[1], self.messages[2])

def buildNetwork(size: int, connections: list, groups: list, leaders: list):
  nodes = []
  for i in range(size):
    nodes.append(node_class(i, size))
  for index in range(len(connections)):
    for neighbor in connections[index]:
      if nodes[neighbor] not in nodes[index].neighbors:
        nodes[index].neighbors.append(nodes[neighbor])

  node_groups = []
  for group in groups:
    temp_group = []
    for node_i in group:
      temp_group.append(nodes[node_i])
    node_groups.append(temp_group)

  node_leaders = []
  for leader_i in leaders:
    node_leaders.append(nodes[leader_i])
  
  for group in node_groups:
    for node_i, node in enumerate(group):
      node.updateGroup(group, node_i)
      node.updateLeaders(node_groups, node_leaders)

  for leader_i, leader in enumerate(node_leaders):
    leader.updateLeader(leader_i)

  return {
    "nodes": nodes,
    "groups": node_groups,
    "leaders": node_leaders
  }

def checkConverged(network):
  for node in network["nodes"]:
    if True in node.suspect:
      return False
  return True

def buildExample1():
  connections = [
    [5],
    [5, 6, 2],
    [1, 3, 8],
    [2, 4, 8, 9],
    [3, 8, 9, 19],
    [0, 1, 11],
    [1, 7, 11, 12],
    [6, 13],
    [2, 3, 4, 9, 13],
    [3, 4, 8],
    [13, 15],
    [5, 6],
    [6, 16, 17],
    [7, 8, 10, 14, 18],
    [13],
    [10, 16],
    [12, 15],
    [12, 18],
    [13, 17, 19],
    [18, 4]
  ]

  groups = [[
    0, 5, 6, 7, 11,
    1, 2, 3, 4, 9,
    8, 13, 14, 18, 19,
    10, 12, 15, 16, 17
    ]]

  leaders = [5]

  network = buildNetwork(20, connections, groups, leaders)

  network["nodes"][0].suspect[19] = True
  network["nodes"][0].group_suspect[19] = True
      
  return network

def main():

  print("In-Paper Network Example, old algorithm, one error")

  network = buildExample1()
  leaders = network["leaders"]
  iter = 0
  while not checkConverged(network):
    iter += 1
    for node in network["nodes"]:
      node.groupSend()
    for leader in leaders:
      leader.leaderSend()
    for node in network["nodes"]:
      node.sendOverlays()
  print("Converged after: " + str(iter) + " heartbeats")


    
if __name__ == "__main__":
  main()