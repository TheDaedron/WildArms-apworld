# Wild Arms
 
## What does randomization do to this game?
 
Every item pickup in Wild Arms is a location: chests, barrels, boxes, runes, key items, special-move rewards, and gifts
from NPCs. What each one holds is shuffled into the multiworld, along with the items other players send you.
 
## What items and locations get randomized?
 
Locations:
 
- Chests and trap chests
- Items hidden in barrels and boxes
- Key items, such as Kizim Fire or the Ocarina
- Runes found throughout the game
- Fast Draw and other special-move rewards
- Rewards given by characters

Items in the pool:
 
- Gella, in several amounts
- Consumables, such as berries, apples, and Crest Graphs
- Equipment, as progressive chains for each character's weapon, armor, head slot, and left hand
- Tools, such as Bombs, Skates, the Power Glove, and the Lighter
- Rudy's ARMs and Jack's Fast Draws
- Cecilia's spells (every spell except Escape and Teleport)

Enemies no longer drop or carry equipment. All equipment are removed from shops, so equipment comes from the item pool.
 
## What other changes are made to the game?
 
Several quality-of-life changes speed up the game. The more important ones:
 
- The prologues for each character are skipped. The game starts in Surf Village with the three already together.
- Rudy starts with the Radar. Cecilia starts with the Pocket Watch.
- Cecilia starts with the Teleport and Escape spells, and both cost no MP.
- Most cutscenes are skipped or sped up.
- EXP and Gella from battles can be multiplied.

## Where is my starting inventory?
 
Items from your starting inventory are delivered when the client connects to the server.
 
## What does another world's item look like in Wild Arms?
 
Containers open as usual, and your active character picks the item up. The picture and name on the pickup message are
a preview: your own item types show their real icon, Gella shows the Gella icon, and everything else shows the
Archipelago icon. The item's name and the player it goes to are not shown in the game.
 
Opening the container checks the location. The item itself, including your own items, is delivered by the client.
 
## When the player receives an item, what happens?
 
The client writes the item directly into your game and shows a message on screen, for example `Received Heal Berry!`.
 
- Gella is added to your total.
- Tools go to the right character. An item you already own shows `Already have ...`.
- Weapons, armor, and headgear are equipped as the next tier of their chain. Left-hand pieces and Runes are put in your inventory.
- ARMs, Fast Draws, and spells are learned into the first free slot, and the message names the kind: `Received <ARM> Prism Ray!`, `Received <Fast Draw> Heal Blade!`, or `Received <Spell> Shield!`.
- If your inventory is full, the message says the item could not be delivered, and the client tries again until there is room.
The client stores how many items it has delivered in your save, so items are not repeated when you reload.
 
A save made on a different seed, or on an unrandomized game, is detected. The client shows an error and delivers nothing until you load a save from this seed.
 
A few rewards, such as some runes, special moves, and gifts, still give their original item when you collect them, in addition to checking the location.
 
## Frequently Asked Questions
 
**I have the Holy Berry, but Zombie isn't spawning.**
 
You must enter Berry Cave from Filgaia to trigger the battle.
 
**I opened a container and nothing arrived.**
 
Due to current restrictions, all items are delivered by the client, not by the game. Make sure a client is connected.
 
Claude finished the response
