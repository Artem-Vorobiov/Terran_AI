import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import COMMANDCENTER, SCV, SUPPLYDEPOT, REFINERY, VESPENEGEYSER, MINERALFIELD, BARRACKS, FACTORY, \
STARPORT, BARRACKSREACTOR, BARRACKSTECHLAB, STARPORTREACTOR, STARPORTTECHLAB, FACTORYTECHLAB, FACTORYREACTOR, \
MARAUDER, MARINE, HELLION
from sc2.game_data import UpgradeData
from sc2 import position
from sc2.ids.ability_id import AbilityId
from sc2.game_info import Ramp

import math

import random

MAX_WORKERS = 60
adjusted_time_set = set()

#   To Give Command Attack for Group Of Units  - Should be Improved   
#   Too much iterations when I applied HELLIONs to explore 



#   Notes: I got the system overload when I tried to head my HELLION to explore 
#          the map. And cause is - HELLION changing direction every itaration.
#          Every iteration(step) HELLION receive new coordinates it's too mush pressure for system

#   Solution:  Add .idle before begin to loop through HELLION



#   FINDIGN: Found how to reach the game_info.py class Ramp(object)
#            self.main_base_ramp.top_center
#            self.main_base_ramp._nearby
#            self.main_base_ramp._top_edge_12
#            self.main_base_ramp.lower

#           Thats takes from:    
#        def main_base_ramp(self):
        #     return min(
        #     self.game_info.map_ramps,
        #     key=(lambda r: self.start_location.distance_to(r.top_center))
        # )

class NN(sc2.BotAI):

    def __init__(self):
        self.tags = set()
        self.barrack_morph = {}


    async def on_step(self, iteration):
        #   Adjusted TimeChecking Function
        self.time = (self.state.game_loop/22.4) / 60
        adjusted_time = round(self.time, 1)
        if adjusted_time not in adjusted_time_set:
            adjusted_time_set.add(adjusted_time)
            print(adjusted_time)

        # what to do every step
        await self.distribute_workers()  
        await self.build_scv()           
        await self.build_supply_depot()
        await self.build_refinery()
        await self.expand()
        await self.build_barrack()
        await self.build_factory()
        # await self.build_starport()     #   
        await self.improve_barracks()   #   BUILD TECHLAB
        await self.train_soldiers()     #   Train MARAUDER and MARINE
        # await self.train_marauder()
        # await self.train_marine()
        await self.attack_enemy_g()
        # await self.select_target()
        await self.train_hellion()
        await self.exploring()


    def select_target(self):
        # target = self.known_enemy_structures
        # if target.exists:
        #     return target.random.position

        # target = self.known_enemy_units
        # if target.exists:
        #     return target.random.position

        # return self.state.mineral_field.random.position
        # print('\n Inside Function ===>', self.enemy_start_locations[0].position)
        return self.enemy_start_locations[0].position


    async def attack_enemy_g(self):
        target = self.select_target()   #   <coroutine object NN.select_target at 0x105ae4258>
        # print('\n TARGET', target)
        # print('\n TARGET POSITION', target.position)

        if self.units(MARAUDER).amount >= 7 and self.units(MARINE).amount >= 10:
            for m in self.units(MARAUDER).idle:
                await self.do(m.attack(target))
            for mn in self.units(MARINE).idle:
                await self.do(mn.attack(target))
        elif self.known_enemy_units.exists:
            for m in self.units(MARAUDER).idle:
                # print('\n\t Inside known_enemy_units.exists', self.known_enemy_units)         #   True
                await self.do(m.attack(self.known_enemy_units.random.position))
                # print('\n\t RANDOM ENEMY POSITION', self.known_enemy_units.random.position)   #   (150.970458984375, 21.9423828125)
            for mn in self.units(MARINE).idle:
                await self.do(mn.attack(self.known_enemy_units.random.position))


    async def expand(self):
        if self.units(COMMANDCENTER).amount < 2:
            if self.can_afford(COMMANDCENTER) and not self.already_pending(COMMANDCENTER):
                # print('\n EXPANDING FIRST CONDITION ... ')
                await self.expand_now()
        elif self.units(COMMANDCENTER).amount < 3.5 and self.time >= 4:
            if self.can_afford(COMMANDCENTER) and not self.already_pending(COMMANDCENTER):
                # print('\n EXPANDING  second condition... ')
                await self.expand_now()


    # async def build_starport(self):
    #     cc = self.units(COMMANDCENTER).first
    #     if self.units(FACTORY).exists and self.units(STARPORT).amount < 2:
    #         if self.can_afford(STARPORT) and not self.already_pending(STARPORT):
    #             await self.build(STARPORT, near = cc.position.towards(self.game_info.map_center, 11))



    async def build_factory(self):
        cc = self.units(COMMANDCENTER).first
        if self.units(BARRACKS).amount == 2:
            if self.can_afford(FACTORY) and not self.already_pending(FACTORY) \
            and self.units(FACTORY).amount < 1 and self.units(MARINE).amount >= 3:
                await self.build(FACTORY, near = cc.position.towards(self.main_base_ramp.top_center, 7))
        # if self.units(FACTORY).ready:
        #     for f in self.units(FACTORY):
        #         await self.do(f.build(FACTORYREACTOR))
                # print('\n\n\n Bigan FACTORYREACTOR Building ...')

    async def train_hellion(self):
        if self.units(FACTORY).ready and self.units(MARINE).amount >= 5:
            if self.can_afford(HELLION) and not self.already_pending(HELLION):
                for i in self.units(FACTORY).noqueue:
                    await self.do(i.train(HELLION))
                    print('\n Trainin HELLION', i)

