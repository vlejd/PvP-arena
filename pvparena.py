import os
import sys
from copy import deepcopy
import random
import time
from hrac import Hrac

total_rounds = 20
round_n = 0
debug = True


class Buff():
    def __init__(self, typ, tags=tuple(), stat=None):
        tags = list(tags)
        self.start = round_n
        self.typ = typ
        self.tags = tags
        self.stat = stat

    def __str__(self):
        return "%s %s %s %s" % (self.start, self.typ, self.tags, self.stat)


def send_dmg(player1, player2, val, dot=False):
    if player1.rooted() and not dot:
        val = 0
    multip = 1.
    for b in player1.buffs[:]:
        if b.typ == 26 and (round_n <= b.start+4):
            multip *= 1.5

    player2.recv_dmg(val*multip)


def send_heal(player1, player2, val, dot=False):
    if player1.rooted() and not dot:
        val = int(val * (0.5**player1.root_times()))
    player2.recv_heal(val)


def purgep(player, tag):
    player.buffs = filter(lambda b: tag not in b.tags, player.buffs)


def nothing(player1, player2, stat):
    print("nothing")
    pass


def dmg(player1, player2, stat):
    tosend = 2*player1.stats[stat]
    send_dmg(player1, player2, tosend)


def dmgdouble(player1, player2, stat):
    tosend = player1.stats[stat]
    send_dmg(player1, player2, tosend)
    player2.buffs.append(Buff(1, ["neg"]))


def heal(player1, player2, stat):
    tosend = 2*player1.stats[stat]
    send_heal(player1, player1, tosend)


def hot(player1, player2, stat, buff=False):
    tosend = player1.stats[stat]*0.5
    send_heal(player1, player1, tosend)
    if not buff:
        player1.buffs.append(Buff(3, ["pos"], stat=stat))


def purge(player1, player2, stat):
    tosend = player1.stats[stat]
    send_heal(player1, player1, tosend)
    if not player1.last:
        purgep(player1, "neg")


def dot(player1, player2, stat):
    player2.buffs.append(Buff(5, ["neg"], stat=stat))


def dottick(player1, player2, stat):
    tosend = player1.stats[stat]*0.5
    player2.recv_dmg(tosend)


def shield(player1, player2, stat):
    player1.buffs.append(Buff(6, ["pos"]))


def skin(player1, player2, stat):
    player1.buffs.append(Buff(7, ["pos"]))


def statup(player1, player2, stat):
    player1.stats[stat] += 10


def upir(player1, player2, stat):
    tosend = player1.stats[stat]
    send_dmg(player1, player2, tosend)


def multicast(player1, player2, stat):
    player1.multicast = True


def sot(player1, player2, stat, buff=False):
    player1.stats[stat] += 4
    if not buff:
        player1.buffs.append(Buff(11, ["pos"], stat=stat))


def root(player1, player2, stat):
    player2.buffs.append(Buff(12, ["neg"]))


def scopy(player1, player2, stat):
    player1.copy = True


def flame(player1, player2, stat):
    tosend = player1.stats[stat]*min(round_n, total_rounds - round_n)/2

    if not player1.last:
        purgep(player2, "neg")
        purgep(player2, "pos")
    send_dmg(player1, player2, tosend)


def sac(player1, player2, stat):
    player1.buffs.append(Buff(15, ["pos"], stat=stat))
    sactick(player1, stat)


def sactick(player1, stat):
    minn = min(player1.stats)
    i_minn = player1.stats.index(minn)
    player1.stats[i_minn] = max(0, player1.stats[i_minn] - 2)
    if player1.stats[i_minn] == 0:
        tosend = player1.stats[stat]*2
        send_dmg(player1, player1, tosend, dot=True)
        for i, b in enumerate(player1.buffs[::-1]):
            if b.typ == 15:
                del player1.buffs[0-1-i]
                break

    else:
        player1.stats[stat] += 7
    pass


def bless(player1, player2, stat):
    player1.buffs.append(Buff(16, ["pos"], stat=stat))


def steal(player1, player2, stat):
    stealtick(player1, player2, stat, addnum=3)


def stealtick(player1, player2, stat, addnum=2):
    for i in xrange(addnum):
        player1.buffs.append(Buff(17, ["pos"], stat=stat))

    diff = min(1, player2.stats[stat])
    player1.stats[stat] += diff
    player2.stats[stat] -= diff


