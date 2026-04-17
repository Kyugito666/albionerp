Q_MULT  = {"normal": 1.0, "good": 1.02, "outstanding": 1.05, "excellent": 1.10, "masterpiece": 1.20}
E_MULT  = {0: 1.0, 1: 1.15, 2: 1.30, 3: 1.45, 4: 1.60}
PIE_MULT = {"pie_7_0": 0.30, "pie_7_1": 0.315, "pie_7_2": 0.33, "pie_7_3": 0.345, "none": 0.0}
ENCHANTS = [".0", ".1", ".2", ".3", ".4"]
JOURNAL_TYPES = ["fletcher", "imbuer", "blacksmith", "toolmaker"]
JOURNAL_NPC_PRICES = {3: 1154, 4: 2308, 5: 4616, 6: 9232, 7: 18464, 8: 36928}
JOURNAL_TYPES = ["fletcher", "imbuer", "blacksmith", "toolmaker"]
JOURNAL_NPC_PRICES = {3: 1154, 4: 2308, 5: 4616, 6: 9232, 7: 18464, 8: 36928}

IV_BASE = {3: 8, 4: 16, 5: 32, 6: 64, 7: 128, 8: 256}
IV_MULT = {".0": 1, ".1": 2, ".2": 4, ".3": 8, ".4": 16}
RAW_AMOUNT_NEEDED = {3: 2, 4: 2, 5: 3, 6: 4, 7: 5, 8: 5}
RESOURCE_WEIGHT = {3: 0.3, 4: 0.5, 5: 0.8, 6: 1.3, 7: 2.1, 8: 3.4}
FAME_PER_RESOURCE = {3: 7.5, 4: 22.5, 5: 90, 6: 270, 7: 645, 8: 1395}
JOURNAL_FAME_REQ = {3: 1800, 4: 3600, 5: 7200, 6: 14400, 7: 28380, 8: 58590}
ENCHANT_FAME_MULT = {".0": 1, ".1": 2, ".2": 4, ".3": 8, ".4": 16}
IP_TIER_BASE = {3: 600, 4: 700, 5: 800, 6: 900, 7: 1000, 8: 1100}
IP_QUALITY   = {"normal": 0, "good": 20, "outstanding": 40, "excellent": 60, "masterpiece": 100}

