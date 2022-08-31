from direct.interval.IntervalGlobal import *
from .BattleBase import *
from .BattleProps import *

from direct.directnotify import DirectNotifyGlobal
import random
from direct.particles import ParticleEffect
from . import BattleParticles
from . import BattleProps
from toontown.toonbase import TTLocalizer
from toontown.toonbase.ToontownModules import *

notify = DirectNotifyGlobal.directNotify.newCategory('MovieUtil')

SUIT_LOSE_DURATION = 6.0
SUIT_LURE_DISTANCE = 2.6
SUIT_LURE_DOLLAR_DISTANCE = 5.1
SUIT_EXTRA_REACH_DISTANCE = 0.9
SUIT_EXTRA_RAKE_DISTANCE = 1.1
SUIT_TRAP_DISTANCE = 2.6
SUIT_TRAP_RAKE_DISTANCE = 4.5 # Rake is farther from suit for it to walk into the rake
SUIT_TRAP_MARBLES_DISTANCE = 3.7 # Marbles are out farther
SUIT_TRAP_TNT_DISTANCE = 5.1

PNT3_NEARZERO = Point3(0.01, 0.01, 0.01)
PNT3_ZERO = Point3(0.0, 0.0, 0.0)
PNT3_ONE = Point3(1.0, 1.0, 1.0)

# Certain suits are so large that their movement needs curtail on the reach animation
largeSuits = ['f', 'cc', 'gh', 'tw', 'bf', 'sc', \
               'ds', 'hh', 'cr', 'tbc', 'bs', 'sd', 'le', 'bw', \
               'nc', 'mb', 'ls', 'rb', 'ms', 'tf', 'm', 'mh']

# The shot direction refers to which side of the battle the movie camera will
# remain within during one series of toon and suit attacks.  This value is randomly set
# to left or right (50% chance) in Movie.play right before the action is played.
shotDirection = 'left'

def avatarDodge(leftAvatars, rightAvatars, leftData, rightData):
    # when an avatar dodges, other avatars may need to dodge as well
    if len(leftAvatars) > len(rightAvatars):
        # Path of Least/Most Resistance
        PoLR = rightAvatars
        PoMR = leftAvatars
    else:
        PoLR = leftAvatars
        PoMR = rightAvatars
    # most of the time, choose the side with the least avatars
    # base the random choice on the difference between the
    # number of avatars on the left versus the right
    upper = 1 + (4 * abs(len(leftAvatars) - len(rightAvatars)))
    if (random.randint(0, upper) > 0):
        avDodgeList = PoLR
    else:
        avDodgeList = PoMR
    # select the correct data
    if avDodgeList is leftAvatars:
        data = leftData
    else:
        data = rightData

    return avDodgeList, data

def avatarHide(avatar):
    notify.debug('avatarHide(%d)' % avatar.doId)
    #import pdb; pdb.set_trace()
    if hasattr(avatar,'battleTrapProp'):
        notify.debug('avatar.battleTrapProp = %s' % avatar.battleTrapProp)
    avatar.detachNode()

def copyProp(prop):
    from direct.actor import Actor
    if (isinstance(prop, Actor.Actor)):
        return Actor.Actor(other=prop)
    else:
        return prop.copyTo(hidden)

def showProp(prop, hand, pos=None, hpr=None, scale=None):
    prop.reparentTo(hand)
    if pos:
        if callable(pos):
            pos = pos()
        prop.setPos(pos)
    if hpr:
        if callable(hpr):
            hpr = hpr()
        prop.setHpr(hpr)
    if scale:
        if callable(scale):
            scale = scale()
        prop.setScale(scale)

def showProps(props, hands, pos=None, hpr=None, scale=None):
    assert(len(props) <= len(hands))
    index = 0
    for prop in props:
        prop.reparentTo(hands[index])
        if pos:
            prop.setPos(pos)
        if hpr:
            prop.setHpr(hpr)
        if scale:
            prop.setScale(scale)
        index += 1

def hideProps(props):
    for prop in props:
        prop.detachNode()

