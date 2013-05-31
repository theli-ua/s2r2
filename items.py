from s2r2 import ReplayManager
from sys import argv

from struct import unpack

def test():
	x = ReplayManager(argv[1])
	x.StartPlayback()
	while x.NextFrame():
		for id in (id for id in x.addedentities if x.EntityPool[id].typedesc[0] == 'Item'):
			
			print '___________________\nItem purchase, entity id %d' % id
		#	print 'framenum %d' % x.framenum
			print 'Item: ' + x.StringSets[3][str(x.EntityMap[x.EntityPool[id].EntityIndex])]
		#	print x.EntityPool[id]
			print 'Owner Hero: ' + x.StringSets[3][str(x.EntityMap[x.EntityPool[x.EntityPool[id]['m_uiOwnerIndex']].EntityIndex])]
		#	print 'Time: %d' % x.EntityPool[id]['m_uiPurchaseTime']
		#	#owner hero entity
		#	print x.EntityPool[x.EntityPool[id]['m_uiOwnerIndex']]
		#	
			owner = x.FindClient(x.EntityPool[id]['m_iPurchaserClientNumber'])
			if owner:
				#print owner['m_unNameIndex']
				#print owner
				print 'Purchaser: ' + x.StringSets[2][str(owner['m_unNameIndex'])]
		#	#ownerindex = x.EntityPool[x.EntityPool[id]['m_uiOwnerIndex']]['m_uiOwnerEntityIndex']
		#	#if ownerindex != 65535:
		#	#	print 'Purchaser: ' + x.StringSets[2][str(x.EntityPool[ownerindex]['m_unNameIndex'])]
		if len(x.deletedentities) > 0:
			print 'deleted ', x.deletedentities
		pass
	

	

test()