# ==========================================
# MASTER NODE MAPPING (TERMASUK BAG & CAPE)
# ==========================================
ITEM_TO_MAIN_SPEC = {
    # ---------------- WARRIOR ----------------
    "Soldier Helmet": "Plate Helmet Crafter", "Knight Helmet": "Plate Helmet Crafter", "Guardian Helmet": "Plate Helmet Crafter", "Graveguard Helmet": "Plate Helmet Crafter", "Demon Helmet": "Plate Helmet Crafter", "Judicator Helmet": "Plate Helmet Crafter",
    "Soldier Armor": "Plate Armor Crafter", "Knight Armor": "Plate Armor Crafter", "Guardian Armor": "Plate Armor Crafter", "Graveguard Armor": "Plate Armor Crafter", "Demon Armor": "Plate Armor Crafter", "Judicator Armor": "Plate Armor Crafter",
    "Soldier Boots": "Plate Boots Crafter", "Knight Boots": "Plate Boots Crafter", "Guardian Boots": "Plate Boots Crafter", "Graveguard Boots": "Plate Boots Crafter", "Demon Boots": "Plate Boots Crafter", "Judicator Boots": "Plate Boots Crafter",
    
    "Broadsword": "Sword Crafter", "Claymore": "Sword Crafter", "Dual Swords": "Sword Crafter", "Clarent Blade": "Sword Crafter", "Carving Sword": "Sword Crafter", "Galatine Pair": "Sword Crafter", "Kingmaker": "Sword Crafter", "Broadsword (Awakened)": "Sword Crafter",
    "Battleaxe": "Axe Crafter", "Halberd": "Axe Crafter", "Greataxe": "Axe Crafter", "Carrioncaller": "Axe Crafter", "Infernal Scythe": "Axe Crafter", "Bear Paws": "Axe Crafter", "Realmbreaker": "Axe Crafter",
    "Mace": "Mace Crafter", "Heavy Mace": "Mace Crafter", "Morning Star": "Mace Crafter", "Bedrock Mace": "Mace Crafter", "Incubus Mace": "Mace Crafter", "Camlann Mace": "Mace Crafter", "Oathkeepers": "Mace Crafter",
    "Hammer": "Hammer Crafter", "Polehammer": "Hammer Crafter", "Great Hammer": "Hammer Crafter", "Tombhammer": "Hammer Crafter", "Forge Hammers": "Hammer Crafter", "Grovekeeper": "Hammer Crafter", "Hand of Justice": "Hammer Crafter",
    
    "Light Crossbow": "Crossbow Crafter", "Crossbow": "Crossbow Crafter", "Heavy Crossbow": "Crossbow Crafter", "Weeping Repeater": "Crossbow Crafter", "Boltcasters": "Crossbow Crafter", "Siegebow": "Crossbow Crafter", "Energy Shaper": "Crossbow Crafter",
    "Shield": "Shield Crafter", "Sarcophagus": "Shield Crafter", "Caitiff Shield": "Shield Crafter", "Facebreaker": "Shield Crafter", "Astral Aegis": "Shield Crafter",
    
    # War Gloves
    "Brawler Gloves": "War Gloves Crafter", "Battle Bracers": "War Gloves Crafter", "Spiked Gauntlets": "War Gloves Crafter", "Ursine Maulers": "War Gloves Crafter", "Hellfire Hands": "War Gloves Crafter", "Ravenstrike Cestus": "War Gloves Crafter", "Fists of Avalon": "War Gloves Crafter",

    # ---------------- HUNTER ----------------
    "Mercenary Hood": "Leather Hood Crafter", "Hunter Hood": "Leather Hood Crafter", "Assassin Hood": "Leather Hood Crafter", "Stalker Hood": "Leather Hood Crafter", "Hellion Hood": "Leather Hood Crafter", "Specter Hood": "Leather Hood Crafter",
    "Mercenary Jacket": "Leather Jacket Crafter", "Hunter Jacket": "Leather Jacket Crafter", "Assassin Jacket": "Leather Jacket Crafter", "Stalker Jacket": "Leather Jacket Crafter", "Hellion Jacket": "Leather Jacket Crafter", "Specter Jacket": "Leather Jacket Crafter",
    "Mercenary Shoes": "Leather Shoes Crafter", "Hunter Shoes": "Leather Shoes Crafter", "Assassin Shoes": "Leather Shoes Crafter", "Stalker Shoes": "Leather Shoes Crafter", "Hellion Shoes": "Leather Shoes Crafter", "Specter Shoes": "Leather Shoes Crafter",
    
    "Bow": "Bow Crafter", "Warbow": "Bow Crafter", "Longbow": "Bow Crafter", "Whispering Bow": "Bow Crafter", "Wailing Bow": "Bow Crafter", "Bow of Badon": "Bow Crafter", "Mist Piercer": "Bow Crafter",
    "Dagger": "Dagger Crafter", "Dagger Pair": "Dagger Crafter", "Claws": "Dagger Crafter", "Bloodletter": "Dagger Crafter", "Demon Fang": "Dagger Crafter", "Deathgivers": "Dagger Crafter", "Bridled Fury": "Dagger Crafter",
    "Spear": "Spear Crafter", "Pike": "Spear Crafter", "Glaive": "Spear Crafter", "Heron Spear": "Spear Crafter", "Spirithunter": "Spear Crafter", "Trinity Spear": "Spear Crafter", "Daybreaker": "Spear Crafter",
    "Quarterstaff": "Quarterstaff Crafter", "Iron-clad Staff": "Quarterstaff Crafter", "Double Bladed Staff": "Quarterstaff Crafter", "Black Monk Stave": "Quarterstaff Crafter", "Soulscythe": "Quarterstaff Crafter", "Staff of Balance": "Quarterstaff Crafter", "Grailseeker": "Quarterstaff Crafter",
    
    "Nature Staff": "Nature Staff Crafter", "Great Nature Staff": "Nature Staff Crafter", "Wild Staff": "Nature Staff Crafter", "Druidic Staff": "Nature Staff Crafter", "Blight Staff": "Nature Staff Crafter", "Rampant Staff": "Nature Staff Crafter", "Ironroot Staff": "Nature Staff Crafter",
    "Torch": "Torch Crafter", "Mistcaller": "Torch Crafter", "Leering Cane": "Torch Crafter", "Cryptcandle": "Torch Crafter", "Sacred Scepter": "Torch Crafter",

    # Shapeshifter
    "Prowling Staff": "Shapeshifter Crafter", "Bloodmoon Staff": "Shapeshifter Crafter", "Earthrune Staff": "Shapeshifter Crafter", "Rootbound Staff": "Shapeshifter Crafter", "Primal Staff": "Shapeshifter Crafter", "Lightcaller": "Shapeshifter Crafter", "Hellspawn Staff": "Shapeshifter Crafter",

    # ---------------- MAGE ----------------
    "Scholar Cowl": "Cloth Helmet Crafter", "Cleric Cowl": "Cloth Helmet Crafter", "Mage Cowl": "Cloth Helmet Crafter", "Druid Cowl": "Cloth Helmet Crafter", "Fiend Cowl": "Cloth Helmet Crafter", "Cultist Cowl": "Cloth Helmet Crafter",
    "Scholar Robe": "Cloth Armor Crafter", "Cleric Robe": "Cloth Armor Crafter", "Mage Robe": "Cloth Armor Crafter", "Druid Robe": "Cloth Armor Crafter", "Fiend Robe": "Cloth Armor Crafter", "Cultist Robe": "Cloth Armor Crafter",
    "Scholar Sandals": "Cloth Shoes Crafter", "Cleric Sandals": "Cloth Shoes Crafter", "Mage Sandals": "Cloth Shoes Crafter", "Druid Sandals": "Cloth Shoes Crafter", "Fiend Sandals": "Cloth Shoes Crafter", "Cultist Sandals": "Cloth Shoes Crafter",
    
    "Fire Staff": "Fire Staff Crafter", "Great Fire Staff": "Fire Staff Crafter", "Infernal Staff": "Fire Staff Crafter", "Wildfire Staff": "Fire Staff Crafter", "Brimstone Staff": "Fire Staff Crafter", "Blazing Staff": "Fire Staff Crafter", "Dawnsong": "Fire Staff Crafter",
    "Holy Staff": "Holy Staff Crafter", "Great Holy Staff": "Holy Staff Crafter", "Divine Staff": "Holy Staff Crafter", "Lifetouch Staff": "Holy Staff Crafter", "Fallen Staff": "Holy Staff Crafter", "Redemption Staff": "Holy Staff Crafter", "Hallowfall": "Holy Staff Crafter",
    "Arcane Staff": "Arcane Staff Crafter", "Great Arcane Staff": "Arcane Staff Crafter", "Enigmatic Staff": "Arcane Staff Crafter", "Witchwork Staff": "Arcane Staff Crafter", "Occult Staff": "Arcane Staff Crafter", "Evensong": "Arcane Staff Crafter", "Astral Staff": "Arcane Staff Crafter",
    "Frost Staff": "Frost Staff Crafter", "Great Frost Staff": "Frost Staff Crafter", "Glacial Staff": "Frost Staff Crafter", "Hoarfrost Staff": "Frost Staff Crafter", "Icicle Staff": "Frost Staff Crafter", "Permafrost Prism": "Frost Staff Crafter", "Chillhowl": "Frost Staff Crafter",
    "Cursed Staff": "Cursed Staff Crafter", "Great Cursed Staff": "Cursed Staff Crafter", "Demonic Staff": "Cursed Staff Crafter", "Lifecurse Staff": "Cursed Staff Crafter", "Cursed Skull": "Cursed Staff Crafter", "Damnation Staff": "Cursed Staff Crafter", "Shadowcaller": "Cursed Staff Crafter",
    
    "Tome of Spells": "Tome Crafter", "Eye of Secrets": "Tome Crafter", "Muisak": "Tome Crafter", "Taproot": "Tome Crafter", "Celestial Censer": "Tome Crafter",

    # ---------------- TOOLMAKER ----------------
    "Bag": "Bag Crafter", "Satchel of Insight": "Bag Crafter",
    "Cape": "Cape Crafter", 
    "Lymhurst Cape": "Cape Crafter", "Fort Sterling Cape": "Cape Crafter", "Bridgewatch Cape": "Cape Crafter",
    "Martlock Cape": "Cape Crafter", "Thetford Cape": "Cape Crafter", "Caerleon Cape": "Cape Crafter", "Brecilien Cape": "Cape Crafter",
    "Demon Cape": "Cape Crafter", "Undead Cape": "Cape Crafter", "Keeper Cape": "Cape Crafter", "Morgana Cape": "Cape Crafter", 
    "Heretic Cape": "Cape Crafter", "Avalonian Cape": "Cape Crafter",

    # ---------------- CONSUMABLES ----------------
    "Goat Stew T4": "Chef", "Mutton Stew T6": "Chef", "Beef Stew T8": "Chef", 
    "Chicken Omelette T3": "Chef", "Goose Omelette T5": "Chef", "Pork Omelette T7": "Chef", 
    "Wheat Soup T3": "Chef", "Cabbage Soup T5": "Chef", "Turnip Salad T4": "Chef", 
    "Beef Sandwich T8": "Chef", "Pork Pie T7": "Chef", "Roast Pork T7": "Chef",
    
    "Minor Healing Potion T4": "Alchemist", "Healing Potion T6": "Alchemist", "Major Healing Potion T8": "Alchemist",
    "Minor Energy Potion T4": "Alchemist", "Energy Potion T6": "Alchemist", "Major Energy Potion T8": "Alchemist",
    "Minor Poison Potion T4": "Alchemist", "Poison Potion T6": "Alchemist", "Major Poison Potion T8": "Alchemist",
    "Minor Resistance Potion T4": "Alchemist", "Resistance Potion T6": "Alchemist", "Major Resistance Potion T8": "Alchemist",
    "Invisibility Potion T8": "Alchemist"
}