def removeProp(prop):
    from direct.actor import Actor
    if ((prop.isEmpty() == 1) or (prop == None)):
        return
    prop.detachNode()
    if (isinstance(prop, Actor.Actor)):
        prop.cleanup()
    else:
        prop.removeNode()

def removeProps(props):
    for prop in props:
        removeProp(prop)

def getActorIntervals(props, anim):
    tracks = Parallel()
    for prop in props:
        tracks.append(ActorInterval(prop, anim))
    return tracks

def getScaleIntervals(props, duration, startScale, endScale):
    tracks = Parallel()
    for prop in props:
        tracks.append(LerpScaleInterval(prop, duration, endScale,
                                        startScale=startScale))
    return tracks

def avatarFacePoint(av, other=render):
    pnt = av.getPos(other)
    pnt.setZ(pnt[2] + av.getHeight())
    return pnt

def insertDeathSuit(suit, deathSuit, battle=None, pos=None, hpr=None):
    holdParent = suit.getParent()
    if suit.getVirtual():
        virtualize(deathSuit)
    avatarHide(suit)
    if (deathSuit != None and not deathSuit.isEmpty()):
        if holdParent and 0:# seems like a good idea if everything wasn't hosed JML
            #import pdb; pdb.set_trace()
            deathSuit.reparentTo(holdParent)
        else:
            deathSuit.reparentTo(render)
        if (battle != None and pos != None):
            deathSuit.setPos(battle, pos)
        if (battle != None and hpr != None):
            deathSuit.setHpr(battle, hpr)

def removeDeathSuit(suit, deathSuit):
    notify.debug('removeDeathSuit()')
    if (not deathSuit.isEmpty()):
        deathSuit.detachNode()
        suit.cleanupLoseActor()


def insertReviveSuit(suit, deathSuit, battle=None, pos=None, hpr=None):
    holdParent = suit.getParent()
    if suit.getVirtual():
        virtualize(deathSuit)
    #avatarHide(suit)
    suit.hide()
    if (deathSuit != None and not deathSuit.isEmpty()):
        if holdParent and 0:# seems like a good idea if everything wasn't hosed JML
            #import pdb; pdb.set_trace()
            deathSuit.reparentTo(holdParent)
        else:
            deathSuit.reparentTo(render)
        if (battle != None and pos != None):
            deathSuit.setPos(battle, pos)
        if (battle != None and hpr != None):
            deathSuit.setHpr(battle, hpr)

def removeReviveSuit(suit, deathSuit):
    notify.debug('removeDeathSuit()')
    suit.setSkelecog(1)
    #suit.makeSkeleton()
    suit.show()
    if (not deathSuit.isEmpty()):
        deathSuit.detachNode()
        suit.cleanupLoseActor()
    #suit.removeHealthBar()
    suit.healthBar.show()
    suit.reseatHealthBarForSkele()

def virtualize(deathsuit):
        actorNode = deathsuit.find("**/__Actor_modelRoot")
        actorCollection = actorNode.findAllMatches("*")
        parts = ()
        for thingIndex in range(0,actorCollection.getNumPaths()):
            thing = actorCollection[thingIndex]
            if thing.getName() not in ('joint*attachMeter', 'joint*nameTag', 'def_nameTag'):
                thing.setColorScale(1.0,0.0,0.0,1.0)
                thing.setAttrib(ColorBlendAttrib.make(ColorBlendAttrib.MAdd))
                thing.setDepthWrite(False)
                thing.setBin('fixed', 1)




