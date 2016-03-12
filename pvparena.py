import os, sys
from copy import deepcopy
import random
import time

n_kol = 20  #WARNING SECURITY CHANGE ME

kolo = 0 
debug = True

#TODO best
class Hrac:
    def __init__(self, stats = (0,0,0,0), name = "p" ):
        self.name = name
        self.stats = list(stats)
        self.hp = 0
        self.old_hp = 0
        self.buffs = []
        self.spells = []
        self.dmgdone = 0
        self.multicast = False
        self.copy = False
        self.last = False
    
    def check(self):
        delta = self.hp-self.old_hp
        self.old_hp = self.hp
        self.dmgdone = 0
        self.stats = map(int, self.stats)
        return delta
    
    def recv_dmg(self, kolko, typ = ()):
        multip = 1.
        for b in self.buffs[:]:
            if b.typ == 1 and b.start == kolo-2:
                multip *= 2
            if b.typ == 6:
                multip *= 0.5
            if b.typ == 7 and (kolo <= b.start+3):
                multip *= 0.25
            if b.typ == 25.1 and (kolo <= b.start+3):
                multip *= 0.9
            if b.typ == 25.6 and (kolo <= b.start+3):
                multip *= 1.1
            if b.typ == 26.5 and (kolo <= b.start+4):
                multip *= 1.5
            
        nowdone = int(multip*kolko)
        self.dmgdone += nowdone
        self.hp -= nowdone
    
    def recv_heal(self, kolko, typ = ()):
        multip = 1.
        for b in self.buffs[:]:
            if b.typ == 7 and (kolo <= b.start+3):
                multip *= 0.5
        self.hp += int(kolko*multip)
        
    
    def rooted(self):
        for b in self.buffs[:]:
            if b.typ == 12 and b.start == kolo-1:
                return True
        return False
    
    def root_times(self):
        ret = 0
        for b in self.buffs[:]:
            if b.typ == 12 and b.start == kolo-1:
                ret+=1
        return ret
    
    def __str__(self):
        return self.name +" "+ str(self.stats) +" "+ str(self.hp)

    def buffprint(self):
        for b in self.buffs:
            print str(b)

class Buff():
    def __init__(self, typ, tags=tuple(), stat=None):
        tags = list(tags)
        self.start = kolo
        self.typ = typ
        self.tags = tags
        self.stat = stat
    
    def __str__(self):
        return "%s %s %s %s"%(self.start, self.typ, self.tags, self.stat)
    
    
        
def send_dmg(hrac1, hrac2, val, dot = False):
    if hrac1.rooted() and not dot:
        val = 0
    multip = 1.
    for b in hrac1.buffs[:]:
        if b.typ == 26 and (kolo <= b.start+4):
            multip *= 1.5
    
    hrac2.recv_dmg(val*multip)

def send_heal(hrac1, hrac2, val, dot = False):
    if hrac1.rooted() and not dot:
        val = int(val* (0.5**hrac1.root_times()))
    hrac2.recv_heal(val)

def purgep(hrac, tag):
    hrac.buffs = filter(lambda b: tag not in b.tags, hrac.buffs)

def nothing(hrac1, hrac2, stat):
    print "nothing"
    pass

def dmg(hrac1, hrac2, stat):
    tosend = 2*hrac1.stats[stat]
    send_dmg (hrac1, hrac2, tosend)


def dmgdouble(hrac1, hrac2, stat):
    tosend = hrac1.stats[stat]
    send_dmg (hrac1, hrac2, tosend)
    hrac2.buffs.append(Buff(1,["neg"]))

def heal(hrac1, hrac2, stat):
    tosend = 2*hrac1.stats[stat]
    send_heal(hrac1, hrac1, tosend)
    
    
def hot(hrac1, hrac2, stat, buff = False):
    tosend = hrac1.stats[stat]*0.5
    send_heal(hrac1, hrac1,tosend)
    if not buff:
        hrac1.buffs.append(Buff(3,["pos"],stat=stat))

def purge(hrac1, hrac2, stat):
    tosend = hrac1.stats[stat]
    send_heal(hrac1, hrac1, tosend)
    if not hrac1.last:
        purgep(hrac1, "neg")