############################################################################################
############################################################################################
############################################################################################
#                       Effective solution for exploring the map

#   self.do(h.attack(self.state.mineral_field.random.position))

    async def exploring(self):
        if self.units(HELLION).amount >=5:
            for h in self.units(HELLION).idle:
                await self.do(h.attack(self.state.mineral_field.random.position))
############################################################################################
############################################################################################
############################################################################################




    async def build_barrack(self):
        for cc in self.units(COMMANDCENTER).ready:
            if self.units(BARRACKS).amount < 2 and self.time > 1.6:
                if self.can_afford(BARRACKS) and not self.already_pending(BARRACKS):
                    # print('\n\t\t\t\t We are in BUILD BARRACKS method')
                    await self.build(BARRACKS, near = cc.position.towards(self.game_info.map_center, 10))
    

    async def improve_barracks(self):   
        for BR in self.units(BARRACKS).ready:
            if not self.tags:
                await self.do(BR.build(BARRACKSTECHLAB))
                self.tags.add(BR.tag)


    async def train_soldiers(self):
        if self.units(BARRACKSTECHLAB).ready:
            for brlab in self.units(BARRACKS).noqueue:
                if brlab.tag in self.tags:
                    # print('\n Took one BARRACKS: {}'.format(brlab.tag))
                    if self.can_afford(MARAUDER):
                        if not self.already_pending(MARAUDER):
                            await self.do(brlab.train(MARAUDER))
                            # print('\n Training MARAUDER: {}'.format(brlab.tag))
                else:
                    if self.can_afford(MARINE):
                        if not self.already_pending(MARINE):
                            await self.do(brlab.train(MARINE))
                            # print('\n Training MARINE: {}'.format(brlab.tag))


    # async def train_marauder(self):
    #     if self.units(BARRACKSTECHLAB).ready:
    #         for brlab in self.units(BARRACKS):
    #             if self.can_afford(MARAUDER) and not self.already_pending(MARAUDER):
    #                 await self.do(brlab.train(MARAUDER))

    # async def train_marine(self):
    #     if self.units(BARRACKSREACTOR).ready:
    #         for brlab in self.units(BARRACKS):
    #             if not self.already_pending(MARINE):
    #                 await self.do(brlab.train(MARINE))





    async def build_refinery(self):
        if self.units(SUPPLYDEPOT).exists:
            for cc in self.units(COMMANDCENTER):
                if self.can_afford(REFINERY) and not self.already_pending(REFINERY) and self.units(REFINERY).amount < 1:
                    try:
                        vgs = self.state.vespene_geyser.closer_than(20.0, cc)
                        for vg in vgs:
                            if self.units(REFINERY).closer_than(1.0,vg).exists:
                                break
                            worker = self.select_build_worker(vg.position)
                            await self.do(worker.build(REFINERY, vg))
                    except Exception as e:
                        pass

                elif self.can_afford(REFINERY) and self.time > 1.7 and self.units(REFINERY).amount < 3 and not self.already_pending(REFINERY):
                    try:
                        vgs = self.state.vespene_geyser.closer_than(20.0, cc)
                        for vg in vgs:
                            if self.units(REFINERY).closer_than(1.0,vg).exists:
                                break
                            worker = self.select_build_worker(vg.position)
                            await self.do(worker.build(REFINERY, vg))
                    except Exception as e:
                        pass

                elif self.can_afford(REFINERY) and self.time > 4 and self.units(REFINERY).amount < 4 and not self.already_pending(REFINERY):
                    try:
                        vgs = self.state.vespene_geyser.closer_than(20.0, cc)
                        for vg in vgs:
                            if self.units(REFINERY).closer_than(1.0,vg).exists:
                                break
                            worker = self.select_build_worker(vg.position)
                            await self.do(worker.build(REFINERY, vg))
                    except Exception as e:
                        pass


    async def build_scv(self):
        if self.units(SCV).amount <= MAX_WORKERS:
            for cc in self.units(COMMANDCENTER).ready.noqueue:
                if self.can_afford(SCV) and not self.already_pending(SCV):
                    await self.do(cc.train(SCV))


    async def build_supply_depot(self):
        SD = self.units(COMMANDCENTER)
        if self.supply_used > 0.7*self.supply_cap:
            if self.can_afford(SUPPLYDEPOT) and not self.already_pending(SUPPLYDEPOT):
                await self.build(SUPPLYDEPOT, near = SD.first.position.towards(self.main_base_ramp.top_center, 4))






run_game(maps.get("AbyssalReefLE"), [
    Bot(Race.Terran, NN()),
    Computer(Race.Terran, Difficulty.Medium)
], realtime=False)