def createTrainTrackAppearTrack( dyingSuit, toon, battle, npcs):
    """
    so if the suit which has the visible train track dies
    we need to make it visible for the other suits which have survived, if any
    """

    retval = Sequence()
    return retval
    possibleSuits = []
    #we assume that if a suit attacked, it's still alive
    #darn we need to consider lured suits... well maybe not,
    #can it have a train trap and be lured at the same time?
    for suitAttack in battle.movie.suitAttackDicts:
        suit = suitAttack['suit']
        if not suit == dyingSuit:
            if hasattr(suit,'battleTrapProp') and suit.battleTrapProp and \
               suit.battleTrapProp.getName() == 'traintrack':
                possibleSuits.append(suitAttack['suit'])

    #so we have the possible suits, see which one is closest to the center
    closestXDistance = 10000
    closestSuit = None
    for suit in possibleSuits:
        suitPoint, suitHpr = battle.getActorPosHpr(suit)
        xDistance = abs(suitPoint.getX())
        if xDistance < closestXDistance:
            closestSuit = suit
            closestXDistance = xDistance

    if closestSuit and closestSuit.battleTrapProp.isHidden():
        #immediately set the alpha to zero, and show the the train track
        #this will prevent this sequence happening twice when 2 cogs die
        #import pdb; pdb.set_trace()

        closestSuit.battleTrapProp.setColorScale(1,1,1,0)
        closestSuit.battleTrapProp.show()
        newRelativePos = dyingSuit.battleTrapProp.getPos(closestSuit)
        newHpr = dyingSuit.battleTrapProp.getHpr(closestSuit)
        closestSuit.battleTrapProp.setPos(newRelativePos)
        closestSuit.battleTrapProp.setHpr(newHpr)


        retval.append(LerpColorScaleInterval(closestSuit.battleTrapProp, 3.0, Vec4(1,1,1,1)))
    else:
        notify.debug('could not find closest suit, returning empty sequence')

    return retval


def createSuitReviveTrack(suit, toon, battle, npcs = []):
    suitTrack = Sequence()

    suitPos, suitHpr = battle.getActorPosHpr(suit)

    #import pdb; pdb.set_trace()

    if hasattr(suit,'battleTrapProp') and suit.battleTrapProp and \
       suit.battleTrapProp.getName() == 'traintrack' and \
       not suit.battleTrapProp.isHidden():
        suitTrack.append( createTrainTrackAppearTrack( suit, toon, battle, npcs))

    deathSuit = suit.getLoseActor()
    assert(deathSuit != None)
    #suitTrack.append(Wait(10))
    suitTrack.append(Func(notify.debug, 'before insertDeathSuit'))
    suitTrack.append(Func(insertReviveSuit, suit, deathSuit, battle, suitPos, suitHpr))
    #suitTrack.append(Wait(10))
    suitTrack.append(Func(notify.debug, 'before actorInterval lose'))
    suitTrack.append(ActorInterval(deathSuit, 'lose', duration=SUIT_LOSE_DURATION))
    #suitTrack.append(Wait(10))
    suitTrack.append(Func(notify.debug, 'before removeDeathSuit'))
    suitTrack.append(Func(removeReviveSuit, suit, deathSuit, name='remove-death-suit'))
    #suitTrack.append(Wait(10))
    suitTrack.append(Func(notify.debug, 'after removeDeathSuit'))
    suitTrack.append(Func(suit.loop, 'neutral'))




    spinningSound = base.loader.loadSfx("phase_3.5/audio/sfx/Cog_Death.mp3")
    deathSound = base.loader.loadSfx("phase_3.5/audio/sfx/ENC_cogfall_apart.mp3")
    deathSoundTrack = Sequence(
        Wait(0.8),
        SoundInterval(spinningSound, duration=1.2, startTime = 1.5, volume=0.2, node=suit),
        SoundInterval(spinningSound, duration=3.0, startTime = 0.6, volume=0.8, node=suit),
        SoundInterval(deathSound, volume = 0.32, node=suit),
        )

    BattleParticles.loadParticles()
    smallGears = BattleParticles.createParticleEffect(file='gearExplosionSmall')
    singleGear = BattleParticles.createParticleEffect('GearExplosion',
                                                                numParticles=1)
    smallGearExplosion = BattleParticles.createParticleEffect('GearExplosion',
                                                              numParticles=10)
    bigGearExplosion = BattleParticles.createParticleEffect('BigGearExplosion',
                                                              numParticles=30)

    gearPoint = Point3(suitPos.getX(), suitPos.getY(), suitPos.getZ()+suit.height-0.2)
    smallGears.setPos(gearPoint)
    singleGear.setPos(gearPoint)
    smallGears.setDepthWrite(False)
    singleGear.setDepthWrite(False)
    smallGearExplosion.setPos(gearPoint)
    bigGearExplosion.setPos(gearPoint)
    smallGearExplosion.setDepthWrite(False)
    bigGearExplosion.setDepthWrite(False)

    explosionTrack = Sequence()
    explosionTrack.append(Wait(5.4))
    explosionTrack.append(createKapowExplosionTrack(battle, explosionPoint=gearPoint))

    gears1Track = Sequence(
        Wait(2.1),
        ParticleInterval(smallGears, battle, worldRelative=0, duration=4.3, cleanup = True),
        name='gears1Track')
    gears2MTrack = Track(
        (0.0, explosionTrack),
        (0.7, ParticleInterval(singleGear, battle, worldRelative=0,
                               duration=5.7, cleanup = True)),
        (5.2, ParticleInterval(smallGearExplosion, battle,
                               worldRelative=0, duration=1.2, cleanup = True)),
        (5.4, ParticleInterval(bigGearExplosion, battle,
                               worldRelative=0, duration=1.0, cleanup = True)),
        name='gears2MTrack')
    toonMTrack = Parallel(name='toonMTrack')
    for mtoon in battle.toons:
        toonMTrack.append(Sequence(
            Wait(1.0),
            ActorInterval(mtoon, 'duck'),
            ActorInterval(mtoon, 'duck', startTime=1.8),
            Func(mtoon.loop, 'neutral'),
        ))
    for mtoon in npcs:
        toonMTrack.append(Sequence(
            Wait(1.0),
            ActorInterval(mtoon, 'duck'),
            ActorInterval(mtoon, 'duck', startTime=1.8),
            Func(mtoon.loop, 'neutral'),
        ))

    return Parallel(suitTrack, deathSoundTrack, gears1Track, gears2MTrack,
                    toonMTrack)