# ==========================================
# AUTO-DETECT BONUS CITIES
# ==========================================
REFINE_BONUS_CITY = {
    "cloth": "Lymhurst",
    "leather": "Martlock",
    "steel": "Thetford",
    "plank": "Fort Sterling",
    "block": "Bridgewatch"
}

ITEM_BONUS_CITY = {
    # Lymhurst
    "Broadsword": "Lymhurst", "Claymore": "Lymhurst", "Dual Swords": "Lymhurst", "Clarent Blade": "Lymhurst", "Carving Sword": "Lymhurst", "Galatine Pair": "Lymhurst",
    "Bow": "Lymhurst", "Warbow": "Lymhurst", "Longbow": "Lymhurst", "Whispering Bow": "Lymhurst", "Wailing Bow": "Lymhurst", "Bow of Badon": "Lymhurst",
    "Arcane Staff": "Lymhurst", "Great Arcane Staff": "Lymhurst", "Enigmatic Staff": "Lymhurst", "Witchwork Staff": "Lymhurst", "Occult Staff": "Lymhurst", "Evensong": "Lymhurst",
    "Mercenary Hood": "Lymhurst", "Hunter Hood": "Lymhurst", "Assassin Hood": "Lymhurst", "Stalker Hood": "Lymhurst", "Hellion Hood": "Lymhurst", "Specter Hood": "Lymhurst",
    "Mercenary Shoes": "Lymhurst", "Hunter Shoes": "Lymhurst", "Assassin Shoes": "Lymhurst", "Stalker Shoes": "Lymhurst", "Hellion Shoes": "Lymhurst", "Specter Shoes": "Lymhurst",
    # Bridgewatch
    "Dagger": "Bridgewatch", "Dagger Pair": "Bridgewatch", "Claws": "Bridgewatch", "Bloodletter": "Bridgewatch", "Demon Fang": "Bridgewatch", "Deathgivers": "Bridgewatch",
    "Light Crossbow": "Bridgewatch", "Crossbow": "Bridgewatch", "Heavy Crossbow": "Bridgewatch", "Weeping Repeater": "Bridgewatch", "Boltcasters": "Bridgewatch", "Siegebow": "Bridgewatch",
    "Cursed Staff": "Bridgewatch", "Great Cursed Staff": "Bridgewatch", "Demonic Staff": "Bridgewatch", "Lifecurse Staff": "Bridgewatch", "Cursed Skull": "Bridgewatch", "Damnation Staff": "Bridgewatch",
    "Soldier Armor": "Bridgewatch", "Knight Armor": "Bridgewatch", "Guardian Armor": "Bridgewatch", "Graveguard Armor": "Bridgewatch", "Demon Armor": "Bridgewatch", "Judicator Armor": "Bridgewatch",
    "Soldier Boots": "Bridgewatch", "Knight Boots": "Bridgewatch", "Guardian Boots": "Bridgewatch", "Graveguard Boots": "Bridgewatch", "Demon Boots": "Bridgewatch", "Judicator Boots": "Bridgewatch",
    # Martlock
    "Battleaxe": "Martlock", "Halberd": "Martlock", "Greataxe": "Martlock", "Carrioncaller": "Martlock", "Infernal Scythe": "Martlock", "Bear Paws": "Martlock",
    "Quarterstaff": "Martlock", "Iron-clad Staff": "Martlock", "Double Bladed Staff": "Martlock", "Black Monk Stave": "Martlock", "Soulscythe": "Martlock", "Staff of Balance": "Martlock",
    "Frost Staff": "Martlock", "Great Frost Staff": "Martlock", "Glacial Staff": "Martlock", "Hoarfrost Staff": "Martlock", "Icicle Staff": "Martlock", "Permafrost Prism": "Martlock",
    "Soldier Helmet": "Martlock", "Knight Helmet": "Martlock", "Guardian Helmet": "Martlock", "Graveguard Helmet": "Martlock", "Demon Helmet": "Martlock", "Judicator Helmet": "Martlock",
    "Shield": "Martlock", "Sarcophagus": "Martlock", "Caitiff Shield": "Martlock", "Facebreaker": "Martlock",
    # Thetford
    "Mace": "Thetford", "Heavy Mace": "Thetford", "Morning Star": "Thetford", "Bedrock Mace": "Thetford", "Incubus Mace": "Thetford", "Camlann Mace": "Thetford",
    "Nature Staff": "Thetford", "Great Nature Staff": "Thetford", "Wild Staff": "Thetford", "Druidic Staff": "Thetford", "Blight Staff": "Thetford", "Rampant Staff": "Thetford",
    "Fire Staff": "Thetford", "Great Fire Staff": "Thetford", "Infernal Staff": "Thetford", "Wildfire Staff": "Thetford", "Brimstone Staff": "Thetford", "Blazing Staff": "Thetford",
    "Mercenary Jacket": "Thetford", "Hunter Jacket": "Thetford", "Assassin Jacket": "Thetford", "Stalker Jacket": "Thetford", "Hellion Jacket": "Thetford", "Specter Jacket": "Thetford",
    "Scholar Cowl": "Thetford", "Cleric Cowl": "Thetford", "Mage Cowl": "Thetford", "Druid Cowl": "Thetford", "Fiend Cowl": "Thetford", "Cultist Cowl": "Thetford",
    # Fort Sterling
    "Hammer": "Fort Sterling", "Polehammer": "Fort Sterling", "Great Hammer": "Fort Sterling", "Tombhammer": "Fort Sterling", "Forge Hammers": "Fort Sterling", "Grovekeeper": "Fort Sterling",
    "Spear": "Fort Sterling", "Pike": "Fort Sterling", "Glaive": "Fort Sterling", "Heron Spear": "Fort Sterling", "Spirithunter": "Fort Sterling", "Trinity Spear": "Fort Sterling",
    "Holy Staff": "Fort Sterling", "Great Holy Staff": "Fort Sterling", "Divine Staff": "Fort Sterling", "Lifetouch Staff": "Fort Sterling", "Fallen Staff": "Fort Sterling", "Redemption Staff": "Fort Sterling",
    "Scholar Robe": "Fort Sterling", "Cleric Robe": "Fort Sterling", "Mage Robe": "Fort Sterling", "Druid Robe": "Fort Sterling", "Fiend Robe": "Fort Sterling", "Cultist Robe": "Fort Sterling",
    "Scholar Sandals": "Fort Sterling", "Cleric Sandals": "Fort Sterling", "Mage Sandals": "Fort Sterling", "Druid Sandals": "Fort Sterling", "Fiend Sandals": "Fort Sterling", "Cultist Sandals": "Fort Sterling",
    # --- Cooking (Caerleon) ---
    "Goat Stew T4": "Caerleon", "Mutton Stew T6": "Caerleon", "Beef Stew T8": "Caerleon",
    "Chicken Omelette T3": "Caerleon", "Goose Omelette T5": "Caerleon", "Pork Omelette T7": "Caerleon",
    "Wheat Soup T3": "Caerleon", "Cabbage Soup T5": "Caerleon", "Turnip Salad T4": "Caerleon",
    "Beef Sandwich T8": "Caerleon", "Pork Pie T7": "Caerleon", "Roast Pork T7": "Caerleon",
    # --- Alchemy (Brecilien) ---
    "Minor Healing Potion T4": "Brecilien", "Healing Potion T6": "Brecilien", "Major Healing Potion T8": "Brecilien",
    "Minor Energy Potion T4": "Brecilien", "Energy Potion T6": "Brecilien", "Major Energy Potion T8": "Brecilien",
    "Minor Poison Potion T4": "Brecilien", "Poison Potion T6": "Brecilien", "Major Poison Potion T8": "Brecilien",
    "Minor Resistance Potion T4": "Brecilien", "Resistance Potion T6": "Brecilien", "Major Resistance Potion T8": "Brecilien",
    "Invisibility Potion T8": "Brecilien"
}