def dot(hrac1, hrac2, stat):
    hrac2.buffs.append(Buff(5,["neg"],stat=stat))

def dottick(hrac1, hrac2, stat):
    tosend = hrac1.stats[stat]*0.5
    hrac2.recv_dmg(tosend)
    
def shield(hrac1, hrac2, stat):
    hrac1.buffs.append(Buff(6,["pos"]))

def skin(hrac1, hrac2, stat):
    hrac1.buffs.append(Buff(7,["pos"]))

def statup(hrac1, hrac2, stat):
    hrac1.stats[stat]+=10

def upir(hrac1, hrac2, stat):
    tosend = hrac1.stats[stat]
    send_dmg (hrac1, hrac2, tosend)
    
def multicast(hrac1, hrac2, stat):
    hrac1.multicast = True
    
def sot(hrac1, hrac2, stat, buff = False):
    hrac1.stats[stat] += 4
    if not buff:
        hrac1.buffs.append(Buff(11,["pos"],stat=stat))

def root(hrac1, hrac2, stat):
    hrac2.buffs.append(Buff(12,["neg"]))
    pass

def scopy(hrac1, hrac2, stat):
    hrac1.copy = True


def flame(hrac1, hrac2, stat):
    tosend = hrac1.stats[stat]*min(kolo, n_kol - kolo)/2
    
    if not hrac1.last:
        purgep(hrac2, "neg")
        purgep(hrac2, "pos")
    send_dmg (hrac1, hrac2, tosend)
    
    
def sac(hrac1, hrac2, stat):
    hrac1.buffs.append(Buff(15,["pos"], stat=stat))
    sactick(hrac1, stat) 

def sactick(hrac1, stat):
    minn = min(hrac1.stats)
    i_minn = hrac1.stats.index(minn)
    hrac1.stats[i_minn] = max(0, hrac1.stats[i_minn] - 2)
    if hrac1.stats[i_minn]==0:
        tosend = hrac1.stats[stat]*2
        send_dmg(hrac1, hrac1, tosend, dot=True)
        for i,b in enumerate(hrac1.buffs[::-1]):
            if b.typ == 15:
                del hrac1.buffs[0-1-i]
                break
        
    else:
        hrac1.stats[stat]+=7
    pass

def bless(hrac1, hrac2, stat):
    hrac1.buffs.append(Buff(16,["pos"], stat=stat))


def steal(hrac1, hrac2, stat):
    stealtick(hrac1, hrac2, stat, addnum =3)

    
def stealtick(hrac1, hrac2, stat, addnum = 2):
    for i in xrange(addnum):
        hrac1.buffs.append(Buff(17,["pos"], stat=stat))
    
    diff = min(1, hrac2.stats[stat])
    hrac1.stats[stat] += diff
    hrac2.stats[stat] -= diff
    

def pact(hrac1, hrac2, stat): 
    m = max(hrac1.stats)
    m_i = hrac1.stats.index(m)
    hrac1.stats[m_i] = (m*0.9)
    if not hrac1.last:
        purgep(hrac1, "neg")
        purgep(hrac2, "pos")


def change(hrac1, hrac2, stat, back = False):
    pom = hrac1.stats[stat]
    hrac1.stats[stat] = hrac2.stats[stat]
    hrac2.stats[stat] = pom
    
    if not back:
        hrac1.buffs.append(Buff(19, stat=stat))
        tosend = hrac1.stats[stat]*2.5
        send_dmg(hrac1, hrac2, tosend)
        


def eql(hrac1, hrac2, stat):
    h1has = set([b.typ for b in hrac1.buffs])
    
    h2has = set([b.typ for b in hrac2.buffs])
    
    for b in filter(lambda b: "pos" in b.tags or "neg" in b.tags,
                    hrac1.buffs[::-1]):
        if b.typ not in h2has:
            h2has.add(b.typ)
            hrac2.buffs.append(deepcopy(b))
    
    for b in filter(lambda b: "pos" in b.tags or "neg" in b.tags,
                    hrac2.buffs[::-1]):
        if b.typ not in h1has:
            h1has.add(b.typ)
            hrac1.buffs.append(deepcopy(b))
    