def pact(player1, player2, stat):
    m = max(player1.stats)
    m_i = player1.stats.index(m)
    player1.stats[m_i] = (m*0.9)
    if not player1.last:
        purgep(player1, "neg")
        purgep(player2, "pos")


def change(player1, player2, stat, back=False):
    pom = player1.stats[stat]
    player1.stats[stat] = player2.stats[stat]
    player2.stats[stat] = pom

    if not back:
        player1.buffs.append(Buff(19, stat=stat))
        tosend = player1.stats[stat]*2.5
        send_dmg(player1, player2, tosend)


def eql(player1, player2, stat):
    h1has = set([b.typ for b in player1.buffs])

    h2has = set([b.typ for b in player2.buffs])

    for b in filter(lambda b: "pos" in b.tags or "neg" in b.tags,
                    player1.buffs[::-1]):
        if b.typ not in h2has:
            h2has.add(b.typ)
            player2.buffs.append(deepcopy(b))

    for b in filter(lambda b: "pos" in b.tags or "neg" in b.tags,
                    player2.buffs[::-1]):
        if b.typ not in h1has:
            h1has.add(b.typ)
            player1.buffs.append(deepcopy(b))


def madness(player1, player2, stat):
    tosend = player1.stats[stat]
    send_dmg(player1, player2, tosend)
    if not player1.last:
        purgep(player2, "pos")


def posses(player1, player2, stat):
    tosend = player1.stats[stat]*1.5
    send_dmg(player1, player2, tosend)
    player1.buffs.append(Buff(22))


def lightning(player1, player2, stat):
    tosend = sum(player1.stats)
    send_dmg(player1, player2, tosend)


def soulburn(player1, player2, stat):
    s = map(list, zip(player1.stats, [random.random() for x in xrange(4)], range(4)))
    s = sorted(s, key=lambda x: x[0])
    mults = [0.5, 0.3, 0.15, 0.05]
    for i, x in enumerate(s):
        s[i][0] *= (1.-mults[i])
    s = sorted(s, key=lambda x: x[2])
    player1.stats = list(map(lambda x: int(x[0]), s))


def suck(player1, player2, stat):
    player1.buffs.append(Buff(25, ["pos"]))
    player2.buffs.append(Buff(25.5, ["neg"]))


def rage(player1, player2, stat):
    player1.buffs.append(Buff(26, ["pos"], stat=stat))
    player2.buffs.append(Buff(26.5, ["neg"], stat=stat))


def last(player1, player2, stat):
    player2.last = True


def supstr(player1, player2, stat):
    small = sorted(player1.stats)[:2]
    tosend = small[0]*small[1]
    send_dmg(player1, player2, tosend)


def broken(player1, player2, stat):
    tosend = player1.stats[stat]*2
    send_dmg(player1, player1, tosend)
    send_heal(player1, player1, tosend)
    if not player1.last:
        purgep(player1, "pos")
        purgep(player1, "neg")


codes = {
    0: dmg,         # 0
    1: dmgdouble,   # 4
    2: heal,        # 8
    3: hot,         # 12
    4: purge,       # 16
    5: dot,         # 20
    6: shield,      # 24
    7: skin,        # 28
    8: statup,      # 32
    9: upir,        # 36
    10: multicast,  # 40
    11: sot,        # 44
    12: root,       # 48
    13: scopy,      # 52
    14: flame,      # 56
    15: sac,        # 60
    16: bless,      # 64
    17: steal,      # 68
    18: pact,       # 72
    19: change,     # 76
    20: eql,        # 80
    21: madness,    # 84
    22: posses,     # 88
    23: lightning,  # 92
    24: soulburn,   # 96
    25: suck,       # 100
    26: rage,       # 104
    27: last,       # 108
    28: supstr,     # 112
    29: broken,     # 116
    }

d = ""
try:
    f = open("spellmaper")
    d = map(lambda x: x.strip().split(), f.read().split('\n'))
    f.close()
except:
    print("no spell maper file")

spellmaper = {
    int(x[0]): " ".join(x[1:]) for x in filter(lambda q: len(q) >= 2, d)
}

statmap = {
    0: "wis",
    1: "str",
    2: "agi",
    3: "int"
}


def totallog(x):
    f = open("totallog", "a+")
    f.write(x+"\n")
    f.close()