FARMING_BONUS_CITY = {
    # Fort Sterling
    "turnip": "Fort Sterling", "ghoul_yarrow": "Fort Sterling", "chicken_egg": "Fort Sterling", "sheep_milk": "Fort Sterling", "raw_chicken": "Fort Sterling", "raw_mutton": "Fort Sterling",
    # Lymhurst
    "carrot": "Lymhurst", "pumpkin": "Lymhurst", "burdock": "Lymhurst", "goose_egg": "Lymhurst", "raw_goose": "Lymhurst",
    # Bridgewatch
    "bean": "Bridgewatch", "corn": "Bridgewatch", "dragon_teasel": "Bridgewatch", "goat_milk": "Bridgewatch", "raw_goat": "Bridgewatch",
    # Martlock
    "wheat": "Martlock", "potato": "Martlock", "foxglove": "Martlock", "cow_milk": "Martlock", "raw_beef": "Martlock",
    # Thetford
    "cabbage": "Thetford", "comfrey": "Thetford", "mullein": "Thetford", "raw_pork": "Thetford",
    # Caerleon
    "agaric": "Caerleon"
}

FRAGMENT_MAPPING = {
    "Druid Cowl": "Rune", "Fiend Cowl": "Soul", "Cultist Cowl": "Relic",
    "Stalker Hood": "Rune", "Hellion Hood": "Soul", "Specter Hood": "Relic",
    "Graveguard Helmet": "Rune", "Demon Helmet": "Soul", "Judicator Helmet": "Relic",
    "Druid Robe": "Rune", "Fiend Robe": "Soul", "Cultist Robe": "Relic",
    "Stalker Jacket": "Rune", "Hellion Jacket": "Soul", "Specter Jacket": "Relic",
    "Graveguard Armor": "Rune", "Demon Armor": "Soul", "Judicator Armor": "Relic",
    "Druid Sandals": "Rune", "Fiend Sandals": "Soul", "Cultist Sandals": "Relic",
    "Stalker Shoes": "Rune", "Hellion Shoes": "Soul", "Specter Shoes": "Relic",
    "Graveguard Boots": "Rune", "Demon Boots": "Soul", "Judicator Boots": "Relic",
    "Clarent Blade": "Rune", "Carving Sword": "Soul", "Galatine Pair": "Relic",
    "Carrioncaller": "Rune", "Infernal Scythe": "Soul", "Bear Paws": "Relic",
    "Bedrock Mace": "Rune", "Incubus Mace": "Soul", "Camlann Mace": "Relic",
    "Tombhammer": "Rune", "Forge Hammers": "Soul", "Grovekeeper": "Relic",
    "Weeping Repeater": "Rune", "Boltcasters": "Soul", "Siegebow": "Relic",
    "Whispering Bow": "Rune", "Wailing Bow": "Soul", "Bow of Badon": "Relic",
    "Heron Spear": "Rune", "Spirithunter": "Soul", "Trinity Spear": "Relic",
    "Bloodletter": "Rune", "Demon Fang": "Soul", "Deathgivers": "Relic",
    "Black Monk Stave": "Rune", "Soulscythe": "Soul", "Staff of Balance": "Relic",
    "Wildfire Staff": "Rune", "Brimstone Staff": "Soul", "Blazing Staff": "Relic",
    "Lifetouch Staff": "Rune", "Fallen Staff": "Soul", "Redemption Staff": "Relic",
    "Druidic Staff": "Rune", "Blight Staff": "Soul", "Rampant Staff": "Relic",
    "Hoarfrost Staff": "Rune", "Icicle Staff": "Soul", "Permafrost Prism": "Relic",
    "Witchwork Staff": "Rune", "Occult Staff": "Soul", "Evensong": "Relic",
    "Lifecurse Staff": "Rune", "Cursed Skull": "Soul", "Damnation Staff": "Relic",
    "Eye of Secrets": "Rune", "Muisak": "Soul", "Taproot": "Relic",
    "Mistcaller": "Rune", "Leering Cane": "Soul", "Cryptcandle": "Relic",
    "Sarcophagus": "Rune", "Caitiff Shield": "Soul", "Facebreaker": "Relic"
}