def createSuitDeathTrack(suit, toon, battle, npcs = []):
    suitTrack = Sequence()

    suitPos, suitHpr = battle.getActorPosHpr(suit)

    #import pdb; pdb.set_trace()

    if hasattr(suit,'battleTrapProp') and suit.battleTrapProp and \
       suit.battleTrapProp.getName() == 'traintrack' and \
       not suit.battleTrapProp.isHidden():
        suitTrack.append( createTrainTrackAppearTrack( suit, toon, battle, npcs))

    deathSuit = suit.getLoseActor()
    assert(deathSuit != None)
    #suitTrack.append(Wait(10))
    suitTrack.append(Func(notify.debug, 'before insertDeathSuit'))
    suitTrack.append(Func(insertDeathSuit, suit, deathSuit, battle, suitPos, suitHpr))
    #suitTrack.append(Wait(10))
    suitTrack.append(Func(notify.debug, 'before actorInterval lose'))
    suitTrack.append(ActorInterval(deathSuit, 'lose', duration=SUIT_LOSE_DURATION))
    #suitTrack.append(Wait(10))
    suitTrack.append(Func(notify.debug, 'before removeDeathSuit'))
    suitTrack.append(Func(removeDeathSuit, suit, deathSuit, name='remove-death-suit'))
    #suitTrack.append(Wait(10))
    suitTrack.append(Func(notify.debug, 'after removeDeathSuit'))




    spinningSound = base.loader.loadSfx("phase_3.5/audio/sfx/Cog_Death.mp3")
    deathSound = base.loader.loadSfx("phase_3.5/audio/sfx/ENC_cogfall_apart.mp3")
    deathSoundTrack = Sequence(
        Wait(0.8),
        SoundInterval(spinningSound, duration=1.2, startTime = 1.5, volume=0.2, node=deathSuit),
        SoundInterval(spinningSound, duration=3.0, startTime = 0.6, volume=0.8, node=deathSuit),
        SoundInterval(deathSound, volume = 0.32, node=deathSuit),
        )

    BattleParticles.loadParticles()
    smallGears = BattleParticles.createParticleEffect(file='gearExplosionSmall')
    singleGear = BattleParticles.createParticleEffect('GearExplosion',
                                                                numParticles=1)
    smallGearExplosion = BattleParticles.createParticleEffect('GearExplosion',
                                                              numParticles=10)
    bigGearExplosion = BattleParticles.createParticleEffect('BigGearExplosion',
                                                              numParticles=30)

    gearPoint = Point3(suitPos.getX(), suitPos.getY(), suitPos.getZ()+suit.height-0.2)
    smallGears.setPos(gearPoint)
    singleGear.setPos(gearPoint)
    smallGears.setDepthWrite(False)
    singleGear.setDepthWrite(False)
    smallGearExplosion.setPos(gearPoint)
    bigGearExplosion.setPos(gearPoint)
    smallGearExplosion.setDepthWrite(False)
    bigGearExplosion.setDepthWrite(False)

    explosionTrack = Sequence()
    explosionTrack.append(Wait(5.4))
    explosionTrack.append(createKapowExplosionTrack(battle, explosionPoint=gearPoint))

    gears1Track = Sequence(
        Wait(2.1),
        ParticleInterval(smallGears, battle, worldRelative=0, duration=4.3, cleanup = True),
        name='gears1Track')
    gears2MTrack = Track(
        (0.0, explosionTrack),
        (0.7, ParticleInterval(singleGear, battle, worldRelative=0,
                               duration=5.7, cleanup = True)),
        (5.2, ParticleInterval(smallGearExplosion, battle,
                               worldRelative=0, duration=1.2, cleanup = True)),
        (5.4, ParticleInterval(bigGearExplosion, battle,
                               worldRelative=0, duration=1.0, cleanup = True)),
        name='gears2MTrack')
    toonMTrack = Parallel(name='toonMTrack')
    for mtoon in battle.toons:
        toonMTrack.append(Sequence(
            Wait(1.0),
            ActorInterval(mtoon, 'duck'),
            ActorInterval(mtoon, 'duck', startTime=1.8),
            Func(mtoon.loop, 'neutral'),
        ))
    for mtoon in npcs:
        toonMTrack.append(Sequence(
            Wait(1.0),
            ActorInterval(mtoon, 'duck'),
            ActorInterval(mtoon, 'duck', startTime=1.8),
            Func(mtoon.loop, 'neutral'),
        ))

    return Parallel(suitTrack, deathSoundTrack, gears1Track, gears2MTrack,
                    toonMTrack)

