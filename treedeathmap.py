from s2r2 import ReplayManager
from sys import argv

from struct import unpack
import heatmap
import random

def test():
	x = ReplayManager(argv[1])
	x.StartPlayback()
	treemodels = []
	for key,value in x.StringSets[3].items():
		if '/props/trees/' in value:
			treemodels.append(int(key))

	#skip all initall entities states
	x.NextFrame()
	pts = []
	while x.NextFrame():
		for id in  x.addedentities:
			if x.EntityPool[id].typedesc[0] == 'Prop_Dynamic' and x.EntityPool[id]['m_hModel'] in treemodels:
				pts.append((x.EntityPool[id]['m_v3Position'][0]/32,x.EntityPool[id]['m_v3Position'][1]/32))
	hm = heatmap.Heatmap()
	pts.extend([(0,0),(511,511)])
	hm.heatmap(pts, "heatmap.png",size=(512,512),dotsize=15)
test()