ALBION_MAPPING = {
    # ---------------- ARMORS & SETS ----------------
    "HEAD_CLOTH_SET1": ("helmets", "Scholar Cowl"), "HEAD_CLOTH_SET2": ("helmets", "Cleric Cowl"), "HEAD_CLOTH_SET3": ("helmets", "Mage Cowl"),
    "HEAD_LEATHER_SET1": ("helmets", "Mercenary Hood"), "HEAD_LEATHER_SET2": ("helmets", "Hunter Hood"), "HEAD_LEATHER_SET3": ("helmets", "Assassin Hood"),
    "HEAD_PLATE_SET1": ("helmets", "Soldier Helmet"), "HEAD_PLATE_SET2": ("helmets", "Knight Helmet"), "HEAD_PLATE_SET3": ("helmets", "Guardian Helmet"),

    "HEAD_CLOTH_KEEPER": ("artifact_helmets", "Druid Cowl"), "HEAD_CLOTH_HELL": ("artifact_helmets", "Fiend Cowl"), "HEAD_CLOTH_MORGANA": ("artifact_helmets", "Cultist Cowl"),
    "HEAD_LEATHER_MORGANA": ("artifact_helmets", "Stalker Hood"), "HEAD_LEATHER_HELL": ("artifact_helmets", "Hellion Hood"), "HEAD_LEATHER_UNDEAD": ("artifact_helmets", "Specter Hood"),
    "HEAD_PLATE_UNDEAD": ("artifact_helmets", "Graveguard Helmet"), "HEAD_PLATE_HELL": ("artifact_helmets", "Demon Helmet"), "HEAD_PLATE_KEEPER": ("artifact_helmets", "Judicator Helmet"),

    "ARMOR_CLOTH_SET1": ("armors", "Scholar Robe"), "ARMOR_CLOTH_SET2": ("armors", "Cleric Robe"), "ARMOR_CLOTH_SET3": ("armors", "Mage Robe"),
    "ARMOR_LEATHER_SET1": ("armors", "Mercenary Jacket"), "ARMOR_LEATHER_SET2": ("armors", "Hunter Jacket"), "ARMOR_LEATHER_SET3": ("armors", "Assassin Jacket"),
    "ARMOR_PLATE_SET1": ("armors", "Soldier Armor"), "ARMOR_PLATE_SET2": ("armors", "Knight Armor"), "ARMOR_PLATE_SET3": ("armors", "Guardian Armor"),

    "ARMOR_CLOTH_KEEPER": ("artifact_armors", "Druid Robe"), "ARMOR_CLOTH_HELL": ("artifact_armors", "Fiend Robe"), "ARMOR_CLOTH_MORGANA": ("artifact_armors", "Cultist Robe"),
    "ARMOR_LEATHER_MORGANA": ("artifact_armors", "Stalker Jacket"), "ARMOR_LEATHER_HELL": ("artifact_armors", "Hellion Jacket"), "ARMOR_LEATHER_UNDEAD": ("artifact_armors", "Specter Jacket"),
    "ARMOR_PLATE_UNDEAD": ("artifact_armors", "Graveguard Armor"), "ARMOR_PLATE_HELL": ("artifact_armors", "Demon Armor"), "ARMOR_PLATE_KEEPER": ("artifact_armors", "Judicator Armor"),

    "SHOES_CLOTH_SET1": ("shoes", "Scholar Sandals"), "SHOES_CLOTH_SET2": ("shoes", "Cleric Sandals"), "SHOES_CLOTH_SET3": ("shoes", "Mage Sandals"),
    "SHOES_LEATHER_SET1": ("shoes", "Mercenary Shoes"), "SHOES_LEATHER_SET2": ("shoes", "Hunter Shoes"), "SHOES_LEATHER_SET3": ("shoes", "Assassin Shoes"),
    "SHOES_PLATE_SET1": ("shoes", "Soldier Boots"), "SHOES_PLATE_SET2": ("shoes", "Knight Boots"), "SHOES_PLATE_SET3": ("shoes", "Guardian Boots"),

    "SHOES_CLOTH_KEEPER": ("artifact_shoes", "Druid Sandals"), "SHOES_CLOTH_HELL": ("artifact_shoes", "Fiend Sandals"), "SHOES_CLOTH_MORGANA": ("artifact_shoes", "Cultist Sandals"),
    "SHOES_LEATHER_MORGANA": ("artifact_shoes", "Stalker Shoes"), "SHOES_LEATHER_HELL": ("artifact_shoes", "Hellion Shoes"), "SHOES_LEATHER_UNDEAD": ("artifact_shoes", "Specter Shoes"),
    "SHOES_PLATE_UNDEAD": ("artifact_shoes", "Graveguard Boots"), "SHOES_PLATE_HELL": ("artifact_shoes", "Demon Boots"), "SHOES_PLATE_KEEPER": ("artifact_shoes", "Judicator Boots"),

    # ---------------- WEAPONS ----------------
    "MAIN_SWORD": ("weapons", "Broadsword"), "2H_CLAYMORE": ("weapons", "Claymore"), "2H_DUALSWORD": ("weapons", "Dual Swords"),
    "MAIN_AXE": ("weapons", "Battleaxe"), "2H_HALBERD": ("weapons", "Halberd"), "2H_AXE": ("weapons", "Greataxe"),
    "MAIN_MACE": ("weapons", "Mace"), "2H_MACE": ("weapons", "Heavy Mace"), "2H_FLAIL": ("weapons", "Morning Star"),
    "MAIN_HAMMER": ("weapons", "Hammer"), "2H_POLEHAMMER": ("weapons", "Polehammer"), "2H_HAMMER": ("weapons", "Great Hammer"),
    "MAIN_1HCROSSBOW": ("weapons", "Light Crossbow"), "2H_CROSSBOW": ("weapons", "Crossbow"), "2H_CROSSBOWLARGE": ("weapons", "Heavy Crossbow"),
    "2H_BOW": ("weapons", "Bow"), "2H_WARBOW": ("weapons", "Warbow"), "2H_LONGBOW": ("weapons", "Longbow"),
    "MAIN_SPEAR": ("weapons", "Spear"), "2H_SPEAR": ("weapons", "Pike"), "2H_GLAIVE": ("weapons", "Glaive"),
    "MAIN_DAGGER": ("weapons", "Dagger"), "2H_DAGGERPAIR": ("weapons", "Dagger Pair"), "2H_CLAWPAIR": ("weapons", "Claws"),
    "2H_QUARTERSTAFF": ("weapons", "Quarterstaff"), "2H_IRONCLADEDSTAFF": ("weapons", "Iron-clad Staff"), "2H_DOUBLEBLADEDSTAFF": ("weapons", "Double Bladed Staff"),
    "MAIN_FIRESTAFF": ("weapons", "Fire Staff"), "2H_FIRESTAFF": ("weapons", "Great Fire Staff"), "2H_INFERNOSTAFF": ("weapons", "Infernal Staff"),
    "MAIN_HOLYSTAFF": ("weapons", "Holy Staff"), "2H_HOLYSTAFF": ("weapons", "Great Holy Staff"), "2H_DIVINESTAFF": ("weapons", "Divine Staff"),
    "MAIN_NATURESTAFF": ("weapons", "Nature Staff"), "2H_NATURESTAFF": ("weapons", "Great Nature Staff"), "2H_WILDSTAFF": ("weapons", "Wild Staff"),
    "MAIN_FROSTSTAFF": ("weapons", "Frost Staff"), "2H_FROSTSTAFF": ("weapons", "Great Frost Staff"), "2H_GLACIALSTAFF": ("weapons", "Glacial Staff"),
    "MAIN_ARCANESTAFF": ("weapons", "Arcane Staff"), "2H_ARCANESTAFF": ("weapons", "Great Arcane Staff"), "2H_ENIGMATICSTAFF": ("weapons", "Enigmatic Staff"),
    "MAIN_CURSEDSTAFF": ("weapons", "Cursed Staff"), "2H_CURSEDSTAFF": ("weapons", "Great Cursed Staff"), "2H_DEMONICSTAFF": ("weapons", "Demonic Staff"),

    "MAIN_SCIMITAR_MORGANA": ("artifact_weapons", "Clarent Blade"), "2H_CLEAVER_HELL": ("artifact_weapons", "Carving Sword"), "2H_DUALSCIMITAR_UNDEAD": ("artifact_weapons", "Galatine Pair"),
    "2H_HALBERD_MORGANA": ("artifact_weapons", "Carrioncaller"), "2H_SCYTHE_HELL": ("artifact_weapons", "Infernal Scythe"), "2H_DUALAXE_KEEPER": ("artifact_weapons", "Bear Paws"),
    "MAIN_ROCKMACE_KEEPER": ("artifact_weapons", "Bedrock Mace"), "MAIN_MACE_HELL": ("artifact_weapons", "Incubus Mace"), "2H_MACE_MORGANA": ("artifact_weapons", "Camlann Mace"),
    "2H_HAMMER_UNDEAD": ("artifact_weapons", "Tombhammer"), "2H_DUALHAMMER_HELL": ("artifact_weapons", "Forge Hammers"), "2H_RAM_KEEPER": ("artifact_weapons", "Grovekeeper"),
    "2H_CROSSBOWLARGE_UNDEAD": ("artifact_weapons", "Weeping Repeater"), "2H_DUALCROSSBOW_HELL": ("artifact_weapons", "Boltcasters"), "2H_CROSSBOWLARGE_MORGANA": ("artifact_weapons", "Siegebow"),
    "2H_BOW_UNDEAD": ("artifact_weapons", "Whispering Bow"), "2H_BOW_HELL": ("artifact_weapons", "Wailing Bow"), "2H_BOW_KEEPER": ("artifact_weapons", "Bow of Badon"),
    "MAIN_SPEAR_KEEPER": ("artifact_weapons", "Heron Spear"), "2H_HARPOON_HELL": ("artifact_weapons", "Spirithunter"), "2H_TRIDENT_UNDEAD": ("artifact_weapons", "Trinity Spear"),
    "MAIN_DAGGER_MORGANA": ("artifact_weapons", "Bloodletter"), "MAIN_DAGGER_HELL": ("artifact_weapons", "Demon Fang"), "2H_DUALDAGGER_UNDEAD": ("artifact_weapons", "Deathgivers"),
    "2H_QUARTERSTAFF_MORGANA": ("artifact_weapons", "Black Monk Stave"), "2H_TWINSCYTHE_HELL": ("artifact_weapons", "Soulscythe"), "2H_ROCKSTAFF_KEEPER": ("artifact_weapons", "Staff of Balance"),
    "MAIN_FIRESTAFF_MORGANA": ("artifact_weapons", "Wildfire Staff"), "2H_FIRESTAFF_HELL": ("artifact_weapons", "Brimstone Staff"), "2H_FIRESTAFF_KEEPER": ("artifact_weapons", "Blazing Staff"),
    "MAIN_HOLYSTAFF_MORGANA": ("artifact_weapons", "Lifetouch Staff"), "2H_HOLYSTAFF_HELL": ("artifact_weapons", "Fallen Staff"), "2H_HOLYSTAFF_UNDEAD": ("artifact_weapons", "Redemption Staff"),
    "MAIN_NATURESTAFF_KEEPER": ("artifact_weapons", "Druidic Staff"), "2H_NATURESTAFF_HELL": ("artifact_weapons", "Blight Staff"), "2H_NATURESTAFF_MORGANA": ("artifact_weapons", "Rampant Staff"),
    "MAIN_FROSTSTAFF_KEEPER": ("artifact_weapons", "Hoarfrost Staff"), "2H_FROSTSTAFF_HELL": ("artifact_weapons", "Icicle Staff"), "2H_FROSTSTAFF_MORGANA": ("artifact_weapons", "Permafrost Prism"),
    "MAIN_ARCANESTAFF_MORGANA": ("artifact_weapons", "Witchwork Staff"), "2H_ARCANESTAFF_HELL": ("artifact_weapons", "Occult Staff"), "2H_ARCANESTAFF_UNDEAD": ("artifact_weapons", "Evensong"),
    "MAIN_CURSEDSTAFF_MORGANA": ("artifact_weapons", "Lifecurse Staff"), "2H_SKULLORB_HELL": ("artifact_weapons", "Cursed Skull"), "2H_CURSEDSTAFF_UNDEAD": ("artifact_weapons", "Damnation Staff"),

    # ---------------- OFFHANDS ----------------
    "MAIN_BOOK": ("offhands", "Tome of Spells"), "OFF_BOOK": ("offhands", "Tome of Spells"),
    "OFF_TORCH": ("offhands", "Torch"),
    "OFF_SHIELD": ("offhands", "Shield"),

    "MAIN_BOOK_MORGANA": ("artifact_offhands", "Eye of Secrets"), "MAIN_BOOK_KEEPER": ("artifact_offhands", "Muisak"), "MAIN_BOOK_UNDEAD": ("artifact_offhands", "Taproot"),
    "OFF_HORN_KEEPER": ("artifact_offhands", "Mistcaller"), "OFF_JESTERCANE_HELL": ("artifact_offhands", "Leering Cane"), "OFF_LAMP_UNDEAD": ("artifact_offhands", "Cryptcandle"),
    "OFF_SHIELD_UNDEAD": ("artifact_offhands", "Sarcophagus"), "OFF_SHIELD_MORGANA": ("artifact_offhands", "Caitiff Shield"), "OFF_SHIELD_KEEPER": ("artifact_offhands", "Facebreaker"),

    "T4_MEAL_STEW": ("foods", "Goat Stew T4"), "T6_MEAL_STEW": ("foods", "Mutton Stew T6"), "T8_MEAL_STEW": ("foods", "Beef Stew T8"),
    "T3_MEAL_OMELETTE": ("foods", "Chicken Omelette T3"), "T5_MEAL_OMELETTE": ("foods", "Goose Omelette T5"), "T7_MEAL_OMELETTE": ("foods", "Pork Omelette T7"),
    "T3_MEAL_SOUP": ("foods", "Wheat Soup T3"), "T5_MEAL_SOUP": ("foods", "Cabbage Soup T5"),
    "T4_MEAL_SALAD": ("foods", "Turnip Salad T4"),
    "T8_MEAL_SANDWICH": ("foods", "Beef Sandwich T8"),
    "T7_MEAL_PIE": ("foods", "Pork Pie T7"),
    "T7_MEAL_ROAST": ("foods", "Roast Pork T7"),
    "T4_POTION_POISON": ("potions", "Minor Poison Potion T4"), "T6_POTION_POISON": ("potions", "Poison Potion T6"), "T8_POTION_POISON": ("potions", "Major Poison Potion T8"),
    "T4_POTION_HEAL": ("potions", "Minor Healing Potion T4"), "T6_POTION_HEAL": ("potions", "Healing Potion T6"), "T8_POTION_HEAL": ("potions", "Major Healing Potion T8"),
    "T4_POTION_ENERGY": ("potions", "Minor Energy Potion T4"), "T6_POTION_ENERGY": ("potions", "Energy Potion T6"), "T8_POTION_ENERGY": ("potions", "Major Energy Potion T8"),
    "T4_POTION_STONESKIN": ("potions", "Minor Resistance Potion T4"), "T6_POTION_STONESKIN": ("potions", "Resistance Potion T6"), "T8_POTION_STONESKIN": ("potions", "Major Resistance Potion T8"),
    "T8_POTION_INVISIBILITY": ("potions", "Invisibility Potion T8"),

    # 🚀 ---------------- BAGS & CAPES ---------------- 🚀
    "BAG": ("bags", "Bag"),
    "BAG_INSIGHT": ("artifact_bags", "Satchel of Insight"),
    "CAPE": ("capes", "Cape"),
    "CAPEITEM_FW_BRIDGEWATCH": ("artifact_capes", "Bridgewatch Cape"),
    "CAPEITEM_FW_FORTSTERLING": ("artifact_capes", "Fort Sterling Cape"),
    "CAPEITEM_FW_LYMHURST": ("artifact_capes", "Lymhurst Cape"),
    "CAPEITEM_FW_MARTLOCK": ("artifact_capes", "Martlock Cape"),
    "CAPEITEM_FW_THETFORD": ("artifact_capes", "Thetford Cape"),
    "CAPEITEM_FW_CAERLEON": ("artifact_capes", "Caerleon Cape"),
    "CAPEITEM_FW_BRECILIEN": ("artifact_capes", "Brecilien Cape"),
    "CAPEITEM_DEMON": ("artifact_capes", "Demon Cape"),
    "CAPEITEM_UNDEAD": ("artifact_capes", "Undead Cape"),
    "CAPEITEM_KEEPER": ("artifact_capes", "Keeper Cape"),
    "CAPEITEM_MORGANA": ("artifact_capes", "Morgana Cape"),
    "CAPEITEM_HERETIC": ("artifact_capes", "Heretic Cape"),
    "CAPEITEM_AVALON": ("artifact_capes", "Avalonian Cape")
}