def createSuitDodgeMultitrack(tDodge, suit, leftSuits, rightSuits):
    suitTracks = Parallel()
    suitDodgeList, sidestepAnim = avatarDodge(leftSuits, rightSuits,
                                              'sidestep-left', 'sidestep-right')
    # make the other suits dodge
    for s in suitDodgeList:
        suitTracks.append(Sequence(ActorInterval(s, sidestepAnim),
                                   Func(s.loop, 'neutral')))
    # finally, make the target suit dodge
    suitTracks.append(Sequence(ActorInterval(suit, sidestepAnim),
                               Func(suit.loop, 'neutral')))
    # indicate that the suit was missed
    suitTracks.append(Func(indicateMissed, suit))

    ## play the dodge sounds
    #jumpSound = base.loader.loadSfx("phase_5/audio/sfx/ENC_cogjump_to_side.mp3")
    #stepSound = base.loader.loadSfx("phase_5/audio/sfx/ENC_cogside_step.mp3")
    #if jumpSound:
    #    suitTracks.append(SoundInterval(jumpSound))
    #if stepSound:
    #    suitTracks.append(Sequence(Wait(1.5), SoundInterval(stepSound)))

    return Sequence(Wait(tDodge), suitTracks)

def createToonDodgeMultitrack(tDodge, toon, leftToons, rightToons):
    # Unlike suits, the toon side step right animation occurs behind
    # the adjacent toon thus we only need to move other toons with the
    # sidestep left dodge.  But even with this difference, we still
    # use the same probability for which direction to dodge.
    toonTracks = Parallel()

    # when an avatar dodges, other avatars may need to dodge as well
    if len(leftToons) > len(rightToons):
        # Path of Least/Most Resistance
        PoLR = rightToons
        PoMR = leftToons
    else:
        PoLR = leftToons
        PoMR = rightToons
    # most of the time, choose the side with the least avatars
    # base the random choice on the difference between the
    # number of avatars on the left versus the right
    upper = 1 + (4 * abs(len(leftToons) - len(rightToons)))
    if (random.randint(0, upper) > 0):
        toonDodgeList = PoLR
    else:
        toonDodgeList = PoMR

    # select the correct data
    if toonDodgeList is leftToons:
        sidestepAnim = 'sidestep-left'
        # Make the other toons dodge
        for t in toonDodgeList:
            toonTracks.append(Sequence(ActorInterval(t, sidestepAnim),
                                       Func(t.loop, 'neutral')))
    else:
        sidestepAnim = 'sidestep-right'

    # finally, make the target toon dodge
    toonTracks.append(Sequence(ActorInterval(toon, sidestepAnim),
                               Func(toon.loop, 'neutral')))
    # indicate that the toon was missed
    toonTracks.append(Func(indicateMissed, toon))

    return Sequence(Wait(tDodge), toonTracks)

