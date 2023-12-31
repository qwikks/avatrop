import asyncio, random
from modules.base_module import Module
import time

class_name = "Pet"


class Pet(Module):
    prefix = "pet"
    
    def __init__(self, server):
        self.server = server
        self.commands = {"b": self.buy, "gtpt": self._getPetModel, "e": self.editName, "uc": self._updateCharacterPet}
    
    async def _addPet(self, client, houseId, namePet, colorIndexPet, petTypeId):
        r = self.server.redis
        uid = client.uid
        petsModel = f"uid:{uid}:pets"
        petId = await self.server.getFreeIdPlace(client)
        await r.rpush(petsModel, petId)
        petModel = f"uid:{uid}:pet:{petId}:"
        await r.set(petModel + "nm", namePet)
        await r.set(petModel + "tid", petTypeId)
        await r.set(petModel + "rtg", 0)
        await r.set(petModel + "cix", colorIndexPet)
        await r.set(petModel + "sltm", 0)
        await r.set(petModel + "sltp", "nap")
        await self._createCharacterPet(client, petId)
        # await r.set(petModel + "sltp", "advid")
        # await r.set(petModel + "sltp", "advsttm")
        await r.set(petModel + "wx", client.position[0])
        await r.set(petModel + "wy", client.position[1])
        await r.set(petModel + "hid", houseId)
        await r.set(petModel + "oid", client.uid)
        pet = await self._getPetModel(client, str(petId))
        msg = ['pet.b', {"pet": pet, "phid": int(houseId)}]
        await client.send(msg)
        await self._petJoin(client, petId)
    
    async def _getPetModel(self, client, pid):
        r = self.server.redis
        uid = client.uid
        petsModel = f"uid:{uid}:pets"
        pet = {}
        if pid not in await r.lrange(petsModel, 0, -1):
            return {}
        petModel = f"uid:{uid}:pet:{pid}:"
        pet["id"] = int(pid)
        pet["n"] = await r.get(petModel + "nm")
        pet["oid"] = await r.get(petModel + "oid")
        pet["sut"] = int(float(await r.get(petModel + "sltm")))
        if 0 < pet["sut"] <= int(time.time()):
            lineModel = petModel + "chrctr:line:"
            await r.set(lineModel + "cf", 100 * 100)
            await r.set(petModel + "sltm", 0)
            pet["sut"] = 0
        pet["c"] = await self._updateCharacterPet(client, pid)
        pet["tid"] = await r.get(petModel + "tid")
        pet["rt"] = await r.get(petModel + "rtg")
        pet["ci"] = int(await r.get(petModel + "cix"))
        pet["stp"] = await r.get(petModel + "sltp")
        pet["psx"] = int(float(await r.get(petModel + "wx")))
        pet["psy"] = int(float(await r.get(petModel + "wy")))
        return pet
    
    async def _sleepPet(self, client):
        ...
    
    async def _updateCharacterPet(self, client, pid, uptm=True) -> dict:
        r = self.server.redis
        try:
            uid = client.uid
        except:
            uid = client
        characterLineTypes = ["st", "hp", "hl", "hg", "cf"]
        petsModel = f"uid:{uid}:pets"
        character = {}
        if pid not in await r.lrange(petsModel, 0, -1):
            return {}
        petModel = f"uid:{uid}:pet:{pid}:"
        characterModel = petModel + "chrctr:"
        character["l"] = []
        for line in characterLineTypes:
            ln = await r.get(characterModel + f"line:{line}")
            if not ln:
                await self._createCharacterPet(client, pid)
                ln = await r.get(characterModel + f"line:{line}")
            character["l"] += [{"v": int(ln) / 100, "n": line}]
        if uptm:
            await r.set(characterModel + "lut", int(time.time()))
            character["lut"] = int(time.time())
        return character
    
    async def _petJoin(self, client, pid):
        pet = await self._getPetModel(client, str(pid))
        msg = ["pet.jn", {"nw": True, "pet": pet, "psx": pet["psx"], "psy": pet["psy"]}]
        await client.send(msg)
    
    async def _logicCharacterLinePet(self, uid, pid):
        r = self.server.redis
        characterLineTypes = ["st", "hp", "hl", "hg", "cf"]
        petsModel = f"uid:{uid}:pets"
        character = {}
        if pid not in await r.lrange(petsModel, 0, -1):
            return {}
        petModel = f"uid:{uid}:pet:{pid}:"
        characterModel = petModel + "chrctr:"
        character["l"] = {}
        lastUpdateCharacter = int(time.time()) - int(await r.get(characterModel + "lut"))
        for line in characterLineTypes:
            ln = await r.get(characterModel + f"line:{line}")
            if not ln:
                await self._createCharacterPet(uid, pid)
                ln = await r.get(characterModel + f"line:{line}")
            ln = float(float(ln) / 100)  # x.x float
            if line == "st":
                i = 5  # снять значение за 1 час
                minusIndex = (lastUpdateCharacter / (60 * 60)) * i
                if ln < minusIndex:
                    await r.set(characterModel + f"line:{line}", 0)
                else:
                    await r.set(characterModel + f"line:{line}", int((ln - minusIndex) * 100))
                # сытость
            elif line == "hp":
                i = 10  # снять значение за 1 час
                minusIndex = (lastUpdateCharacter / (60 * 60)) * i
                if ln < minusIndex:
                    await r.set(characterModel + f"line:{line}", 0)
                else:
                    await r.set(characterModel + f"line:{line}", int((ln - minusIndex) * 100))
                # радость
            elif line == "hl":
                oldcharacter = await self._updateCharacterPet(uid, pid, False)
                satiety = int(oldcharacter["l"][0]["v"])
                if satiety < 50:
                    minusIndex = 8
                    if ln < minusIndex:
                        await r.set(characterModel + f"line:{line}", 0)
                    else:
                        await r.set(characterModel + f"line:{line}", int((ln - minusIndex) * 100))
                # здоровье
            elif line == "hg":
                i = 15  # снять значение за 1 час
                minusIndex = (lastUpdateCharacter / (60 * 60)) * i
                if ln < minusIndex:
                    await r.set(characterModel + f"line:{line}", 0)
                else:
                    await r.set(characterModel + f"line:{line}", int((ln - minusIndex) * 100))
                # гигиена
            elif line == "cf":
                i = 20  # снять значение за 1 час
                minusIndex = (lastUpdateCharacter / (60 * 60)) * i
                if ln < minusIndex:
                    await r.set(characterModel + f"line:{line}", 0)
                else:
                    await r.set(characterModel + f"line:{line}", int((ln - minusIndex) * 100))
                # жизнерадостность
                
    async def _createCharacterPet(self, client, pid):
        r = self.server.redis
        try:
            uid = client.uid
        except:
            uid = client
        characterLineTypes = ["st", "hp", "hl", "hg", "cf"]
        petsModel = f"uid:{uid}:pets"
        if pid not in await r.lrange(petsModel, 0, -1):
            return {}
        petModel = f"uid:{uid}:pet:{pid}:"
        characterModel = petModel + "chrctr:"
        lineModel = petModel + "chrctr:line:"
        for line in characterLineTypes:
            await r.set(lineModel + line, 10000)  # divide 10000 / 100 = 100.00%
        await r.set(characterModel + "lut", int(time.time()))
        # await r.set(characterModel + "ui", ) used items soon
    
    async def buy(self, msg, client):
        houseId = msg[2]["phid"]
        namePet = msg[2]["n"]
        colorIndexPet = msg[2]["ci"]
        petTypeId = msg[2]["tpid"]
        await self._addPet(client, houseId, namePet, colorIndexPet, petTypeId)
        
    async def editName(self, msg, client):
        pid = msg[2]["id"]
        nm = msg[2]["n"]
        r = self.server.redis
        uid = client.uid
        petsModel = f"uid:{uid}:pets"
        if str(pid) not in await r.lrange(petsModel, 0, -1):
            return
        petModel = f"uid:{uid}:pet:{pid}:"
        await r.set(petModel+"nm", nm)
        msg[2]["id"] = str(msg[2]["id"])
        await client.send(msg[1:])
        
    async def _petMove(self, pid, client, pos=(None, None)):
        commandWalk = ["pet.wk", {}]
        petModel = f"uid:{client.uid}:pet:{pid}:"
        if pos == (None, None):
            houseId = int(await self.server.redis.get(petModel + "hid"))
            getHouse = await self.server.getArgsItemMapSmart(client, houseId)
            x = round(float(getHouse["x"]))
            y = round(float(getHouse["y"]))
            maxX = x + 6
            maxY = y + 6
            minX = x - 6
            minY = y - 6
            x = random.randint(minX, maxX)
            y = random.randint(minY, maxY)
            xp = round(float(await self.server.redis.get(petModel + "wx")))
            yp = round(float(await self.server.redis.get(petModel + "wy")))
            path = self.gen_path_move(xp, yp, x, y)
        else:
            return
        commandWalk[1]["psy"] = yp
        commandWalk[1]["psx"] = xp
        commandWalk[1]["dur"] = len(path)*2
        commandWalk[1]["path"] = path
        commandWalk[1]["pid"] = "pet"+str(pid)
        commandWalk[1]["act"] = "walk"
        await self.server.redis.set(petModel + "wx", x)
        await self.server.redis.set(petModel + "wy", y)
        # bad method
        """for xuy in range()
        ["pet.wk", {psy: 49, path: [{y: 49, x: 19}, {y: 49, x: 20}, {y: 49, x: 21}, {y: 50, x: 22}, {y: 51, x: 23},
                                    {y: 52, x: 24}, {y: 53, x: 24}], dur: 6, pid: "pet3439172", act: "walk", psx: 18}]"""
        await self.server.send_everybody_room(client.room, commandWalk)
        
    def gen_path_move(self, x, y, sx, sy):
        path = []
        while sx != x and sy != y:
            if (sx < x):
                sx+=1
            if (sy < y):
                sy+=1
            if (sx > x):
                sx-=1
            if (sy > y):
                sy-=1
            path.append({"y": sy, "x": sx})
        path.reverse()
        return path
    
    async def petInSleep(self, uid, pid) -> bool:
        petModel = f"uid:{uid}:pet:{pid}:"
        return int(await self.server.redis.get(petModel + "sltm")) > int(time.time())
        
    async def _background(self):
        r = self.server.redis
        while True:
            for onl in range(1, await self.server.redis.incrby("uids", 0)+1):
                petsModel = f"uid:{onl}:pets"
                pets = await r.lrange(petsModel, 0, -1)
                if not pets:
                    continue
                for pet in pets:
                    await self._logicCharacterLinePet(onl, pet)
            await asyncio.sleep(60*60)

    async def background_two(self):
        r = self.server.redis
        while True:
            for onl in self.server.online:
                petsModel = f"uid:{onl}:pets"
                pets = await r.lrange(petsModel, 0, -1)
                if not pets:
                    continue
                for pet in pets:
                    if await self.petInSleep(onl, pet):
                        continue
                    await self._petMove(pet, self.server.online[onl])
            await asyncio.sleep(random.randint(30, 50))
