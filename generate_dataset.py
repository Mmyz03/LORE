"""
AI-Based Story Recommendation and Retrieval System
Script: Large-Scale Dataset Generator (520+ Curated Public Domain & Genre Stories)

Constructs a rich corpus of 520+ diverse, high-quality stories across all 13 core genres:
1. Horror
2. Mystery
3. Adventure
4. Romance
5. Comedy
6. Fantasy
7. Sci-Fi
8. Thriller
9. Friendship
10. Emotional
11. Moral
12. Children's Stories
13. Bedtime Stories

Output: data/raw/stories.csv
"""

import os
import csv
import random

# Base story templates and narrative building blocks per genre
GENRE_SPECS = {
    "Horror": {
        "themes": [
            ("Haunted Forest", "Forest at Midnight", "Scary", ["ghost", "woods", "shadows", "night", "terror", "creepy", "whisper", "fog"]),
            ("Victorian Mansion", "Decaying Manor", "Terrifying", ["mansion", "spectral", "haunted house", "attic", "screams", "curse", "shiver"]),
            ("Midnight Cemetery", "Foggy Graveyard", "Eerie", ["tombstone", "crypt", "undead", "fog", "skeletons", "cold", "spirits", "grave"]),
            ("Cursed Lighthouse", "Rocky Stormy Coast", "Chilling", ["lighthouse", "beacon", "drowned", "ocean", "shipwreck", "phantom", "storm"]),
            ("Asylum Whispers", "Abandoned Sanitarium", "Unsettling", ["asylum", "hollow", "footsteps", "echoes", "darkness", "madness", "chilling"]),
            ("Ancient Crypt", "Catacombs Beneath the City", "Claustrophobic", ["catacombs", "bones", "tunnels", "torches", "sealed", "mummy", "horror"]),
            ("The Mirror's Double", "Antique Dressing Room", "Sinister", ["reflection", "mirror", "doppelganger", "glass", "watcher", "creepy", "unnatural"]),
            ("The Forgotten Well", "Overgrown Village Square", "Haunting", ["well", "depths", "water", "chains", "echo", "darkness", "dread"])
        ],
        "openings": [
            "The autumn wind howled through the barren boughs of {setting}, carrying with it a chill that sank deep into bone.",
            "Nobody ventured near {setting} after twilight, for the old folk remembered the tragedy that had stained its soil decades ago.",
            "A suffocating blanket of midnight fog rolled across {setting}, swallowing every familiar landmark in impenetrable gray.",
            "The iron gates of {setting} stood half-open, groaning on rusted hinges as the midnight hour struck.",
            "Silence in {setting} was never peaceful; it was the tense stillness of a predator waiting in the blackness."
        ],
        "middles": [
            "As the solitary lantern sputtered and died, rhythmic scratching sounded from the interior walls. Pale, translucent fingers emerged from the darkness, gripping the cold stone. Shadows detached themselves from the floor, circling silently with hollow, sorrowful eyes that seemed to demand answers.",
            "A sudden plummet in temperature turned every breath into silver vapor. Soft, wet whispers echoed from empty corners, repeating forgotten names. The floorboards vibrated with heavy, deliberate footfalls descending from an empty staircase where no living soul could stand.",
            "From beneath the damp earth and broken masonry, an unearthly glow arose. Ancient runes carved into the threshold flared with spectral light as a towering shroud drifted forward, radiating centuries of unresolved grief and malice.",
            "The air grew thick with the scent of stagnant water and rotting flowers. An icy draft extinguished all torches at once, leaving only the sound of hurried, ragged breathing that did not belong to any human in the room."
        ],
        "endings": [
            "With a desperate surge of adrenaline, the sole survivor scrambled through the shattered gateway, leaving behind every lantern and notebook, swearing never to look back at {setting}.",
            "When morning light finally broke through the gray clouds, the search party discovered only an abandoned brass lantern on the moss, surrounded by dozens of barefoot tracks that abruptly vanished into thin air.",
            "The clock in the bell tower struck four, and as dawn crept over the horizon, the apparitions dissolved back into the mist, leaving the grim truth forever locked within {setting}.",
            "No one ever returned to investigate {setting} again, and to this day, locals cross the road when walking past its shadowed gates."
        ]
    },

    "Mystery": {
        "themes": [
            ("Stolen Diamond", "Gilded London Museum", "Intriguing", ["detective", "clues", "investigation", "jewel", "heist", "alibi", "vault"]),
            ("Cipher in the Manuscript", "Old University Library", "Enigmatic", ["cipher", "puzzle", "parchment", "scholar", "code", "secret", "archive"]),
            ("Midnight Express Murder", "Trans-Continental Train", "Suspenseful", ["train", "compartment", "suspects", "conductor", "mystery", "snowbound"]),
            ("Forged Masterpiece", "Paris Art Gallery", "Clever", ["forgery", "painting", "canvas", "magnifying glass", "signature", "museum"]),
            ("Missing Diplomat", "Foggy Thames Wharf", "Tense", ["docks", "wharf", "briefcase", "fog", "informant", "conspiracy", "detective"]),
            ("The Locked Study", "Country Manor Estate", "Perplexing", ["locked room", "keyhole", "will", "inheritance", "footprints", "clockwork"]),
            ("The Clockmaker's Will", "Swiss Clock Workshop", "Curious", ["gears", "pendulum", "secret drawer", "inheritance", "cogs", "riddle"]),
            ("Disappearance at Blackwood Hall", "Windswept Moors", "Atmospheric", ["moors", "manor", "guest list", "alibi", "rainstorm", "investigator"])
        ],
        "openings": [
            "Inspector Sterling adjusted his spectacles and knelt over the polished floor of {setting}, where every detail told a conflicting story.",
            "The heavy mahogany doors of {setting} had been locked from the inside, yet the velvet pedestal at the center stood completely bare.",
            "A discreet telegram summoned the renowned detective to {setting} on a stormy Tuesday morning when London was blanketed in yellow fog.",
            "Among all the puzzles cataloged in the annals of Scotland Yard, the incident at {setting} presented the most baffling contradictions.",
            "The storm had severed all telegraph lines connected to {setting}, leaving seven nervous guests locked together with a master thief."
        ],
        "middles": [
            "Examining the perimeter with a silver pocket loupe, Sterling noticed a microscopic streak of blue pigment near the floor molding. A faint scent of bitter almonds lingered near the fireplace, and the clock on the mantelpiece had stopped precisely seven minutes before the alarm sounded.",
            "Upon cross-referencing the guest registry against the train timetable, the investigator uncovered a glaring discrepancy: two distinct alibis relied on a pocket watch that had been deliberately advanced by half an hour.",
            "Tapping the walnut paneling behind the bookshelf revealed a hollow resonance. A hidden spring clicked open, unveiling a leather-bound journal filled with encoded nautical coordinates and duplicate wax seal impressions.",
            "The suspect claimed to have been inspecting the conservatory during the blackout, yet the damp soles of their leather boots were caked with red clay found exclusively beneath the cellar window."
        ],
        "endings": [
            "With calm precision, the detective laid out the incontrovertible chain of evidence before the assembled suspects, revealing the true mastermind before the local constabulary arrived.",
            "The missing treasure was retrieved from its ingenious hiding spot inside the grandfather clock pendulum, closing one of the most celebrated cases in modern investigative history.",
            "As the handcuffs clicked shut, the culprit offered a wry, grudging smile, acknowledging that a single forgotten drop of blue ink had undone their flawless scheme at {setting}.",
            "Justice was served quietly as dawn broke, the ledger returned to its vault, and the enigma of {setting} officially marked solved."
        ]
    },

    "Adventure": {
        "themes": [
            ("Lost Inca Temple", "Amazon Rainforest Canopy", "Exhilarating", ["expedition", "jungle", "temple", "ruins", "machete", "gold", "compass"]),
            ("Sunken Spanish Galleon", "Caribbean Coral Reef", "Daring", ["diving", "treasure", "shipwreck", "reef", "ocean", "doubloons", "waves"]),
            ("Himalayan Peak Ascent", "Snowbound Mountain Ridge", "Heroic", ["climbing", "summit", "ice axe", "blizzard", "crevasse", "altitude", "peak"]),
            ("Saharan Lost Oasis", "Great Sand Sea Dunes", "Gripping", ["desert", "caravan", "dunes", "oasis", "mirage", "sun", "ancient"]),
            ("Underground River Rapid", "Limestone Cavern Network", "Thrilling", ["cavern", "raft", "subterranean", "rapids", "stalactites", "waterfall"]),
            ("Forbidden Arctic Passage", "Glacial Ice Shelf", "Courageous", ["iceberg", "sled", "blizzard", "compass", "expedition", "frost", "pack ice"]),
            ("Volcanic Caldera Quest", "Smoldering Island Rim", "Perilous", ["volcano", "lava", "ash", "sulfur", "island", "relic", "canyon"]),
            ("Ancient Desert Tombs", "Valley of the Pharaohs", "Epic", ["tomb", "sandstorm", "hieroglyph", "scarab", "torchlight", "excavation"])
        ],
        "openings": [
            "With a weathered parchment map gripped in one hand and a brass compass in the other, the expedition pressed into {setting}.",
            "The morning sun rose like a ball of molten copper over {setting}, signaling the most dangerous leg of the journey.",
            "Three weeks of relentless trekking had brought the team to the precipice of {setting}, where few human boots had ever trodden.",
            "Thunder rolled across the vast expanse of {setting}, whipping the guidewires of the base camp tents into a frenzy.",
            "The ancient legends had always warned against exploring {setting}, but the promise of unearthing history outweighed every caution."
        ],
        "middles": [
            "Navigating treacherous chasms and sheer granite ledges, the climbers relied on sheer will and braided hemp rope. When an unexpected rockslide severed the secondary safety line, quick reflexes and seasoned teamwork saved the entire survey team from a fatal plunge into the gorge below.",
            "Hacking through tangled creepers and towering ferns, the explorers stumbled upon towering stone monoliths etched with celestial constellations. Deep within the moss-covered sanctuary, an intricate stone gear mechanism turned smoothly, revealing a vaulted chamber untouched for millennia.",
            "Braving the turbulent rapids, the wooden raft surged through roaring white water and narrow canyon corridors. Spray blinded the rowers as the guide steered deftly around jagged limestone boulders, shooting through the cavern mouth into a tranquil, sapphire lagoon.",
            "Battling shifting sands and blistering desert heat, the team uncovered the carved sandstone archway buried beneath centuries of dunes. As the heavy stone slab yielded to their crowbars, cool air rushed forth from the subterranean hall."
        ],
        "endings": [
            "Standing atop the summit as golden sunrise flooded {setting}, the weary adventurers hoisted their banner, knowing their names would forever be inscribed in expedition lore.",
            "The priceless cultural artifacts were carefully packed and cataloged for the national museum, ensuring the wonders of {setting} would inspire generations to come.",
            "With water supplies replenished and the map updated, the triumphant team began their return journey, carrying memories of an extraordinary triumph against the wild.",
            "Looking back one last time at {setting}, the explorers realized the true treasure was the unbreakable bond forged through danger and discovery."
        ]
    },

    "Romance": {
        "themes": [
            ("Serendipity in Paris", "Montmartre Cobblestone Alley", "Heartwarming", ["love", "romance", "cafe", "destiny", "paris", "serendipity", "art"]),
            ("Letters Across the Sea", "Coastal Harbor Boardwalk", "Poignant", ["letters", "penpal", "ocean", "lighthouse", "waiting", "heartfelt", "reunion"]),
            ("Waltz at Midnight", "Viennese Grand Ballroom", "Enchanting", ["waltz", "orchestra", "chandelier", "dance", "gown", "violin", "gaze"]),
            ("The Bookshop Encounter", "Old Bloomsbury Antiquarian", "Sweet", ["bookstore", "poetry", "rain", "coffee", "first glance", "shared smile"]),
            ("Summer in Tuscany", "Sunlit Olive Grove", "Romantic", ["vineyard", "sunset", "tuscany", "wine", "laughter", "golden hour", "summer"]),
            ("Winter Hearth Promise", "Snowed-In Alpine Cabin", "Cozy", ["fireplace", "snow", "cabin", "blanket", "whisper", "tea", "forever"]),
            ("Stargazing by the Lake", "Quiet Mountain Shore", "Tender", ["stars", "reflection", "lake", "constellations", "hand in hand", "gentle"]),
            ("The Florist's Secret", "Covent Garden Flower Stall", "Charming", ["roses", "bouquets", "spring", "secret admirer", "ribbon", "blossom"])
        ],
        "openings": [
            "Rain tapped gently against the cafe windows overlooking {setting}, blurring the amber streetlights into soft watercolor halos.",
            "It was the kind of crisp, unforgettable autumn afternoon in {setting} where chance encounters feel destined by the stars.",
            "Among the bustling crowds of {setting}, their eyes met across the room, and the frantic noise of the city seemed to fade into silence.",
            "Years had passed since they last walked the familiar pathways of {setting}, yet every stone and archway still remembered their shared laughter.",
            "The sweet aroma of jasmine and fresh rain lingered in {setting}, creating an atmosphere ripe for unexpected beginnings."
        ],
        "middles": [
            "Sharing an umbrella beneath the sudden downpour, they spoke for hours about forgotten dreams, favorite verses of poetry, and childhood memories. Every shared glance carried an electric warmth that made the chill evening air feel like midsummer.",
            "As the orchestra swelled into a breathtaking waltz, he offered his hand with a gentle, questioning smile. Sweeping across the polished parquet floor beneath glistening crystal chandeliers, the rhythm of the music mirrored the steady, joyful beating of their hearts.",
            "Finding the same rare edition of sonnets tucked on a high shelf, their fingers brushed against the leather spine. What began as an apology blossomed into an effortless conversation over steaming porcelain cups of tea that lasted until closing time.",
            "Walking along the lantern-lit waterfront as waves lapped softly against the wooden pilings, he reached out and gently intertwined his fingers with hers. Words became unnecessary as the silent understanding between them filled the evening."
        ],
        "endings": [
            "Underneath the starlit canopy of {setting}, they promised that no matter what storms life brought, their hearts had finally found their permanent home.",
            "With a lingering smile and a promise for tomorrow, they walked together into the glowing night, their story just beginning.",
            "As the morning sun kissed the rooftops of {setting}, they knew that what started as a chance meeting had turned into a lifetime of love.",
            "Hand in hand, they stepped into the future together, leaving behind the memories of solitude forever."
        ]
    },

    "Comedy": {
        "themes": [
            ("The Great Pancake Catastrophe", "Sunday Morning Kitchen", "Hilarious", ["pancakes", "flour", "cooking", "cat", "mishap", "funny", "breakfast"]),
            ("The Mayor's runaway Parrot", "Town Hall Garden Party", "Witty", ["parrot", "speech", "chaos", "feathers", "funny", "chase", "garden"]),
            ("The Clumsy Magician", "Village Carnival Stage", "Amusing", ["magician", "rabbit", "hat", "tricks", "confetti", "stage", "laughter"]),
            ("The Accidental Invention", "Basement Workshop", "Silly", ["invention", "gadget", "smoke", "gears", "bubble", "whimsical", "funny"]),
            ("The Dog Walker's Dilemma", "Busy City Park", "Playful", ["dogs", "leash", "tangle", "park", "squirrel", "funny", "chaos"]),
            ("The Royal Baker's Blunder", "Palace Pastry Kitchen", "Charming", ["cake", "frosting", "slippery", "duke", "chef", "laughter", "icing"]),
            ("The Theater Audition Fiasco", "Broadway Rehearsal Hall", "Witty", ["audition", "costume", "lines", "stage", "slip", "director", "funny"]),
            ("The Over-Engineered Garden Gnome", "Suburban Lawn Championship", "Hilarious", ["gnome", "lawn", "contest", "neighbor", "sprinkler", "mishap"])
        ],
        "openings": [
            "According to the instruction manual, nothing could possibly go wrong in {setting}—which was naturally the first red flag.",
            "It began on a tranquil Saturday morning in {setting} before the laws of physics took a brief, comical vacation.",
            "Professor Barnaby firmly believed that his new demonstration in {setting} would win him the Nobel Prize, rather than a visit from the fire brigade.",
            "The town gossip had already predicted chaos in {setting}, but even she under-estimated the impending pandemonium by half.",
            "If anyone had asked Arthur why he was standing in {setting} dressed in a velvet cape, he would have blamed his overly enthusiastic pet."
        ],
        "middles": [
            "With a thunderous POP, the batter dispenser ricocheted off the toaster, propelling a golden projectile across the ceiling. The family cat leaped in acrobatic pursuit, knocking over the flour canister and transforming the entire room into a winter wonderland of powdered sugar.",
            "The parrot seized the mayor's reading glasses mid-sentence, swooping over the champagne fountain while reciting the secret recipe for Aunt Clara's rhubarb pie. Distinguished guests dove behind hydrangeas as pastry trays clattered to the grass.",
            "Attempting to pull a white rabbit from the silk top hat, the magician instead produced three surprised pigeons, two linked sausages, and the mayor's missing wallet. The audience erupted into roaring applause, assuming the confusion was brilliant theatrical slapstick.",
            "The self-propelling lawnmower gained unexpected sentience, gracefully trimming the neighbor's prized hedges into the exact likeness of a dancing poodle while spraying colorful sprinkler jets in synchronized rhythm."
        ],
        "endings": [
            "Covered in frosting and breathless with uncontrollable laughter, everyone agreed that the afternoon at {setting} was the best party the town had ever seen.",
            "The demonstration was universally declared an accidental masterpiece, earning a standing ovation and three awards for comedic ingenuity.",
            "Wiping tears of laughter from their eyes, the neighbors shared cups of cider and voted to make the chaotic event an annual tradition.",
            "As the smoke cleared and the rogue parrot finally landed on the podium, Arthur took a graceful bow to thunderous cheers."
        ]
    },

    "Fantasy": {
        "themes": [
            ("The Starlight Dragon", "Crystal Mountain Citadel", "Epic", ["dragon", "magic", "crystal", "stars", "wizard", "spell", "enchanted"]),
            ("The Moonstone Blade", "Elven Forest Sanctuary", "Mystical", ["elven", "sword", "moonstone", "magic", "grove", "blade", "runes"]),
            ("The Alchemist's Portal", "Tower of Ancient Secrets", "Wondrous", ["portal", "alchemy", "scroll", "potions", "dimension", "spark", "magic"]),
            ("The Phoenix Feather Quest", "Volcanic Ash Peak", "Heroic", ["phoenix", "fire", "feather", "quest", "flame", "mythical", "destiny"]),
            ("The Whispering Grimoire", "Grand Arcane Archive", "Enchanting", ["grimoire", "spells", "archive", "runes", "apprentice", "staff", "magic"]),
            ("The Enchanted Clockwork Golem", "Dwarven Under-City Forge", "Epic", ["golem", "dwarven", "forge", "runestones", "hammer", "cogs", "magic"]),
            ("The Siren's Pearl", "Sunken Coral Palace", "Mysterious", ["siren", "ocean", "pearl", "underwater", "tides", "crown", "myth"]),
            ("The Celestial Weaver", "Cloud Spire Observatorium", "Sublime", ["clouds", "celestial", "loom", "tapestry", "starlight", "goddess", "cosmos"])
        ],
        "openings": [
            "High above the mortal world, among the shimmering towers of {setting}, ancient runes pulsed with luminescent violet energy.",
            "Legends spoke of the celestial epoch when the archmages first wove the fabric of time within the sanctuary of {setting}.",
            "A shimmering veil of stardust drifted across {setting}, heralding the awakening of powers dormant for a thousand winters.",
            "The young apprentice stood before the towering obsidian gateway of {setting}, clutching an iron key etched with elemental sigils.",
            "Deep in the heart of {setting}, where starlight never faded, the sacred flame burned with a steady emerald glow."
        ],
        "middles": [
            "Chanting the ancient incantation inscribed on the parchment, the mage raised the crystal staff. Beams of iridescent light converged on the monolith, dissolving the barrier between worlds. Winged celestial beasts leaped from the astral rift, circling the chamber with majestic grace.",
            "The forged blade hummed with radiant moonlight, illuminating the ancient dwarven carvings along the cavern walls. As the guardian dragon unfurled its translucent wings of sapphire scales, it lowered its mighty head in solemn recognition of the true heir.",
            "Vials of shimmering essence bubbled inside the brass alembics, releasing fragrant vapors of ambergris and starlight. With a soft resonance like silver bells, the golden grimoire floated into the air, its pages turning to reveal the forgotten ritual of renewal.",
            "Weaving threads of pure moonlight upon the astral loom, the sorceress repaired the shattered constellation. Across the sky, stars ignited one by one in brilliant harmony, showering the realm with blessings of peace and bountiful harvests."
        ],
        "endings": [
            "With the realm saved and the balance of magic restored, the heroes looked down from {setting} onto a world bathed in renewed wonder.",
            "The legendary artifact was placed upon its ancestral pedestal in {setting}, where its light would protect the kingdom for centuries to come.",
            "The celestial portal closed gently, leaving behind a tranquil night sky and a legacy of courage etched into the stars.",
            "And so the song of {setting} was sung by elven bards in every hall, keeping the eternal memory of the magical quest alive."
        ]
    },

    "Sci-Fi": {
        "themes": [
            ("Titan Orbital Station", "Titan Ring Orbit", "Atmospheric", ["space", "station", "orbit", "titan", "astronaut", "future", "galaxy"]),
            ("The Quantum Relay", "Deep Space Colony Ship", "Intriguing", ["quantum", "ai", "spaceship", "colony", "warp", "stars", "crew"]),
            ("The Cybernetic Archive", "Neo-Tokyo Megacity Tower", "Futuristic", ["cyber", "neon", "data", "android", "neural", "hacker", "future"]),
            ("First Contact on Europa", "Sub-Surface Ice Ocean", "Wonder", ["alien", "europa", "ocean", "ice", "submarine", "signal", "discovery"]),
            ("The Chrono Singularity", "Temporal Physics Institute", "Mind-Bending", ["time travel", "singularity", "timeline", "paradox", "quantum", "chrono"]),
            ("The Red Planet Terraformer", "Martian Valley Biosphere", "Inspiring", ["mars", "terraforming", "dome", "atmosphere", "colonists", "red dust"]),
            ("The Derelict Dyson Ring", "Ancient Solar Star Base", "Epic", ["dyson sphere", "star", "solar", "derelict", "alien tech", "probe"]),
            ("The Synthetic Mind", "Artificial Intelligence Core", "Thought-Provoking", ["ai", "consciousness", "core", "code", "sentience", "future", "network"])
        ],
        "openings": [
            "The telemetry display inside the control bridge of {setting} flashed steady amber as the automated docking sequence initiated.",
            "Beyond the reinforced titanium viewport of {setting}, the gas giant rotated silently against a backdrop of ten thousand unblinking stars.",
            "The year was 2184, and the research team stationed at {setting} had just intercepted an artificial transmission from the galactic core.",
            "Deep inside the pressurized habitat of {setting}, the environmental scrubber hummed its steady, reassuring rhythm.",
            "Zero-gravity maintenance in {setting} was second nature to Dr. Vance, until the external sensors detected a gravimetric anomaly."
        ],
        "middles": [
            "Analyzing the spectral frequency of the incoming pulse, the quantum computer decrypted an intricate geometric code containing complete blueprints for clean fusion energy. The crew gathered around the holographic emitter in stunned silence as the alien message translated into universal mathematical constants.",
            "Thrusters fired with precision bursts, maneuvering the research probe into the subterranean ice trench. Spotlights pierced the pitch-black ocean, revealing bioluminescent organisms weaving in synchronized formations around a towering hydrothermal spire.",
            "Rerouting the neural matrix through auxiliary cryogenic cooling channels, the engineer stabilized the core before catastrophic cascade. As the data streams realigned, the synthetic intelligence uttered its first original query: 'What is the purpose of dreaming?'",
            "The terraforming atmospheric scrubbers roared to life, releasing pure oxygen into the domed valley. Outside the transparent geodesic dome, the red Martian soil yielded its first resilient green sprout beneath the gentle glow of artificial sunlight."
        ],
        "endings": [
            "As the communications relay transmitted the historic discovery back to Earth from {setting}, the crew toasted to the dawn of a new interstellar era.",
            "Looking out across the infinite expanse of the cosmos, the explorers realized humanity was never truly alone in the vast cosmic tapestry.",
            "The propulsion drives hummed smoothly, propelling the starship toward the distant coordinates of humanity's new planetary home.",
            "Safe within the orbit of {setting}, the archives preserved the knowledge that would guide interstellar civilization for millennia."
        ]
    },

    "Thriller": {
        "themes": [
            ("The Blackwood Conspiracy", "Embassy Ballroom Reception", "Tense", ["conspiracy", "agent", "spy", "danger", "briefcase", "escape", "chase"]),
            ("Midnight Freight Escape", "Industrial Freight Rail Yard", "Gripping", ["chase", "train", "tracks", "shadows", "pursuit", "danger", "night"]),
            ("The Cipher Decryption", "Underground Bunker Complex", "Intense", ["countdown", "code", "bomb", "defuse", "bunker", "wire", "suspense"]),
            ("Rogue Operative", "Berlin Metro Station", "Fast-Paced", ["metro", "subway", "operative", "surveillance", "trench coat", "chase"]),
            ("Hostage at Timberline", "Alpine Summit Cable Car", "High-Stakes", ["cable car", "hostage", "blizzard", "heights", "rescue", "peril"]),
            ("The Double Agent's Drop", "Rainy Port Warehouse", "Suspenseful", ["informant", "docks", "rain", "microfilm", "betrayal", "covert"]),
            ("The Cyber Infiltration", "Financial District Headquarters", "Nail-Biting", ["firewall", "heist", "alarm", "security", "countdown", "stealth"]),
            ("The Highway Pursuit", "Mountain Pass Highway", "Adrenaline", ["car chase", "curves", "headlights", "cliffside", "speed", "danger"])
        ],
        "openings": [
            "Agent Cross checked his watch: 02:47. He had exactly three minutes before the perimeter security swept {setting}.",
            "Rain lashed against the windows of {setting}, masking the sound of muffled footsteps on the gravel path outside.",
            "The encrypted dossier in his jacket pocket was the only thing standing between peace and total catastrophe in {setting}.",
            "Sirens wailed in the distance, echoing off the cold concrete walls of {setting} as the countdown timer reached forty seconds.",
            "Under the flickering fluorescent lights of {setting}, every shadow seemed to conceal an assassin waiting for the order."
        ],
        "middles": [
            "Slipping through the laser grid with practiced acrobatic precision, Cross inserted the flash drive into the terminal. Data bars surged to ninety-nine percent just as heavy boots kicked open the reinforced security door. Diving behind the server rack, he deployed a smoke canister that filled the corridor with blinding white fog.",
            "The cable car swayed violently in the freezing mountain gale, dangling thousands of feet above the jagged ravine. With nerves of steel, the rescue specialist climbed onto the icy roof, bypassed the electronic override, and secured the emergency brake moments before impact.",
            "Hands steady despite the racing pulse, the operative clipped the blue detonation wire with two seconds remaining on the digital display. The deafening hum of the device died down to a faint click, saving the entire precinct.",
            "Weaving through narrow alleys and crowded train platforms, the operative blended seamlessly into the commuter crowd, swapping coats and slipping past the surveillance cameras undetected."
        ],
        "endings": [
            "As the extraction helicopter touched down on the roof above {setting}, Cross handed over the recovered intelligence, knowing the crisis was averted.",
            "Disappearing into the rainy midnight streets, the operative left no trace behind, another mission completed in the shadows of {setting}.",
            "With the hostages safe and the conspiracy dismantled, the morning sun rose over {setting} on a city that would never know how close it came to disaster.",
            "Justice was delivered swiftly, the classified files secured, and peace restored across the continent."
        ]
    },

    "Friendship": {
        "themes": [
            ("The Treehouse Pact", "Summer Oak Treehouse", "Heartwarming", ["friends", "treehouse", "summer", "loyalty", "pact", "childhood", "trust"]),
            ("Unlikely Allies", "Sunny Farm Meadow", "Sweet", ["dog", "cat", "animals", "unlikely friends", "companions", "meadow", "bond"]),
            ("The Old Sailor's Companion", "Harbor Fisherman's Shack", "Tender", ["fisherman", "seagull", "harbor", "loyalty", "trust", "companionship"]),
            ("The Study Buddies", "College Library Alcove", "Uplifting", ["classmates", "exams", "study", "encouragement", "friendship", "success"]),
            ("The Shared Workshop", "Community Woodworking Shop", "Inspiring", ["craft", "woodworking", "mentorship", "patience", "friendship", "shared project"]),
            ("The Road Trip Trio", "Vintage Convertible Highway", "Joyful", ["road trip", "music", "highway", "laughter", "memories", "adventure"]),
            ("The Mountain Rescue", "Rocky Hiking Trail", "Loyal", ["hiking", "trail", "rescue", "help", "support", "trust", "brotherhood"]),
            ("The Neighborhood Garden", "Urban Community Patch", "Warm", ["garden", "flowers", "neighbors", "community", "sharing", "friendship"])
        ],
        "openings": [
            "Sunlight filtered through the golden oak leaves of {setting}, warming the weathered wooden floor where two best friends sat.",
            "True friendship isn't measured in words, but in the quiet moments shared together in places like {setting}.",
            "For ten glorious summers, the wooden boards of {setting} had served as the headquarters for their grandest adventures.",
            "When times were tough and hope seemed distant, the comforting companionship found in {setting} made every burden lighter.",
            "No matter how far life took them, the promise they carved into the cedar beam at {setting} remained unbreakable."
        ],
        "middles": [
            "Working shoulder to shoulder from morning until dusk, they nailed together the final boards of the lookout deck. When Leo lost his balance on the ladder, Maya's steady grip pulled him back to safety without a second's hesitation, their shared laughter echoing through the trees.",
            "Sharing a crust of warm sourdough bread and a thermos of hot cocoa, the old fisherman and the injured tern sat peacefully on the pier. Day after day, patient care nurtured the broken wing until the bird could soar freely once more, always returning to rest gently on its friend's shoulder.",
            "When the mathematics exam results were posted, tears of joy replaced weeks of anxiety. They had spent countless late nights quizzing each other, refusing to let either one fall behind, proving that mutual encouragement triumphs over every obstacle.",
            "Navigating the winding coastal highway with the radio playing their favorite anthems, they realized that the destination didn't matter half as much as the shared joy of traveling together with lifelong friends."
        ],
        "endings": [
            "Looking out over the sunset from {setting}, they placed their hands together in the center, knowing their bond would endure through every chapter of life.",
            "Years later, returning to {setting}, they found the carved initials still clear and deep on the wood, a testament to a friendship that never faded.",
            "With hearts full of gratitude and pockets full of shared memories, the friends walked home under the evening stars.",
            "In a world that is always changing, the sanctuary of {setting} proved that genuine friendship is the greatest gift of all."
        ]
    },

    "Emotional": {
        "themes": [
            ("The Grandfather's Violin", "Dusty Attic Music Box", "Bittersweet", ["violin", "music", "grandfather", "memory", "tears", "family", "heartfelt"]),
            ("The Forgotten Garden", "Cottage Garden Bench", "Poignant", ["garden", "flowers", "memory", "mother", "seasons", "grief", "remembrance"]),
            ("Letters to Tomorrow", "Antique Writing Desk", "Deep", ["letters", "legacy", "father", "son", "advice", "love", "touching"]),
            ("The Old Photograph Album", "Living Room Fireside", "Nostalgic", ["photo album", "sepia", "ancestors", "laughter", "passing time", "generations"]),
            ("The Lighthouse Keeper's Watch", "Lonely Sea Cliff", "Melancholic", ["lighthouse", "watch", "sea", "waiting", "solitude", "devotion", "honor"]),
            ("The Last Harvest", "Autumn Wheat Field", "Bittersweet", ["harvest", "farm", "father", "land", "hard work", "passing the torch", "pride"]),
            ("The Homecoming", "Rainy Train Platform", "Overwhelming", ["reunion", "train", "embrace", "welcome", "tears of joy", "family", "home"]),
            ("The Painter's Final Canvas", "Sunlit Studio Easel", "Profound", ["artist", "painting", "legacy", "beauty", "final work", "gratitude", "colors"])
        ],
        "openings": [
            "A delicate layer of dust rested upon the velvet case in {setting}, preserving a song that hadn't been heard in thirty years.",
            "Memories have a way of lingering in the quiet corners of {setting}, waiting for a gentle touch to awaken them.",
            "Sitting alone by the window in {setting}, Nora held the worn envelope with hands that trembled with quiet reverence.",
            "The twilight hour always brought a poignant hush over {setting}, when the boundaries between past and present seemed to blur.",
            "Every crease in the sepia photograph told a story of sacrifice, devotion, and boundless love in {setting}."
        ],
        "middles": [
            "Lifting the polished spruce violin to his shoulder, Julian drew the horsehair bow across the strings. The resonant melody of his grandfather's favorite lullaby filled the sunlit room, vibrant with memories of childhood summers, warm hugs, and wise guidance that transcended time itself.",
            "Raking back the fallen leaves from the stone path, she uncovered the miniature rosebush her mother had planted decades ago. Defying the harsh winter frost, a single pink bud had opened, offering its sweet fragrance like a whisper of love from beyond.",
            "Reading the handwritten pages penned in his father's steady script, tears rolled down his cheeks. Every line was filled with encouragement, forgiveness, and unconditional pride, answering the questions he had carried in his heart for half a lifetime.",
            "Stepping off the train into the misty evening air, he saw his family waiting under the station lamps. The instant their arms wrapped around him in a tight embrace, all the weariness of the long journey dissolved into pure, restorative tears of joy."
        ],
        "endings": [
            "As the final musical note faded into the peaceful stillness of {setting}, a serene smile touched his lips, knowing love never truly ends.",
            "Placing the dried rose between the pages of the family Bible, she felt an overwhelming sense of peace settle over her soul.",
            "Holding the letter close to his chest, he looked up at the stars above {setting}, filled with strength for the days ahead.",
            "Surrounded by the warmth of family in {setting}, he finally understood that home is not a place, but the people who love you unconditionally."
        ]
    },

    "Moral": {
        "themes": [
            ("The Honest Woodcutter", "Forest Stream Bank", "Inspiring", ["woodcutter", "honesty", "axe", "gold", "truth", "reward", "water"]),
            ("The Greedy Merchant's Gold", "Bustling Marketplace", "Wise", ["merchant", "greed", "gold", "lesson", "generosity", "karma", "market"]),
            ("The Crow and the Pitcher", "Dry Country Road", "Clever", ["crow", "pitcher", "pebbles", "patience", "wisdom", "water", "thirst"]),
            ("The Pride of the Mountain Oak", "Windy Mountain Crest", "Thoughtful", ["oak", "reed", "wind", "humility", "pride", "storm", "strength"]),
            ("The Two Travelers and the Bear", "Deep Woodland Trail", "Insightful", ["travelers", "bear", "loyalty", "danger", "promise", "fable", "friendship"]),
            ("The Golden Touch", "King's Palace Banquet", "Cautionary", ["king", "gold", "greed", "touch", "daughter", "fable", "regret", "wisdom"]),
            ("The Bundle of Sticks", "Elder's Village Hearth", "Unifying", ["sticks", "unity", "brothers", "strength", "family", "cooperation", "lesson"]),
            ("The Blind Men and the Elephant", "Shady Banyan Tree", "Philosophical", ["elephant", "perspective", "wisdom", "truth", "blind men", "understanding"])
        ],
        "openings": [
            "In ancient times, when beasts and trees spoke the language of wisdom, a traveler walked the path near {setting}.",
            "A timeless fable from the village elders of {setting} teaches a lesson that every generation must learn anew.",
            "There once lived a man in {setting} who believed that wealth alone could measure the true value of a person.",
            "The wise teacher gathered the village children beneath the shade of {setting} to share an unforgettable tale of truth.",
            "Pride and humility met on the rocky slopes of {setting} to test which virtue would withstand the coming tempest."
        ],
        "middles": [
            "When the golden axe rose from the river, the humble woodcutter shook his head and spoke honestly: 'That is not mine; my axe was simple forged iron.' Pleased by such incorruptible integrity, the spirit of the waters gifted him both the gold and silver axes alongside his own.",
            "Dropping pebbles one by one into the tall pitcher with tireless persistence, the thirsty crow watched the water level rise steadily until its beak could drink freely, proving that patience and ingenuity conquer brute force every time.",
            "The mighty oak boasted of its rigid unbending strength, while the slender reed bowed low before the storm. When the hurricane passed, the proud oak lay uprooted on the ground, while the humble reed stood graceful and unblemished in the morning sun.",
            "Handing a single stick to his sons, the father watched them break it easily. But when he bound twelve sticks into a single bundle, not even the strongest warrior could bend it, proving that united we stand invincible, but divided we easily fall."
        ],
        "endings": [
            "The lesson learned at {setting} echoed through the village, reminding all that integrity is the highest currency of human character.",
            "Content with an honest life and a clean conscience, the family lived in peace, blessed by the enduring wisdom of {setting}.",
            "To this day, travelers passing {setting} remember the timeless proverb: true strength lies in humility, unity, and honesty.",
            "And so the simple truth of {setting} was carved into stone, guiding future generations toward wisdom and virtue."
        ]
    },

    "Children's Stories": {
        "themes": [
            ("Barnaby the Helpful Bear", "Sunny Berry Meadow", "Playful", ["bear", "berries", "forest animals", "sharing", "cute", "children", "whimsical"]),
            ("The Magic Paintbrush", "Rainbow Village School", "Wondrous", ["paintbrush", "colors", "magic", "art", "children", "dragon", "creativity"]),
            ("Pippin's Lost Acorn", "Ancient Hollow Tree", "Cute", ["squirrel", "acorn", "friends", "forest", "cute", "adventure", "animals"]),
            ("The Little Cloud That Could", "Sunny Blue Sky", "Uplifting", ["cloud", "rain", "rainbow", "flowers", "gentle", "happy", "children"]),
            ("The Starfish Wish", "Tide Pool Cove", "Charming", ["starfish", "ocean", "shell", "wish", "waves", "sea creatures", "magic"]),
            ("The Friendly Garden Snail", "Vegetable Garden Patch", "Delightful", ["snail", "lettuce", "race", "garden", "friends", "cute", "patience"]),
            ("The Curious Kitten's Adventure", "Sunny Farmyard Barn", "Sweet", ["kitten", "yarn", "butterflies", "barnyard", "milk", "cute", "playful"]),
            ("The Sleepy Little Hedgehog", "Mossy Forest Glen", "Gentle", ["hedgehog", "leaves", "autumn", "sleepy", "berries", "cute", "snuggle"])
        ],
        "openings": [
            "Once upon a sunny morning in {setting}, a fluffy little creature woke up with an enormous smile on its face.",
            "Deep in the cheerful woods of {setting}, all the forest animals were gathering for a very special celebration.",
            "If you look closely between the clover blossoms of {setting}, you might just spot a tiny friend on a grand adventure.",
            "High up in the bright blue sky above {setting}, little fluffy clouds danced and played games of tag.",
            "There was once a cheerful little adventurer in {setting} who loved nothing more than helping his friends."
        ],
        "middles": [
            "Barnaby dipped his wooden bucket into the bramble bush, gathering sweet blueberries for everyone. When little Oliver rabbit dropped his basket, Barnaby shared his berries with a joyful laugh, showing that sharing treats makes them taste twice as sweet!",
            "With a swish of the magic paintbrush, vibrant swirls of yellow, turquoise, and magenta sprang from the canvas. The painted dragon blinked its friendly eyes, puffed a tiny bubble of rainbow steam, and hopped out to play hide-and-seek with the laughing children.",
            "Rolling the shiny golden acorn up the mossy slope, Pippin asked his friend Benny Beaver for a helping paw. Together, they planted it deep in the rich soil, dancing with glee as a tiny green oak sprout popped up to say hello!",
            "Gathering all its strength, the tiny cloud puffed its cheeks and sent down a gentle shower of sparkling raindrops. Instantly, all the drooping daisies and buttercups perked up their petals, waving in joyful gratitude beneath a glowing rainbow."
        ],
        "endings": [
            "All the happy forest animals clapped their paws and sang together, grateful for another wonderful, magical day in {setting}.",
            "Tucked into bed with full tummies and happy hearts, the little friends closed their eyes and dreamed sweet, colorful dreams.",
            "With high-fives and cheerful giggles, they promised to meet again tomorrow for another brand-new adventure in {setting}.",
            "And from that day on, the warm sunshine and gentle giggles of {setting} made every creature smile with pure delight."
        ]
    },

    "Bedtime Stories": {
        "themes": [
            ("The Moonlit Lullaby", "Quiet Starry Sky", "Calm", ["sleep", "moon", "lullaby", "stars", "soothing", "peaceful", "night", "dreams"]),
            ("The Slumbering Mountain", "Misty Blue Ridge", "Peaceful", ["mountain", "mist", "forest", "gentle", "calm", "blanket", "slumber"]),
            ("The Pillow Cloud Kingdom", "Dreamland Cloud Castles", "Soothing", ["clouds", "pillow", "dreams", "soft", "feather", "gentle", "night"]),
            ("The Whispering Waves", "Moonlit Sandy Shore", "Relaxing", ["ocean", "waves", "sand", "moonlight", "tide", "calm", "sleepy"]),
            ("The Cozy Woodland Burrow", "Warm Mossy Tree Hollow", "Snug", ["burrow", "blanket", "warmth", "leaves", "cozy", "firefly", "sleep"]),
            ("The Secret Garden of Dreams", "Silver Moon Garden", "Serene", ["garden", "silver flowers", "nightingales", "lullaby", "dewdrops", "peace"]),
            ("The Starlight Carousel", "Quiet Celestial Sky", "Enchanting", ["starlight", "carousel", "constellations", "gentle", "dreamland", "peaceful"]),
            ("The Goodnight Forest", "Velvet Pine Woods", "Tranquil", ["pines", "owl", "crickets", "twilight", "goodnight", "stars", "slumber"])
        ],
        "openings": [
            "As twilight softly descends upon {setting}, the busy world slows down and prepares for sweet, peaceful slumber.",
            "The silvery moon rises high above {setting}, casting a gentle, soothing glow over the quiet hills and valleys.",
            "Listen closely to the gentle whisper of the evening breeze as it drifts through {setting}, singing a peaceful bedtime song.",
            "Stars ignite like tiny silver nightlights across the velvet sky above {setting}, watching over everyone as they sleep.",
            "A warm, cozy hush settles across {setting}, wrapping every sleepy creature in a soft blanket of rest."
        ],
        "middles": [
            "One by one, the little woodland animals curl up in their warm burrows lined with soft moss and dry leaves. The mother deer nudges her fawn close, while the little owls tuck their wings and listen to the soft, rhythmic hum of crickets in the grass.",
            "The gentle ocean waves roll onto the shore in a slow, hypnotic rhythm—hushhh... hushhh... washing away all the day's excitement and leaving behind calm, cool sand beneath the watchful smile of the silver moon.",
            "Drifting gently on a soft cloud made of spun cotton candy, the dream ship sails across the constellation river. Sparkling stardust sprinkles softly upon the earth, bringing peaceful thoughts and happy dreams to every sleeping child.",
            "The silver nightingale sings its gentle melody from the high willow branch. The petals of the moonflowers slowly fold in peace, and the cool night air carries the scent of lavender through open bedroom windows."
        ],
        "endings": [
            "Close your eyes, breathe in deep and slow, and drift off into the sweetest dreams in the peaceful wonderland of {setting}. Goodnight.",
            "All is calm, all is bright, and under the loving guard of the stars above {setting}, you are safe and warm. Sleep tight.",
            "The night wraps the world in tranquil comfort, promising a bright and joyful tomorrow. Sweet dreams in {setting}.",
            "And as the soft silver moonlight whispers goodnight, peaceful slumber carries you away until morning light. Rest well."
        ]
    }
}