def createSuitTeaseMultiTrack(suit, delay=0.01):
    # Used if the suit teases a toon for missing an attack, (large drops)
    suitTrack = Sequence(
        Wait(delay),
        ActorInterval(suit, 'victory', startTime=0.5, endTime=1.9),
        Func(suit.loop, 'neutral'),
        )
    missedTrack = Sequence(Wait(delay+0.2),
                           Func(indicateMissed, suit, 0.9))
    return Parallel(suitTrack, missedTrack)


# spray intervals

SPRAY_LEN = 1.5

# spray head extends from origin to target, holds,
# then spray tail extends from origin to target
def getSprayTrack(battle, color, origin, target, dScaleUp, dHold,
                  dScaleDown, horizScale = 1.0, vertScale = 1.0, parent = render):
    track = Sequence()

    # sprayRot
    #  |__ sprayScale
    #       |__ sprayProp

    sprayProp = globalPropPool.getProp('spray')
    # make a parent node for the spray that will hold the scale
    sprayScale = hidden.attachNewNode('spray-parent')
    # the rotation must be on a separate node so that the
    # lerpScale doesn't muck with the rotation
    sprayRot = hidden.attachNewNode('spray-rotate')

    spray = sprayRot
    spray.setColor(color)
    if (color[3] < 1.0):
        spray.setTransparency(1)

    # show the spray
    def showSpray(sprayScale, sprayRot, sprayProp, origin, target, parent):
        if callable(origin):
            origin = origin()
        if callable(target):
            target = target()
        sprayRot.reparentTo(parent)
        sprayRot.clearMat()
        sprayScale.reparentTo(sprayRot)
        sprayScale.clearMat()
        sprayProp.reparentTo(sprayScale)
        sprayProp.clearMat()
        sprayRot.setPos(origin)
        sprayRot.lookAt(Point3(target))
    track.append(Func(battle.movie.needRestoreRenderProp, sprayProp))
    track.append(Func(showSpray, sprayScale, sprayRot, sprayProp,
                      origin, target, parent))

    # scale the spray up
    def calcTargetScale(target = target, origin = origin, horizScale = horizScale, vertScale = vertScale):
        if callable(target):
            target = target()
        if callable(origin):
            origin = origin()
        distance = Vec3(target - origin).length()
        yScale = distance / SPRAY_LEN
        #targetScale = Point3(yScale, yScale*horizScale, yScale*vertScale)
        targetScale = Point3(yScale*horizScale, yScale, yScale*vertScale)
        return targetScale
    track.append(LerpScaleInterval(sprayScale, dScaleUp, calcTargetScale, startScale=PNT3_NEARZERO))

    # hold the spray
    track.append(Wait(dHold))

    # bring the back of the spray up to the front, using a scale

    # first we need to adjust the spray's parent node so that it
    # is positioned at the end of the spray
    def prepareToShrinkSpray(spray, sprayProp, origin, target):
        if callable(target):
            target = target()
        if callable(origin):
            origin = origin()
        #localSprayHeadPos = target - origin
        sprayProp.setPos(Point3(0., -SPRAY_LEN, 0.))
        spray.setPos(target)
    track.append(Func(prepareToShrinkSpray, spray, sprayProp,
                      origin, target))

    # shrink the spray down
    track.append(LerpScaleInterval(sprayScale, dScaleDown, PNT3_NEARZERO))

    # hide the spray
    def hideSpray(spray, sprayScale, sprayRot, sprayProp, propPool):
        sprayProp.detachNode()
        removeProp(sprayProp)
        sprayRot.removeNode()
        sprayScale.removeNode()

    track.append(Func(hideSpray, spray, sprayScale, sprayRot,
                      sprayProp, globalPropPool))
    track.append(Func(battle.movie.clearRenderProp, sprayProp))

    return track