LOCATION_MAPPING = {
    "7": "Thetford", "0007": "Thetford", "11": "Thetford", "thetford": "Thetford",
    "1002": "Lymhurst", "1006": "Lymhurst", "lymhurst": "Lymhurst",
    "2004": "Bridgewatch", "2008": "Bridgewatch", "bridgewatch": "Bridgewatch",
    "3008": "Martlock", "3013": "Martlock", "martlock": "Martlock",
    "4002": "Fort Sterling", "4006": "Fort Sterling", "fort sterling": "Fort Sterling",
    "3005": "Caerleon", "caerleon": "Caerleon",
    "5003": "Brecilien", "brecilien": "Brecilien",
    "3003": "Black Market", "black market": "Black Market", "black_market": "Black Market"
}

FRAG_PER_MAT = {4: 12, 5: 48, 6: 192, 7: 768, 8: 3072}

FARMING_MATS_MAPPING = {
    "T8_MEAT": "raw_beef", "T7_MEAT": "raw_pork", "T6_MEAT": "raw_mutton", "T5_MEAT": "raw_goose", "T4_MEAT": "raw_goat", "T3_MEAT": "raw_chicken",
    "T8_PUMPKIN": "pumpkin", "T7_CORN": "corn", "T6_POTATO": "potato", "T5_CABBAGE": "cabbage", "T4_TURNIP": "turnip", "T3_WHEAT": "wheat", "T2_BEAN": "bean", "T1_CARROT": "carrot",
    "T8_YARROW": "ghoul_yarrow", "T7_MULLEIN": "mullein", "T6_FOXGLOVE": "foxglove", "T5_TEASEL": "dragon_teasel", "T4_BURDOCK": "burdock", "T3_COMFREY": "comfrey", "T2_AGARIC": "agaric",
    "T3_FLOUR": "flour", "T3_BREAD": "bread", "T4_BUTTER": "butter", "T6_ALCOHOL": "potato_schnapps",
    "T3_EGG": "chicken_egg", "T5_EGG": "goose_egg", "T4_MILK": "goat_milk", "T6_MILK": "sheep_milk", "T8_MILK": "cow_milk",
    "T1_FISHSAUCE_LEVEL1": "fish_sauce_.1", "T1_FISHSAUCE_LEVEL2": "fish_sauce_.2", "T1_FISHSAUCE_LEVEL3": "fish_sauce_.3",
    "T1_ALCHEMY_EXTRACT_LEVEL1": "arcane_extract_.1", "T1_ALCHEMY_EXTRACT_LEVEL2": "arcane_extract_.2", "T1_ALCHEMY_EXTRACT_LEVEL3": "arcane_extract_.3"
    }

FARMING_GROUPS = {
    "crops": ["pumpkin", "corn", "potato", "cabbage", "turnip", "wheat", "bean", "carrot"],
    "herbs": ["ghoul_yarrow", "mullein", "foxglove", "dragon_teasel", "burdock", "comfrey", "agaric"],
    "meat": ["raw_beef", "raw_pork", "raw_mutton", "raw_goose", "raw_goat", "raw_chicken"],
    "dairy": ["cow_milk", "sheep_milk", "goat_milk", "goose_egg", "chicken_egg"],
    "intermediate": ["flour", "bread", "butter", "potato_schnapps"],
    "enchant": ["fish_sauce_.1", "fish_sauce_.2", "fish_sauce_.3", "arcane_extract_.1", "arcane_extract_.2", "arcane_extract_.3"]
}