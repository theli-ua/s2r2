"""
A module to parse S2 Games S2R2 replay format used in Heroes of Newerth replays
"""
import struct
from bitarray import bitarray
from zipfile import ZipFile
import StringIO
try:
    import psyco
    psyco.full()
except ImportError:
    pass
    
FILTER=''.join([(len(repr(chr(x)))==3) and chr(x) or '.' for x in range(256)])

"""Hexdump a string"""
def dump(src, length=8):
    N=0; result=''
    while src:
        s,src = src[:length],src[length:]
        hexa = ' '.join(["%02X"%ord(x) for x in s])
        s = s.translate(FILTER)
        result += "%04X   %-*s   %s\n" % (N, length*3, hexa, s)
        N+=length
    return result

"""Decode/decompress a bitarray of fields present in entity snapshot"""
def unpack_enabled(a,count):
    if count <= 8:
        result = a.bits[a.currentbit:a.currentbit+count]
        a.ReadBits(count)
    else:   
        result = bitarray('0' * 64 * 8,endian='little')
        if not a.ReadBit():
            return result
        j = 1
        while j < count:
            j *= 2
        v21 = j 
        v10 = 0
        while 1:
            Power = v10 + 1
            if ( j <= 1 ):
                break
            v10 += 1
            j >>= 1
        result[1] = 1
        for CurrentPower in xrange ( 1, Power ):
            v11 = 2**CurrentPower
            v13 = v11
            v23 = 2 * v11
            k = v11 + 1
            while (v13 != v23):
                if result[v13 >> 1]:
                    if a.ReadBit():
                        if a.ReadBit():
                            result[v13] = 1
                        v18 = k
                    else:
                        v18 = v13
                    result[v18] = 1
                v13 += 2
                k += 2
        result = result[v21:]
    if len(result) < count:
        result.extend([False]*(count-len(result)))
    return result

"""A class simulating the same CBitBuffer used in K2 engine"""
class BitBuffer:
    def __init__(self,data):
        self.bits = bitarray(endian='little')
        #self.bits.fromstring(data)
        self.bits.frombytes(data)
        self.currentbit = 0
    def __len__(self):
        return len(self.bits) - self.currentbit
    """Pop count bytes from bitarray and return as needed type"""
    def __str__(self):
        return self.bits[self.currentbit:].__str__()
    def ReadBits(self,count,type=None):
        #print count,self.bits
        #if len(self.bits) < count:
        #   self.bits.extend([False]*(count-len(self.bits)))
        if count == 0:
            result = []
        elif count <= 8:
            result = struct.unpack('B',self.bits[self.currentbit:self.currentbit+count].tobytes())[0]
            if type == 13:
                result /= 255.0
        elif count <= 16:
            result = struct.unpack('<H',self.bits[self.currentbit:self.currentbit+count].tobytes())[0]
        elif count <=24:
            x = self.bits[self.currentbit:self.currentbit+count]
            while len(x) < 32:
                x.append(0)
            if type == 3:
                result = struct.unpack('<f',x.tobytes())[0]
            else:
                result = struct.unpack('<I',x.tobytes())[0]
        elif count <=32:
            if type == 3:
                result = result = struct.unpack('<f',self.bits[self.currentbit:self.currentbit+count].tobytes())[0]
            else:
                result = result = struct.unpack('<I',self.bits[self.currentbit:self.currentbit+count].tobytes())[0]
        else:
            result = self.bits[self.currentbit:self.currentbit+count]
        #self.bits = self.bits[count:]
        self.currentbit += count
        return result
    """Pop single bit from bitarray"""
    def ReadBit(self):
        #return self.bits.pop(0)
        self.currentbit += 1
        return self.bits[self.currentbit-1]
        

