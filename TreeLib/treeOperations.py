from .tree import Node, SyntacticNode, DiscourseNode, Tree
import codecs

class TreeOperations:

	def __init__(self, conllStringSentence):
		conllStringSentence = conllStringSentence.strip()
		if not conllStringSentence:
			raise ValueError("Please input a correct conll sentence")
			return

		self.tree = self.conll_to_tree(conllStringSentence)

	def conll_to_tree(self, conllString):
		conllArray = conllString.split("\n")
		nodes, root = self.create_nodes(conllArray)
		self.link_nodes(nodes)
		return Tree(root, nodes)

	def create_nodes(self, conllArray):
		nodeDict = {}
		root = None

		for line in conllArray:
			pieces = line.split("\t")
			idNode = int(pieces[0])
			arcLabel = pieces[4]
			parentId = int(pieces[5])
			iNode = Node(line, idNode, arcLabel, parentId)
			nodeDict[idNode] = iNode
			if parentId == idNode:
				root = iNode

		return nodeDict, root


	def link_nodes(self, nodeDict):
		for idNode, iNode in nodeDict.items():
			if iNode.parent != idNode:
				iParent = nodeDict[iNode.parent]
				iParent.addChild(iNode)
				iNode.setParent(iParent)

	
	def get_ramification_factor(self, initNode = None):
		if initNode:
			it = self.tree.getWidthIterator(initNode)
		else:
			it = self.tree.getWidthIterator()

		acumChilds = 0
		levels = 1
		for current in it:
			nchilds = len(current.children)
			if nchilds > 0:
				acumChilds+=nchilds
				levels+=1

		return acumChilds / levels

	def get_max_width(self, initNode = None):
		it = self.tree.getWidthIterator(initNode)
		maxWidth = 0

		for current in it:
			nchilds = len(current.children)
			if nchilds > maxWidth:
				maxWidth = nchilds

		return maxWidth

	def get_max_depth(self, initNode = None):
		if not initNode:
			initNode = self.tree.root

		return self.get_max_depth_recursive(initNode)


	def get_max_depth_recursive(self, node):
		depth = []

		if node:
			if not node.children:
				return 0
		if not node:
			return 0
		
		for child in node.children:
			depth.append(self.get_max_depth_recursive(child))

		return 1 + max(depth)

	def get_node_depth(self, node):
		current = node
		depth = 0
		while current.parent:
			depth+=1
			current = current.parent
		return depth

class SyntacticTreeOperations(TreeOperations):

	'''
		Gets the maximum width and depth below a node that has a given relation 
		with its father. EX: For every subordinate clause, we get the maximum value
		of width and depth of the subtree BELOW the node which has a SUB relation with its father.
	'''
	def get_relation_width_depth(self, relation):
		
		it = self.tree.getWidthIterator()
		widthDepths = []

		for current in it:
			if current.arcLabel == relation:
				width = self.get_max_width(current)
				depth = self.get_max_depth(current)
				widthDepths.append((width,depth))

		return widthDepths

	def get_relation_depth_level(self, relation):
		it = self.tree.getWidthIterator()
		levels = []
		for current in it:
			if current.arcLabel == relation:
				level = self.get_node_depth(current)
				levels.append(level)

		return levels

	def get_relation_ramification_factor(self, relation):
		it = self.tree.getWidthIterator()
		ramFactors = []
		for current in it:
			if current.arcLabel == relation:
				ramFactor = self.get_ramification_factor(current)
				ramFactors.append(ramFactor)

		return ramFactors

	def search_deps_frequency(self, searchedRels = []):

		it = self.tree.getWidthIterator()
		relFreq = {}
		searchAll = False
		if not searchedRels:
			searchAll = True

		total = 0
		for current in it:
			if current:
				for child in current.children:
					if child.arcLabel in searchedRels or searchAll:
						if child.arcLabel in relFreq:
							relFreq[child.arcLabel] +=1
						else:
							relFreq[child.arcLabel] =1
						total+=1

		return relFreq, total

	def search_pos_frequency(self, searchedPos = []):
		it = self.tree.getWidthIterator()
		posFreq = {}

		searchAll = False
		if not searchedPos:
			searchAll = True

		total = 0
		for current in it:
			if current:
				for child in current.children:
					if child.pos in searchedPos or searchAll:
						if child.pos in posFreq:
							posFreq[child.pos] +=1
						else:
							posFreq[child.pos] =1
						total+=1

		return posFreq, total

	def get_composed_verb_ratio(self):
		verbTags = ["VB","VBD","VBG","VBN","VBP","VBZ", "MD"]
		verbFreq, total = self.search_pos_frequency(verbTags)
		depFreq, vcFreq = self.search_deps_frequency(["aux","auxpass","csubj","csubjpass"])

		if vcFreq > 0 and total > 0:
			composedVerbRatio = vcFreq / total
		else:
			composedVerbRatio = 0.0

		return composedVerbRatio

	def get_modal_ratio(self):
		verbTags = ["VB","VBD","VBG","VBN","VBP","VBZ", "MD"]
		verbFreq, total = self.search_pos_frequency(verbTags)

		if total > 0 and "MD" in verbFreq:
			modalRatio = verbFreq["MD"]/ total
		else:
			modalRatio = 0.0

		return modalRatio

	def create_nodes(self, conllArray):
		nodeDict = {}
		root = None
		for line in conllArray:
			pieces = line.split("\t")
			idNode = int(pieces[0])
			arcLabel = pieces[4]
			parentId = int(pieces[5])

			iNode = SyntacticNode(line, idNode, arcLabel, parentId)
			nodeDict[idNode] = iNode
			if parentId == idNode:
				root = iNode

		return nodeDict, root

class DiscourseTreeOperations(SyntacticTreeOperations):

	def __init__(self, discourseString):
        
		lines = discourseString.split("\n") 
		lines[0] = lines[0][5:]
		root = self.createNode(lines, 0, None)
		tree = Tree(root)
		self.addChildren(tree, root, 2, lines, 1)
		self.tree = tree

	def createNode(self,lines, idx, parent):
		line = lines[idx].strip()
		node = DiscourseNode(idx, parent)
		if line.startswith("TEXT:"):
			node.arcLabel, node.meta = line.split(":", 1)
		else:
			pieces = line.split(" ", 1)
			if len(pieces) == 1:
				node.arcLabel = pieces[0]
			else:
				node.arcLabel, node.nucleous = pieces

		return node

	def addChildren(self,tree, parent, level, lines, idx):
		spaces = level
		while idx < len(lines) and spaces >= level:
			spaces = len(lines[idx]) - len(lines[idx].lstrip(" "))

			if spaces > level:
				idx = self.addChildren(tree, node, spaces, lines, idx)

			elif spaces == level:
				node = self.createNode(lines, idx, parent)
				parent.children.append(node)
				tree.nodeDict[node.id] = node

				idx += 1

		return idx