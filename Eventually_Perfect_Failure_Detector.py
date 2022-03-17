
# Author: K. Zirger
# 2022

class node():
  def __init__(self, n, is_leader = False):
    self.T = 1 # Heartbeat time
    self.n = n
    self.neighbors = []
    self.group_no = None
    self.is_leader = is_leader
    self.index_in_group = 0
    self.clock = 1
    self.group = None
    self.group_bag = {}
    self.group_lastHB = []
    # group suspect is shared variable??
    self.group_suspect = []
    self.group_timeout = []
    self.group_TTL = []

  def updateGroup(self, group, index_in_group):
    self.group = group
    self.index_in_group = index_in_group
    for node in group:
      self.group_lastHB.append(0)
      # suspect default to true for testing?
      self.group_suspect.append(True)
      self.group_timeout.append(self.T)
      self.group_TTL.append(1)
  
  def groupSend(self):
    self.clock += self.T
    self.group_bag = {(self, len(self.group) - 1)}
    for index in range(len(self.group)):
      if self.group[index] != self:
        if self.group_suspect[index] == False and self.group_TTL[index] > 1:
          self.group_bag.add((self.group[index], (self.group_TTL[index] - 1)))
    for group_neighbor in list(set(self.group) & set(self.neighbors)):
      group_neighbor.groupRecieve(self.group_bag, self)

  def groupRecieve(self, gr_bag, sending_node):
    for r, m in gr_bag:
      if (r not in self.neighbors) and r != sending_node:
        # Way to do this without index/okay to include index?
        if self.group_TTL[r.index_in_group] <= m:
          self.group_TTL[r.index_in_group] = m
          if self.group_suspect[r.index_in_group] == True:
            self.group_suspect[r.index_in_group] = False
            # ESTIMATE_TIMEOUT
            if r in self.group:
              self.group_timeout[r.index_in_group] = 2 * self.group_timeout[r.index_in_group]
          self.group_lastHB[r.index_in_group] = self.clock

def buildNetwork(size: int, connections: list):
  nodes = []
  for i in range(size):
    nodes.append(node(size))
  for index in range(len(connections)):
    for neighbor in connections[index]:
      if nodes[neighbor] not in nodes[index].neighbors:
        nodes[index].neighbors.append(nodes[neighbor])
  return nodes

def checkConverged(groups):
  for group in groups:
    for node in group:
      if True in node.group_suspect:
        return False
  return True

def buildExample1():
  connections = [
    [5],
    [5, 6],
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
  network = buildNetwork(20, connections)

  groups = [[
    network[0], network[5], network[6], network[7], network[11],
    network[1], network[2], network[3], network[4], network[9],
    network[8], network[13], network[14], network[18], network[19],
    network[10], network[12], network[15], network[16], network[17]
    ]]

  for group in groups:
    for node_i in range(len(group)):
      group[node_i].updateGroup(group, node_i)
      
  return groups

def main():
  groups = buildExample1()
  iter = 0
  while not checkConverged(groups):
    print(iter)
    iter += 1
    for group in groups:
      for node in group:
        node.groupSend()
  print("Converged after: " + str(iter) + " iterations")
    
if __name__ == "__main__":
  main()