"""A frame snapshot"""
class CSnapshot:
    def __init__(self,bits):
        self.dword4 = bits.ReadBits(32)
        if bits.ReadBit():
            v2 = self.dword4 - 1;
        else:
            if bits.ReadBit():
                v2 = self.dword4 + ~self.a.ReadBits(4)
            else:
                v2 = bits.ReadBits(32)
        self.dword8 = v2
        self.dwordC = bits.ReadBits(32)
        self.byte10 = bits.ReadBits(8)
        self.byte11 = bits.ReadBits(8)
        self.dword0 = 1
        #print self.dword4,self.dword8,self.dwordC,self.byte10,self.byte11
        
        for _ in xrange(self.byte11):
            self.CGameEventTranslate(bits)

    """Get next entity from buffer or None if none :D"""
    def GetNextEntity(self,bits):
        if len(bits) > 0:
            xx = EntitySnapshot()
            xx.parse_header(bits)
            return xx
        return None
    """Translate a game event"""
    def CGameEventTranslate(self,a):
        v6 = a.ReadBits(16)
        #print v6
        v8 = 0
        if (v6 & 1):
            v8 = 4
        if ( v6 & 2 ):
            v8 += 2
        if ( v6 & 4 ):
            v8 += 6
        if ( v6 & 8 ):
            v8 += 3
        if ( v6 & 16 ):
            v8 += 2
        if ( v6 & 2048 ):
            v8 += 2
        if ( v6 & 32 ):
            v8 += 2
        if ( v6 & 64 ):
            v8 += 6
        if ( v6 & 128 ):
            v8 += 3
        if ( v6 & 256 ):
            v8 += 2
        if ( v6 & 4096 ):
            v8 += 2
        if ( v6 & 512 ):
            v8 += 2
        if ( v6 & 1024 ):
            v8 += 2
        if ( v6 & 32768 ):
            v8 += 2
        #print 'CGameEventTranslate\t %d bytes' % v8
        for _ in xrange(v8):
            #print a.ReadBits(8)
            a.ReadBits(8)
            
"""A class for entity snapshot (simulating K2's CEntitySnapshot)"""     
class EntitySnapshot:
    def __init__(self):
        self.flags = 7
        self.EntityIndex = 0
        self.id = -1
        self.typedesc = None
        self.Fields = []
    """Get entity field length from field's type"""
    def entity_length(self,x):
        if x in [0,8,13]:
            return 1
        if x in [1,6,7,9,10,11,12,15]:
            return 2
        if x in [2,3,16]:
            return 4
        if x in [4]:
            return 8
        if x in [5]:
            return 12
        if x in [14,17]:
            return 6
        return 0
    """Parse header for entity from bitarray"""
    def parse_header(self,bits):
        if bits.ReadBit():
            self.id = bits.ReadBit();
            if self.id == False:
                if bits.ReadBit():
                    self.id = 1 + bits.ReadBits(4)
                else:
                    if bits.ReadBit():
                        self.id = 0x11 + bits.ReadBits(8)
                    else:
                        self.id = 0x111 + bits.ReadBits(15)
            else:
                self.id = 1
            if bits.ReadBit():
                self.flags |= 2
                self.EntityIndex = bits.ReadBits(16)
            else:
                self.flags &= 0xFFFFFFFD
            
            if bits.ReadBit():
                self.flags |= 4
            else:
                self.flags &= 0xFFFFFFFB
        else:
            self.flags = (self.flags | 4) & 0xFFFFFFFD
        #print self.EntityIndex,self.flags,self.id#,len(self.a)
    def parse_body(self,bits,typedesc):
        self.typedesc = typedesc # (name,u32,entities,es)
        self.enabledFields = unpack_enabled(bits,len(typedesc[2]))
        self.Fields = [None] * len(typedesc[2])
        for ii,ent in enumerate(typedesc[2]):
            if self.enabledFields[ii]:
                if ent[1] in [15,16,17]:
                    self.Fields[ii] = []
                    for v14 in xrange(ent[1] - 14):
                        if bits.ReadBit():
                            v18 = bits.ReadBits(5)
                        else:
                            if bits.ReadBit():
                                v18 = bits.ReadBits(6) + 32
                            else:
                                v18 = bits.ReadBits(15)
                        if (v18 & 1):
                            v37 = (-1 - v18) >> 1
                        else:
                            v37 = v18 >> 1
                        self.Fields[ii].append(v37)
                else:
                    if ent[2] != 0:
                        length = ent[2]
                    else:
                        length = 8*self.entity_length(ent[1])
                    self.Fields[ii] = bits.ReadBits(length,type=ent[1])
            else:
                self.Fields[ii] = typedesc[3].Fields[ii]
    """Fancy output"""
    def __str__(self):
        if not self.typedesc:
            return 'Empty entity snapshot'
        output = '\n' + self.typedesc[0] + '\n'
        for i,field in enumerate(self.Fields):
            output += '\t' + self.typedesc[2][i][0] + ': ' + str(field) + '\n'
        return output
    def applydiff(self,es):
        if (es.flags & 4) != 0:
            self.flags |= 4
        else:
            self.flags &= 0xFFFFFFFB
        for i in xrange(len(self.typedesc[2])):
            if es.enabledFields[i]:
                if self.typedesc[2][i][1] in [15,16,17]:
                    for n in xrange(len(self.Fields[i])):
                        self.Fields[i][n] += es.Fields[i][n]
                else:
                    self.Fields[i] = es.Fields[i]
    def calcSnapshotSize(self):
        len = 0
        for ent in self.entities:
            len+=entity_length(ent[1])
        return len
    """Dict-like interface"""
    def __getitem__(self, key):
        keys = [k for (k,x,y,z) in self.typedesc[2]]
        if key not in keys:
            raise KeyError('No such field for this entity')
        return self.Fields[keys.index(key)]
    def keys(self):
        return [k for (k,x,y,z) in self.typedesc[2]]
    def values(self):
        return self.Fields
        
