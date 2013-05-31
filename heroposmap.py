from s2r2 import ReplayManager
from sys import argv

from struct import unpack
import heatmap
import random

def test():
	x = ReplayManager(argv[1])
	x.StartPlayback()
	madmanid = None
	pts = []
	while not madmanid:
		x.NextFrame()
		for id in  [id for id in x.addedentities if x.EntityPool[id].typedesc[0] == 'Hero']:
			if 'scar' in x.StringSets[3][str(x.EntityMap[x.EntityPool[id].EntityIndex])]:
				madmanid = id
	
	while x.NextFrame():
		#m_yStatus == 0 -- dead
		if x.EntityPool[madmanid]['m_yStatus'] != 0:
			pts.append((x.EntityPool[madmanid]['m_v3Position.xy'][0]/32,x.EntityPool[madmanid]['m_v3Position.xy'][1]/32))
	hm = heatmap.Heatmap()
	pts.extend([(0,0),(511,511)])
	hm.heatmap(pts, "madman.png",size=(512,512),dotsize=15)
test()

