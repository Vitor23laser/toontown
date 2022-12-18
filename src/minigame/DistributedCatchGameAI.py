"""DistributedCatchGameAI module: contains the DistributedCatchGameAI class"""

from .DistributedMinigameAI import *
from toontown.ai.ToonBarrier import *
from direct.fsm import ClassicFSM, State
from direct.fsm import State
from . import CatchGameGlobals
from . import MinigameGlobals

class DistributedCatchGameAI(DistributedMinigameAI):

    def __init__(self, air, minigameId):
        try:
            self.DistributedCatchGameAI_initialized
        except:
            self.DistributedCatchGameAI_initialized = 1
            DistributedMinigameAI.__init__(self, air, minigameId)

            self.gameFSM = ClassicFSM.ClassicFSM('DistributedCatchGameAI',
                                   [
                                    State.State('inactive',
                                                self.enterInactive,
                                                self.exitInactive,
                                                ['play']),
                                    State.State('play',
                                                self.enterPlay,
                                                self.exitPlay,
                                                ['cleanup']),
                                    State.State('cleanup',
                                                self.enterCleanup,
                                                self.exitCleanup,
                                                ['inactive']),
                                    ],
                                   # Initial State
                                   'inactive',
                                   # Final State
                                   'inactive',
                                   )

            # Add our game ClassicFSM to the framework ClassicFSM
            self.addChildGameFSM(self.gameFSM)

    def generate(self):
        self.notify.debug("generate")
        DistributedMinigameAI.generate(self)

    # Disable is never called on the AI so we do not define one

    def delete(self):
        self.notify.debug("delete")
        del self.gameFSM
        DistributedMinigameAI.delete(self)

    # override some network message handlers
    def setGameReady(self):
        self.notify.debug("setGameReady")
        DistributedMinigameAI.setGameReady(self)
        # all of the players have checked in
        # they will now be shown the rules

    def setGameStart(self, timestamp):
        self.notify.debug("setGameStart")
        # base class will cause gameFSM to enter initial state
        DistributedMinigameAI.setGameStart(self, timestamp)
        # all of the players are ready to start playing the game
        # transition to the appropriate ClassicFSM state
        self.gameFSM.request('play')

    def setGameAbort(self):
        self.notify.debug("setGameAbort")
        # this is called when the minigame is unexpectedly
        # ended (a player got disconnected, etc.)
        if self.gameFSM.getCurrentState():
            self.gameFSM.request('cleanup')
        DistributedMinigameAI.setGameAbort(self)

    def gameOver(self):
        self.notify.debug("gameOver")
        # call this when the game is done

        # dole out the jellybeans
        self.notify.debug("fruits: %s, fruits caught: %s" %
                          (self.numFruits, self.fruitsCaught))
        perfect = (self.fruitsCaught >= self.numFruits)
        for avId in self.avIdList:
            self.scoreDict[avId] = max(1, int(self.scoreDict[avId]/2))
            if perfect:
                self.notify.debug("PERFECT GAME!")
                self.scoreDict[avId] += round(self.numFruits / 4.)
                self.logAllPerfect()

        # clean things up in this class
        self.gameFSM.request('cleanup')
        # tell the base class to wrap things up
        DistributedMinigameAI.gameOver(self)

    def enterInactive(self):
        self.notify.debug("enterInactive")

    def exitInactive(self):
        pass

    def enterPlay(self):
        self.notify.debug("enterPlay")

        self.caughtList = [0] * 100

        # get the number of fruits that will be dropped
        table = CatchGameGlobals.NumFruits[self.numPlayers-1]
        self.numFruits = table[self.getSafezoneId()]
        self.notify.debug('numFruits: %s' % self.numFruits)
        # and keep track of how many are caught
        self.fruitsCaught = 0

        # set up a barrier to wait for the 'game done' msgs
        def allToonsDone(self=self):
            self.notify.debug('allToonsDone')
            self.sendUpdate('setEveryoneDone')
            if not CatchGameGlobals.EndlessGame:
                self.gameOver()

        def handleTimeout(avIds, self=self):
            self.notify.debug(
                'handleTimeout: avatars %s did not report "done"' %
                avIds)
            self.setGameAbort()

        self.doneBarrier = ToonBarrier(
            'waitClientsDone',
            self.uniqueName('waitClientsDone'),
            self.avIdList,
            CatchGameGlobals.GameDuration + MinigameGlobals.latencyTolerance,
            allToonsDone, handleTimeout)

    def exitPlay(self):
        del self.caughtList

        self.doneBarrier.cleanup()
        del self.doneBarrier

    def claimCatch(self, objNum, DropObjTypeId):
        if self.gameFSM.getCurrentState().getName() != 'play':
            return

        # range check DropObjTypeId
        if DropObjTypeId < 0 or DropObjTypeId >= len(CatchGameGlobals.DOTypeId2Name):
            self.air.writeServerEvent('warning', DropObjTypeId, 'CatchGameAI.claimCatch DropObjTypeId out of range')
            return

        # sanity check; don't allow hackers to allocate unlimited memory
        if objNum < 0 or objNum > 5000 or objNum >= 2*len(self.caughtList):
            # self.notify.debug('object num %s is too high. ignoring' % objNum)
            self.air.writeServerEvent('warning', objNum, 'CatchGameAI.claimCatch objNum is too high or negative')
            return

        # double the size of the caught table as needed
        if objNum >= len(self.caughtList):
            self.caughtList += [0] * len(self.caughtList)

        # if nobody's caught this object yet, announce that it's been caught
        if not self.caughtList[objNum]:
            self.caughtList[objNum] = 1
            avId = self.air.getAvatarIdFromSender()
            self.sendUpdate('setObjectCaught', [avId, objNum])
            # if it's a good obj, update the score
            objName = CatchGameGlobals.DOTypeId2Name[DropObjTypeId]
            self.notify.debug('avatar %s caught object %s: %s' %
                              (avId, objNum, objName))
            if CatchGameGlobals.Name2DropObjectType[objName].good:
                self.scoreDict[avId] += 1
                self.fruitsCaught += 1

    def reportDone(self):
        if not self.gameFSM or not self.gameFSM.getCurrentState() or \
               self.gameFSM.getCurrentState().getName() != 'play':
            return

        avId = self.air.getAvatarIdFromSender()
        # all of the objects on this avatar's client have landed
        # or been caught
        self.notify.debug('reportDone: avatar %s is done' % avId)
        self.doneBarrier.clear(avId)

    def enterCleanup(self):
        self.notify.debug("enterCleanup")
        self.gameFSM.request('inactive')

    def exitCleanup(self):
        pass