from xml.dom.minidom import parse
"""Small class for holding data from replayinfo xml file"""
class ReplayInfo:
    def __init__(self,replayinfo):
        pass
        
            
"""Class holding all of the replay information"""
class ReplayManager:
    def __init__(self,honreplay):
        self.formatversion = 0
        self.serverversion = '0'
        self.EntityPool = {}
        self.currentframe = 0
        self.replaydata = None
        self.zipfile = ZipFile(honreplay,'r')
        self.replayinfo = ReplayInfo(self.zipfile.open('replayinfo','r'))
        self.TypeDesc = [{},{}]
        self.TypeMap = {}
        self.EntityMap = {}
        self.StringSets = []
        self.StateBlocks = []
        self.MapName = ''
        self.state1count = 0
        self.framenum = -1
        self.changedentities = []
        self.addedentities = []
        self.deletedentities = []
    def read_int(self):
        return struct.unpack("<I",self.replaydata.read(4))[0]
    def read_int16(self):
        return struct.unpack("<H",self.replaydata.read(2))[0]
    def read_float(self):
        return struct.unpack("<f",self.replaydata.read(4))[0]
    def read_byte(self):
        return struct.unpack("B",self.replaydata.read(1))[0]
    def read_str(self):
        str = ''
        b = self.replaydata.read(1)
        while b != '\0':
            str += b
            b = self.replaydata.read(1)
        return str
    def read_str2(self):
        str = ''
        b = self.replaydata.read(1)
        while b != 0xff:
            str += b
            b = self.replaydata.read(1)
        return str
    def parse_string_set(self,str):
        data = str.split(chr(0xFF))
        return dict(zip(data[:-1:2], data[1::2]))
        #return zip(data[:-1:2], data[1::2])
    """Start a playback - parse everything before the first server frame"""
    def StartPlayback(self):
        #self.replaydata = self.zipfile.open('replaydata','r')
        self.replaydata = StringIO.StringIO(self.zipfile.read('replaydata'))
        if self.replaydata.read(4) != 'S2R2':
            raise ValueError('Header of replaydata does not match')
        self.formatversion = self.read_int()
        self.serverversion = '%d.%d.%d.%d' % tuple(self.read_byte() for i in range(4))
        #read entity type descriptions along with default values
        for i in xrange(2):
            varnum = self.read_int()
            for _ in xrange(varnum):
                u16 = self.read_int16()
                name = self.read_str()
                u32 = self.read_int()
                #print u16,name,u32 #u32 always == 1
                count = self.read_byte()
                entities = []
                for x in xrange(count):
                    str = self.read_str()
                    c = self.read_byte()
                    unk1 = self.read_int()
                    unk2 = self.read_int()
                    entities.append((str,c,unk1,unk2))
                snapshot_length = self.read_int16()
                entity_snapshot = self.replaydata.read(snapshot_length)
                bits = BitBuffer(entity_snapshot)
                es = EntitySnapshot()
                es.parse_header(bits)
                typedesc = (name,u32,entities,None)
                es.parse_body(bits,typedesc)
                self.TypeDesc[i][u16] = (name,u32,entities,es)
                #print es
        
        for _ in xrange(self.read_int()):
            u1 = self.read_int16()
            u2 = self.read_int16()
            self.TypeMap[u1] = u2
            
        self.MapName = self.read_str()
        
        if self.formatversion > 3:
            count = self.read_int()
        else:
            count = 5

        self.StringSets = [self.parse_string_set(self.read_str()) for _ in xrange(count - 1)] 
        
        if self.formatversion > 3:
            count = self.read_int()
        else:
            count = 3
            
        self.StateBlocks = [self.replaydata.read(self.read_int()) for _ in xrange(count - 1)]
        self.state1count = ((len(self.StateBlocks[0]) / 4) + 31) / 32
        self.state2count = len(self.StateBlocks[1]) / 6
        
        self.EntityMap = dict([struct.unpack("<HI",self.StateBlocks[1][_*6:_*6+6]) for _ in xrange(self.state2count)])
    def FindClient(self,index):
        for es in (es for es in self.EntityPool.values() if es.typedesc[0] == 'Player' and es['m_iClientNumber'] == index):
            return es
        return None
    def NextFrame(self):
        try:
            length = self.read_int()
        except:
            return False
        if length > 0 :
            bits = BitBuffer(self.replaydata.read(length))
            snapshot = CSnapshot(bits)
            if self.state1count > 0:
                x = unpack_enabled(bits,self.state1count)
                for _ in xrange(len(x)):
                    if x[_]:
                        #print 
                        bits.ReadBits(32)
            id = 0
            es = snapshot.GetNextEntity(bits)
            self.changedentities = []
            self.addedentities = []
            self.deletedentities = []
            while es != None:
                Index = es.EntityIndex
                if es.id == -1:
                    maxid = sorted(self.EntityPool.keys())[-1]
                    while id <= maxid:
                        id += 1
                        if id in self.EntityPool and (self.EntityPool[id].flags & 4):
                            break
                    if id > maxid:
                        break
                else:
                    id += es.id
                #print 'id=0x%x' % id
                #if framenum == 10544 and id==0xf60:
                #   pdb.set_trace()
                if Index == 0 and es.flags & 2:
                    del self.EntityPool[id]
                    self.deletedentities.append(id)
                    es = snapshot.GetNextEntity(bits)
                    continue
                if (Index == 0):
                    es.parse_body(bits,self.EntityPool[id].typedesc)
                elif Index < 256:
                    es.parse_body(bits,self.TypeDesc[0][Index])
                else:
                    es.parse_body(bits,self.TypeDesc[1][self.TypeMap[Index]])

                if es.flags & 2:# and id not in self.EntityPool:
                    #if es.EntityIndex == 0: es.EntityIndex = self.EntityPool[id].EntityIndex
                    self.EntityPool[id] = es
                    self.addedentities.append(id)
                else:
                    if es.enabledFields.any():
                        self.changedentities.append(id)
                    
                    self.EntityPool[id].applydiff(es)
                es = snapshot.GetNextEntity(bits)
        count = self.read_int()
        for i in xrange(count):
            x = self.read_int() #receiver player id
            #print 'receiver client id: %d' % x
            y = self.read_int() #packet length
            if y > 0:
                z = self.replaydata.read(y)
                #print dump(z)
                if z[0] == chr(2) or z[0] == chr(3) or z[0] == chr(0):#0x28): #<- system message
                    msg = z[4:z.index('\0',5)]
                    who = struct.unpack("<i",z[1:5])[0]
                    #who = string_sets[2][`who`] #wrong :(
                    if z[0] == chr(3):
                        pre = '[TEAM]'
                    else:
                        pre = '[ALL]'
                    print '[][]%s[%d=>%d]%s' % (pre,who,x,msg)
                elif z[0] == '5':
                    print 'spawn?' ,dump(z)
                else:
                    print 'xx :',dump(z)
        count = self.read_int()
        for i in xrange(count):
            x = self.read_int()
            y = self.read_int()
            if y > 0:
                z = self.replaydata.read(y)
                #print dump(z)
                #print ord(z[0])
                #print dump(z)

        count = self.read_int()
        for i in xrange(count):
            a = self.read_int()
            b = self.parse_string_set(self.read_str())
            #print '\t' , a,b
            self.StringSets[a-1] = b
        if self.formatversion > 3:
            count = self.read_int()
            for i in xrange(count):
                a = self.read_int()
                b = self.read_int()
                #print a,b
                self.replaydata.read(b)
        self.framenum+=1
        return True
        
        