def madness(hrac1, hrac2, stat):
    tosend = hrac1.stats[stat];
    send_dmg (hrac1, hrac2, tosend)
    if not hrac1.last:
        purgep(hrac2, "pos")
    

def posses(hrac1, hrac2, stat):
    tosend = hrac1.stats[stat]*1.5
    send_dmg(hrac1, hrac2, tosend)
    hrac1.buffs.append(Buff(22))

def lightning(hrac1, hrac2, stat):
    tosend = sum(hrac1.stats)
    send_dmg (hrac1, hrac2, tosend)

def soulburn(hrac1, hrac2, stat): 
    s = map(list, zip(hrac1.stats, [random.random() for x in xrange(4)], range(4)))
    s = sorted(s, key= lambda x: x[0])
    mults = [0.5,0.3,0.15,0.05]
    for i, x in enumerate(s):
        s[i][0] *= (1.-mults[i])
    s = sorted(s, key = lambda x:x[2])
    hrac1.stats=list(map(lambda x: int(x[0]),s))
    
def suck(hrac1, hrac2, stat):
    hrac1.buffs.append(Buff(25,["pos"]))
    hrac2.buffs.append(Buff(25.5,["neg"]))

def rage(hrac1, hrac2, stat):
    hrac1.buffs.append(Buff(26,["pos"], stat=stat))
    hrac2.buffs.append(Buff(26.5,["neg"], stat=stat))
    

def last(hrac1, hrac2, stat):
    hrac2.last = True

def supstr(hrac1, hrac2, stat):
    small = sorted(hrac1.stats)[:2]
    tosend = small[0]*small[1]
    send_dmg (hrac1, hrac2, tosend)

def broken(hrac1, hrac2, stat):
    tosend = hrac1.stats[stat]*2
    send_dmg(hrac1, hrac1, tosend)
    send_heal(hrac1, hrac1, tosend)
    if not hrac1.last:
        purgep(hrac1,"pos")
        purgep(hrac1,"neg")
        
    #root bug

codes= {
    0: dmg,       #0
    1: dmgdouble, #4
    2: heal,      #8
    3: hot,       #12
    4: purge,     #16
    5: dot,       #20
    6: shield,    #24
    7: skin,      #28
    8: statup,    #32
    9: upir,      #36
    10: multicast,#40
    11: sot,      #44
    12: root,     #48
    13: scopy,    #52
    14: flame,    #56
    15: sac,      #60
    16: bless,    #64
    17: steal,    #68
    18: pact,     #72
    19: change,   #76
    20: eql,      #80
    21: madness,  #84
    22: posses,   #88
    23: lightning,#92
    24: soulburn, #96
    25: suck,     #100
    26: rage,     #104
    27: last,     #108
    28: supstr,   #112
    29: broken,   #116
    }



d = ""
try:
    f = open("spellmaper")
    d = map(lambda x: x.strip().split(), f.read().split('\n'))
    f.close()
except:
    print "no spell maper file"
spellmaper = {
        int(x[0]): " ".join(x[1:]) for x in filter(lambda q:len(q)>=2, d)
    }


statmap={ 
            0:"wis",
            1:"str",
            2:"agi",
            3:"int"
        }
         

def totallog(x):
    f = open("totallog","a+")
    f.write(x+"\n")
    f.close()