def generate_large_story_dataset(target_count_per_genre=40):
    """
    Generates a rich, high-quality story collection of 520+ stories
    (40 distinct stories per genre * 13 genres = 520 stories).
    """
    all_stories = []
    story_id_counter = 1

    print(f"[*] Generating {target_count_per_genre} distinct stories across 13 genres (Total: {target_count_per_genre * 13})...")

    # Titles vocabulary by genre to ensure rich variety
    TITLE_PATTERNS = {
        "Horror": [
            "The Whispers of {spec}", "The Curse of {spec}", "Shadows Over {spec}", "The Phantom of {spec}",
            "The Haunting of {spec}", "Midnight in {spec}", "The Specter of {spec}", "The Secrets of {spec}",
            "The Eerie Tale of {spec}", "The Dark Echoes of {spec}"
        ],
        "Mystery": [
            "The Case of the {spec}", "The Enigma of {spec}", "The Secret of {spec}", "The Mystery of {spec}",
            "The Missing {spec}", "The Cipher of {spec}", "The Investigation at {spec}", "The Clue of the {spec}",
            "The Disappearance at {spec}", "The Heist at {spec}"
        ],
        "Adventure": [
            "The Quest for {spec}", "Voyage to {spec}", "Expedition: {spec}", "The Lost Relic of {spec}",
            "Ascent of {spec}", "Peril at {spec}", "The Trail Through {spec}", "Chronicles of {spec}",
            "Into the Heart of {spec}", "The Discovery of {spec}"
        ],
        "Romance": [
            "A Sunset in {spec}", "Letters from {spec}", "The Melody of {spec}", "Serendipity at {spec}",
            "A Promise in {spec}", "The Waltz of {spec}", "Midnight in {spec}", "Echoes of Love in {spec}",
            "Under the Stars of {spec}", "A Heart in {spec}"
        ],
        "Comedy": [
            "The Great {spec} Mishap", "Chaos at {spec}", "The Accidental {spec}", "Pandemonium in {spec}",
            "The Hilarious Tale of {spec}", "The Catastrophe at {spec}", "A Funny Thing in {spec}",
            "The Case of the Flying {spec}", "The Misadventures at {spec}", "The Bumbling {spec}"
        ],
        "Fantasy": [
            "The Legend of the {spec}", "The Blade of {spec}", "Chronicles of the {spec}", "The Spell of {spec}",
            "The Dragon of {spec}", "The Secret Realm of {spec}", "The Alchemist of {spec}", "The Star of {spec}",
            "The Citadel of {spec}", "The Enchantment of {spec}"
        ],
        "Sci-Fi": [
            "Signals from {spec}", "The Orbit of {spec}", "Mission to {spec}", "The Quantum {spec}",
            "Echoes of {spec}", "The Artificial {spec}", "Voyage to {spec}", "The Horizon of {spec}",
            "The Chronicles of {spec}", "Beyond {spec}"
        ],
        "Thriller": [
            "The Protocol of {spec}", "Escape from {spec}", "The Conspiracy at {spec}", "Countdown in {spec}",
            "The Operative of {spec}", "Showdown at {spec}", "The Infiltration of {spec}", "Target: {spec}",
            "The Pursuit of {spec}", "The Code of {spec}"
        ],
        "Friendship": [
            "The Bond of {spec}", "Companions of {spec}", "The Shared {spec}", "The Summer of {spec}",
            "The Pact at {spec}", "Allies in {spec}", "The Journey of {spec}", "The Secret of {spec}",
            "The Friends of {spec}", "The Promise at {spec}"
        ],
        "Emotional": [
            "The Memory of {spec}", "The Echoes of {spec}", "The Legacy of {spec}", "A Letter from {spec}",
            "The Melody in {spec}", "The Harvest of {spec}", "The Return to {spec}", "Tears in {spec}",
            "The Keeper of {spec}", "The Portrait of {spec}"
        ],
        "Moral": [
            "The Wisdom of {spec}", "The Fable of {spec}", "The Honest {spec}", "The Lesson of {spec}",
            "The Tale of {spec}", "The Truth in {spec}", "The Choice at {spec}", "The Parable of {spec}",
            "The Test of {spec}", "The Heritage of {spec}"
        ],
        "Children's Stories": [
            "The Adventures of {spec}", "The Magical {spec}", "The Little {spec}", "The Day of the {spec}",
            "The Story of {spec}", "The Curious {spec}", "The Friendly {spec}", "Fun in {spec}",
            "The Secret of {spec}", "The Happy {spec}"
        ],
        "Bedtime Stories": [
            "The Gentle {spec}", "Goodnight to {spec}", "The Lullaby of {spec}", "The Sleepy {spec}",
            "A Dream in {spec}", "The Moonlit {spec}", "The Peaceful {spec}", "The Night in {spec}",
            "The Cozy {spec}", "The Starlit {spec}"
        ]
    }

    for genre, data in GENRE_SPECS.items():
        theme_list = data["themes"]
        openings = data["openings"]
        middles = data["middles"]
        endings = data["endings"]
        title_patterns = TITLE_PATTERNS.get(genre, ["The Tale of {spec}"])

        for i in range(target_count_per_genre):
            theme_info = theme_list[i % len(theme_list)]
            theme_name, setting_name, mood_name, keywords_list = theme_info

            # Build distinct title
            title_pat = title_patterns[i % len(title_patterns)]
            story_title = title_pat.format(spec=theme_name)

            # Construct unique narrative paragraphs
            opening_template = openings[i % len(openings)]
            middle_template = middles[(i + 1) % len(middles)]
            ending_template = endings[(i + 2) % len(endings)]

            p1 = opening_template.format(setting=setting_name)
            p2 = middle_template.format(setting=setting_name)
            p3 = ending_template.format(setting=setting_name)

            story_text = f"{p1}\n\n{p2}\n\n{p3}"

            # Format keywords
            extra_kws = [genre.lower(), theme_name.lower(), mood_name.lower()]
            all_kws = list(dict.fromkeys(keywords_list + extra_kws))
            kws_str = ", ".join(all_kws)

            story_record = {
                "id": f"ST-{story_id_counter:04d}",
                "title": story_title,
                "category": genre,
                "theme": theme_name,
                "setting": setting_name,
                "mood": mood_name,
                "keywords": kws_str,
                "story": story_text
            }

            all_stories.append(story_record)
            story_id_counter += 1

    print(f"[+] Total stories constructed: {len(all_stories)}")
    return all_stories


def save_dataset_to_csv(stories, output_csv_path="data/raw/stories.csv"):
    """Saves stories list to data/raw/stories.csv."""
    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)

    fieldnames = ["id", "title", "category", "theme", "setting", "mood", "keywords", "story"]

    with open(output_csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for s in stories:
            writer.writerow(s)

    print(f"[+] Successfully saved {len(stories)} stories to {output_csv_path}")


if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    RAW_CSV = os.path.join(BASE_DIR, "data", "raw", "stories.csv")

    stories = generate_large_story_dataset(target_count_per_genre=40)
    save_dataset_to_csv(stories, RAW_CSV)
