
# Author: K. Zirger
# 2022

class node():
  def __init__(self, n, neighbors, group_no, is_leader = False):
    self.T = 1 # Heartbeat time
    self.n = n
    self.neighbors = neighbors
    for neighbor in self.neighbors:
      neighbor.neighbors.append(self)
    self.group_no = group_no
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
      self.group_suspect.append(False)
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
      # In this case I'm assuming we want r without (neighbors and q) rather than
      # r without (neighbors without q)
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

def checkConverged(groups):
  for group in groups:
    for node in group:
      if True in node.group_suspect:
        return False
  return True

def buildExample1():
  p0 = node(20, [], 0)
  p1 = node(20, [], 1)
  p2 = node(20, [p1], 0, True)
  p3 = node(20, [p2], 0)
  p4 = node(20, [p3], 0)
  p5 = node(20, [p0, p1], 0)
  p6 = node(20, [p1], 0)
  p7 = node(20, [p6], 0)
  p8 = node(20, [p2, p3, p4], 0)
  p9 = node(20, [p3, p4, p8], 0)
  p10 = node(20, [], 0)
  p11 = node(20, [p5, p6], 0)
  p12 = node(20, [], 0)
  p13 = node(20, [p7, p8, p10], 0)
  p14 = node(20, [p13], 0)
  p15 = node(20, [p10], 0)
  p16 = node(20, [p15], 0)
  p17 = node(20, [p12], 0)
  p18 = node(20, [p13, p17], 0)
  p19 = node(20, [p4, p18], 0)

  groups = [[
    p0, p5, p6, p7, p11,
    p1, p2, p3, p4, p9,
    p8, p13, p14, p18, p19,
    p10, p12, p15, p16, p17
    ]]

  for group in groups:
    for node_i in range(len(group)):
      group[node_i].updateGroup(group, node_i)
      
  return groups

def buildExample2():
  p0 = node(20, [], 0)
  p1 = node(20, [], 1)
  p2 = node(20, [p1], 1, True)
  p3 = node(20, [p2], 1)
  p4 = node(20, [p3], 1)
  p5 = node(20, [p0, p1], 0, True)
  p6 = node(20, [p1], 0)
  p7 = node(20, [p6], 0)
  p8 = node(20, [p2, p3, p4], 2)
  p9 = node(20, [p3, p4, p8], 1)
  p10 = node(20, [], 3)
  p11 = node(20, [p5, p6], 0)
  p12 = node(20, [], 3)
  p13 = node(20, [p7, p8, p10], 2)
  p14 = node(20, [p13], 2, True)
  p15 = node(20, [p10], 3)
  p16 = node(20, [p15], 3, True)
  p17 = node(20, [p12], 3)
  p18 = node(20, [p13, p17], 2)
  p19 = node(20, [p4, p18], 2)

  groups = [
    [p0, p5, p6, p7, p11],
    [p1, p2, p3, p4, p9],
    [p8, p13, p14, p18, p19],
    [p10, p12, p15, p16, p17]
    ]

  for group in groups:
    for node_i in range(len(group)):
      group[node_i].updateGroup(group, node_i)

  return groups

def main():
  groups = buildExample1()
  while True:
    for group in groups:
      for node in group:
        node.groupSend()
    

if __name__ == "__main__":
  main()