T_HOLE_LEAVES_HAND = 1.708
T_TELEPORT_ANIM = 3.3
T_HOLE_CLOSES = 0.3

def getToonTeleportOutInterval(toon):
    """ getToonTeleportOutInterval(toon)
    """
    holeActors = toon.getHoleActors()
    holes = [holeActors[0], holeActors[1]]
    hole = holes[0]
    hole2 = holes[1]
    hands = toon.getRightHands()
    delay = T_HOLE_LEAVES_HAND
    dur = T_TELEPORT_ANIM
    holeTrack = Sequence()
    holeTrack.append(Func(showProps, holes, hands))
    holeTrack.append(Wait(0.5)),
    holeTrack.append(Func(base.playSfx, toon.getSoundTeleport()))
    holeTrack.append(Wait(delay - 0.5))
    holeTrack.append(Func(hole.reparentTo, toon))
    holeTrack.append(Func(hole2.reparentTo, hidden))
    holeAnimTrack = Sequence()
    holeAnimTrack.append(ActorInterval(hole, 'hole', duration=dur))
    holeAnimTrack.append(Func(hideProps, holes))

    runTrack = Sequence(ActorInterval(toon, 'teleport', duration=dur),
                        Wait(T_HOLE_CLOSES),
                        Func(toon.detachNode))
    return Parallel(runTrack, holeAnimTrack, holeTrack)

def getToonTeleportInInterval(toon):
    """ getToonTeleportInInterval(toon)
    """
    hole = toon.getHoleActors()[0]
    holeAnimTrack = Sequence()
    holeAnimTrack.append(Func(toon.detachNode))
    holeAnimTrack.append(Func(hole.reparentTo, toon))
    pos = Point3(0, -2.4, 0)
    holeAnimTrack.append(Func(hole.setPos, toon, pos))
    holeAnimTrack.append(ActorInterval(hole, 'hole', startTime=T_TELEPORT_ANIM,
                                endTime=T_HOLE_LEAVES_HAND))
    holeAnimTrack.append(ActorInterval(hole, 'hole',
                                startTime=T_HOLE_LEAVES_HAND,
                                endTime=T_TELEPORT_ANIM))
    holeAnimTrack.append(Func(hole.reparentTo, hidden))

    delay = T_TELEPORT_ANIM - T_HOLE_LEAVES_HAND
    jumpTrack = Sequence(Wait(delay),
                         Func(toon.reparentTo, render),
                         ActorInterval(toon, 'jump'))
    return Parallel(holeAnimTrack, jumpTrack)