def main(): 
    global kolo, n_kol
    random.seed()
    print """USAGE: optional id najlepsieho, a jeho stat """
    argv = sys.argv[1:]
    best = None
    stat_best = None
    print argv
    if len(argv)==2:
        best = int(argv[0])
        stat_best = int(argv[1])
        print "najlepsi je %d a stat je %s"%(best,
                                             statmap[stat_best])
    print "id + 4 staty wis, str, agi, int"
    print "zadaj hraca1 hraca "
    stats1 = map(int,raw_input().split())
    assert len(stats1)==5
    
    print "zadaj hraca2 hraca"
    stats2 = [10,5,5,5]
    stats2 = map(int,raw_input().split())
    
    assert len(stats2)==5
    
    hraci = [Hrac(stats1[1:], "hrac %d"%stats1[0]), Hrac(stats2[1:],"hrac %d"%stats2[0])]
    
    totallog("####")
    totallog(str(argv))
    totallog("$$$$")
    totallog("%f %s %s"%( time.time(), hraci[0], hraci[1]))
    if best!=best:
        for h in hraci:
            h.stats[stat_best]*=2
            if h.name == "hrac %d"%best:
                h.stats[stat_best]+=5
            
    seed = random.randint(0,1)
    #seed = 0
    print "seed je %d"%seed
    while kolo < n_kol:
        print
        print "###############################"
        print "kolo: ", kolo
        for j in xrange(2):
            print 
            ide = (j+seed)%2
            nejde = (j+1+seed)%2
            print "ide ", hraci[ide].name
            hraci[ide].check()
            hraci[nejde].check()
            
            for b in hraci[ide].buffs[:]: 
                if b.typ == 19 and kolo == b.start+4:
                    change(hraci[ide], hraci[nejde], b.stat, back=True)
                if b.typ == 22 and kolo == b.start+4:
                    purgep(hraci[nejde], "pos")
                    
                if b.typ == 3:
                    hot(hraci[ide], hraci[nejde], b.stat, buff=True)
                if b.typ == 11:
                    sot(hraci[ide], hraci[nejde], b.stat, buff=True)
                if b.typ == 15:
                    sactick(hraci[ide], b.stat)
                if b.typ == 16 and kolo <= b.start+2:
                    if not hraci[nejde].last:
                        purgep(hraci[nejde], "pos")
                if b.typ == 17:
                    stealtick(hraci[ide], hraci[nejde], b.stat)
                if b.typ == 25:
                    hraci[ide].buffs.append(Buff(25.1,["pos"]))
                
                
            
            akcie = map(int,raw_input().split())
            totallog(str(hraci[ide]))
            totallog(str(akcie))
            totallog("****")
            
            if hraci[ide].copy:
                hraci[ide].copy = False
                for a in hraci[nejde].spells[::-1]:
                    if a/4 not in [13,10]:
                        akcie.append(a)
                        
                        break
            
            
            for akcia in akcie:
                multicast_n = 1
                if hraci[ide].multicast:
                    hraci[ide].multicast = False
                    rnd = random.random()
                    if rnd<0.75:
                        multicast_n+=1
                    if rnd < 0.25:
                        multicast_n+=1
                    print "multicast %d"%(multicast_n)
                
                for i in xrange(multicast_n):
                    codes.get(akcia/4, nothing)(hraci[ide], hraci[nejde], akcia%4)
                hraci[ide].spells.append(akcia)
            
            
            for b in hraci[nejde].buffs[:]:
                if b.typ == 25.5:
                    hraci[ide].buffs.append(Buff(25.6,["neg"]))
                
                if b.typ == 5:
                    dot(hraci[ide], hraci[nejde], b.stat)
                    dottick(hraci[ide], hraci[nejde], b.stat)
            
            dmgdone = hraci[nejde].dmgdone
            print "akcie:"
            for a in akcie:
                print a, spellmaper.get(a,"dont know") 
                if a/4 == 9:
                    send_heal(hraci[ide], hraci[ide], dmgdone*0.5)
                    
            hraci[ide].last = False
            dif1 = hraci[ide].check()
            dif2 = hraci[nejde].check()
            print "Ako sa zmenilo hp"
            print hraci[ide].name, ":", dif1
            print hraci[nejde].name, ":", dif2
            kolo+=1
            
            
        if debug:
            print 
            print "DEBUG"
            print str(hraci[0])
            hraci[0].buffprint()
            print
            print str(hraci[1])
            hraci[1].buffprint()
            print 
        
        
    print
    print "Vysledky:"
    print "Hrac %s ma %d zivota"%(hraci[0].name, hraci[0].hp )
    print "Hrac %s ma %d zivota"%(hraci[1].name, hraci[1].hp )
    
    f = open("logfile","a+")
    f.write("%f %s %d %s %d\n"%( time.time(),hraci[0].name, 
            hraci[0].hp,hraci[1].name, hraci[1].hp))
    f.close()
    
    pass


if __name__ == "__main__":
    main();