def main():
    global round_n, total_rounds
    random.seed()
    print("USAGE: optional id and stat of the current master")
    argv = sys.argv[1:]
    best = None
    stat_best = None
    print(argv)
    if len(argv) == 2:
        best = int(argv[0])
        stat_best = int(argv[1])
        print "master's stat is %d = %s" % (best, statmap[stat_best])
    print "id + 4 stats wis, str, agi, int"
    print "input player one's stats  "
    player_one = map(int, raw_input().split())
    assert len(player_one) == 5

    print "input player two's stats"
    player_two = map(int, raw_input().split())

    assert len(player_two) == 5

    players = [
        Hrac(player_one[1:], "Player %d" % player_one[0]),
        Hrac(player_two[1:], "Player %d" % player_two[0])
    ]

    totallog("####")
    totallog(str(argv))
    totallog("$$$$")
    totallog("%f %s %s" % (time.time(), players[0], players[1]))
    if best != best:
        for player in players:
            player.stats[stat_best] *= 2
            if player.name == "Player %d" % best:
                player.stats[stat_best] += 5

    seed = random.randint(0, 1)
    print "seed is %d" % seed
    while round_n < total_rounds:
        print
        print "###############################"
        print "round_n: ", round_n
        for j in xrange(2):
            print
            on_play = (j+seed) % 2
            not_on_play = (j+1+seed) % 2
            print "on_play ", players[on_play].name
            players[on_play].check()
            players[not_on_play].check()

            for b in players[on_play].buffs[:]:
                if b.typ == 19 and round_n == b.start+4:
                    change(
                        players[on_play],
                        players[not_on_play],
                        b.stat, back=True)
                if b.typ == 22 and round_n == b.start+4:
                    purgep(players[not_on_play], "pos")

                if b.typ == 3:
                    hot(
                        players[on_play],
                        players[not_on_play],
                        b.stat, buff=True)

                if b.typ == 11:
                    sot(
                        players[on_play],
                        players[not_on_play],
                        b.stat, buff=True)

                if b.typ == 15:
                    sactick(players[on_play], b.stat)

                if b.typ == 16 and round_n <= b.start+2:
                    if not players[not_on_play].last:
                        purgep(players[not_on_play], "pos")

                if b.typ == 17:
                    stealtick(players[on_play], players[not_on_play], b.stat)

                if b.typ == 25:
                    players[on_play].buffs.append(Buff(25.1, ["pos"]))

            actions = map(int, raw_input().split())
            totallog(str(players[on_play]))
            totallog(str(actions))
            totallog("****")

            if players[on_play].copy:
                players[on_play].copy = False
                for a in players[not_on_play].spells[::-1]:
                    if a/4 not in [13, 10]:
                        actions.append(a)
                        break

            for action in actions:
                multicast_n = 1
                if players[on_play].multicast:
                    players[on_play].multicast = False
                    rnd = random.random()
                    if rnd < 0.75:
                        multicast_n += 1
                    if rnd < 0.25:
                        multicast_n += 1
                    print "multicast %d" % (multicast_n)

                for i in xrange(multicast_n):
                    action_function = codes.get(action/4, nothing)
                    action_function(players[on_play], players[not_on_play], action % 4)
                players[on_play].spells.append(action)

            for b in players[not_on_play].buffs[:]:
                if b.typ == 25.5:
                    players[on_play].buffs.append(Buff(25.6, ["neg"]))

                if b.typ == 5:
                    dot(players[on_play], players[not_on_play], b.stat)
                    dottick(players[on_play], players[not_on_play], b.stat)

            dmgdone = players[not_on_play].dmgdone
            print "actions:"
            for a in actions:
                print a, spellmaper.get(a, "dont know")
                if a/4 == 9:
                    send_heal(players[on_play], players[on_play], dmgdone*0.5)

            players[on_play].last = False
            dif1 = players[on_play].check()
            dif2 = players[not_on_play].check()
            print "HP difference"
            print players[on_play].name, ":", dif1
            print players[not_on_play].name, ":", dif2
            round_n += 1

        if debug:
            print
            print "DEBUG"
            print str(players[0])
            players[0].buffprint()
            print
            print str(players[1])
            players[1].buffprint()
            print

    print
    print "Results:"
    print "Player %s has %d life" % (players[0].name, players[0].hp)
    print "Player %s has %d life" % (players[1].name, players[1].hp)

    f = open("logfile", "a+")
    f.write("%f %s %d %s %d\n" % (time.time(), players[0].name,
            players[0].hp, players[1].name, players[1].hp))
    f.close()

    pass


if __name__ == "__main__":
    main()