def getSuitRakeOffset(suit):
    """ getSuitRakeOffset(suit)
    """
    suitName = suit.getStyleName()
    if (suitName == 'gh'):
        return 1.4
    elif (suitName == 'f'):
        return 1.0
    elif (suitName == 'cc'):
        return 0.7
    elif (suitName == 'tw'):
        return 1.3
    elif (suitName == 'bf'):
        return 1.0
    elif (suitName == 'sc'):
        return 0.8
    elif (suitName == 'ym'):
        return 0.1
    elif (suitName == 'mm'):
        return 0.05
    elif (suitName == 'tm'):
        return 0.07
    elif (suitName == 'nd'):
        return 0.07
    elif (suitName == 'pp'):
        return 0.04
    elif (suitName == 'bc'):
        return 0.36
    elif (suitName == 'b'):
        return 0.41
    elif (suitName == 'dt'):
        return 0.31
    elif (suitName == 'ac'):
        return 0.39
    elif (suitName == 'ds'):
        return 0.41
    elif (suitName == 'hh'):
        return 0.8
    elif (suitName == 'cr'):
        return 2.1
    elif (suitName == 'tbc'):
        return 1.4
    elif (suitName == 'bs'):
        return 0.4
    elif (suitName == 'sd'):
        return 1.02
    elif (suitName == 'le'):
        return 1.3
    elif (suitName == 'bw'):
        return 1.4
    elif (suitName == 'nc'):
        return 0.6
    elif (suitName == 'mb'):
        return 1.85
    elif (suitName == 'ls'):
        return 1.4
    elif (suitName == 'rb'):
        return 1.6
    elif (suitName == 'ms'):
        return 0.7
    elif (suitName == 'tf'):
        return 0.75
    elif (suitName == 'm'):
        return 0.9
    elif (suitName == 'mh'):
        return 1.3
    else:
        notify.warning('getSuitRakeOffset(suit) - Unknown suit name: %s' % suitName)
        return 0

def startSparksIval(tntProp):
    tip = tntProp.find("**/joint*attachEmitter")
    sparks = BattleParticles.createParticleEffect(file='tnt')
    return Func(sparks.start, tip)

def indicateMissed(actor, duration=1.1, scale=0.7):
    """ indicateMissed() shows the text missed above an actor """
    actor.showHpString(TTLocalizer.AttackMissed, duration=duration, scale=scale)

def createKapowExplosionTrack(parent, explosionPoint=None, scale = 1.0):
    explosionTrack = Sequence()
    explosion = loader.loadModel("phase_3.5/models/props/explosion.bam")
    explosion.setBillboardPointEye()
    #explosion.setDepthWrite(False)
    if not explosionPoint:
        explosionPoint = Point3(0, 3.6, 2.1)
    explosionTrack.append(Func(explosion.reparentTo, parent))
    explosionTrack.append(Func(explosion.setPos, explosionPoint))
    explosionTrack.append(Func(explosion.setScale, 0.4 * scale))
    explosionTrack.append(Wait(0.6))
    explosionTrack.append(Func(removeProp, explosion))
    return explosionTrack

def createSuitStunInterval(suit, before, after):
    # Some temp point vectors
    p1 = Point3(0)
    p2 = Point3(0)
    # Show reaction and stun prop
    stars = globalPropPool.getProp('stun')
    # Give it a color so we can override any head colors
    stars.setColor(1, 1, 1, 1)
    # Override head colors and textures
    stars.adjustAllPriorities(100)
    # How high is head?  Assume head is part 0 (this is good for suits)
    head = suit.getHeadParts()[0]
    head.calcTightBounds(p1, p2)
    # Show stun prop at proper height with specified delay before and after
    return Sequence(Wait(before),
                    Func(stars.reparentTo, head),
                    Func(stars.setZ, max(0.0, p2[2] - 1.0)),
                    Func(stars.loop, 'stun'),
                    Wait(after),
                    Func(stars.removeNode))



def calcAvgSuitPos(throw):
    """
    Calculate the average suit positions for the all the targets in this throw
    """
    battle = throw['battle']
    avgSuitPos = Point3(0,0,0)
    numTargets = len(throw['target'])
    for i in range(numTargets):
        suit = throw['target'][i]['suit']
        avgSuitPos += suit.getPos(battle)
    avgSuitPos /= numTargets
    return avgSuitPos
