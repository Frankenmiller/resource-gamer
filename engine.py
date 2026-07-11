# engine.py
import sys
import os
import time
import random
import subprocess

class GameEngine:
    def __init__(self):
        from game import Player, Market, CLR, COMMODITIES, HUBS, EventEngine
        self.player = Player()
        self.markets = {hub: Market(hub) for hub in HUBS}
        self.events = EventEngine()
        self.running = True
        self.CLR = CLR

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def generate_sector_map(self):
        from game import HUBS, CLR
        """Generates a perfectly aligned, customized visual transit timeline."""
        # 1. Map your full game cities to your custom-styled shortcodes
        city_shortcodes = {
            "Neo-Chicago": "NEO-CHI",
            "Detroit Foundry": "DETROIT",
            "Austin Megaplex": "AUSTIN",
            "Silicon Valley": "SILICON",
            "New Orleans": "NEW-ORL"
        }
        
        map_segments = []
        for hub in HUBS:
            # Fallback to standard uppercase 7-char crop if name isn't mapped
            short_name = city_shortcodes.get(hub, hub.upper()[:7])
            
            if hub == self.player.current_hub:
                # Active city gets the vehicle beacon and structural brackets
                map_segments.append(f"[{CLR['CYAN']}{CLR['BOLD']}🛸 {short_name}{CLR['RESET']}]")
            else:
                # Standby nodes sit neatly on the flight path
                map_segments.append(f" {short_name} ")
        
        connector = f"{CLR['BLUE']}══🔀══{CLR['RESET']}"
        return connector.join(map_segments).strip()

    def draw_header(self):
        from game import CLR
        self.clear_screen()
        p = self.player
        r = p.rig
        
        # Color conditional logic for low levels
        fuel_color = CLR["GREEN"] if r.fuel > 30 else CLR["RED"]
        cond_color = CLR["GREEN"] if r.condition > 40 else CLR["RED"]
        cargo_color = CLR["CYAN"] if r.free_cargo > 0 else CLR["YELLOW"]
        
        print()
        print()
        print(f"{CLR['BLUE']}=" * 70 + f"{CLR['RESET']}")
        print(f" {CLR['BOLD']}OPERATOR:{CLR['RESET']} {p.name:<13} | {CLR['BOLD']}DAY:{CLR['RESET']} {CLR['CYAN']}{p.days_elapsed:02d}{CLR['RESET']} | {CLR['BOLD']}LOCATION:{CLR['RESET']} {CLR['YELLOW']}{p.current_hub}{CLR['RESET']}")
        print(f" {CLR['BOLD']}CASH:{CLR['RESET']} {CLR['GREEN']}${p.cash:<14}{CLR['RESET']} | {CLR['BOLD']}FUEL:{CLR['RESET']} {fuel_color}{r.fuel}/{r.max_fuel}L{CLR['RESET']} | {CLR['BOLD']}RIG INTEGRITY:{CLR['RESET']} {cond_color}{r.condition:.1f}%{CLR['RESET']}")
        print(f" {CLR['BOLD']}CARGO CONFIGURATION:{CLR['RESET']} {cargo_color}{r.free_cargo}/{r.max_cargo} Units Free{CLR['RESET']}")
        print(f"{CLR['BLUE']}=" * 70 + f"{CLR['RESET']}")
        
        # ─── YOUR SECTOR MAP TIMELINE INTEGRATION ───────────────────────────
        print(f" {CLR['BOLD']}SECTOR MAP VECTOR TRACKER:{CLR['RESET']}")
        print(self.generate_sector_map())
        print(f"{CLR['BLUE']}=" * 70 + f"{CLR['RESET']}")
        # ────────────────────────────────────────────────────────────────────
        
        # Format logs intelligently based on event warnings
        log_text = self.events.active_event_text
        if "🚨" in log_text or "⚠️" in log_text or "🏴‍☠️" in log_text:
            print(f" {CLR['RED']}{CLR['BOLD']}LOG: {log_text}{CLR['RESET']}")
        elif "💰" in log_text or "🟩" in log_text:
            print(f" {CLR['GREEN']}{CLR['BOLD']}LOG: {log_text}{CLR['RESET']}")
        else:
            print(f" {CLR['WHITE']}LOG: {log_text}{CLR['RESET']}")
        print(f"{CLR['BLUE']}=" * 70 + f"{CLR['RESET']}")

    def display_market(self):
        from game import CLR, COMMODITIES
        current_market = self.markets[self.player.current_hub]
        
        # Color codes based on market modifier state
        mod_colors = {"Stable": CLR["WHITE"], "Supply Crunch": CLR["RED"], "Resource Glut": CLR["CYAN"]}
        m_color = mod_colors.get(current_market.current_modifier, CLR['WHITE'])
        
        print(f"\n---------- {CLR['YELLOW']}{current_market.name}{CLR['RESET']} Exchange ---------- [Status: {m_color}{CLR['BOLD']}{current_market.current_modifier}{CLR['RESET']}] ---")
        print(f"{CLR['BOLD']}{'Commodity':<18} | {'Price':<10} | {'Weight(U)':<10} | {'In Cargo':<8}| {'Total Value':<12}{CLR['RESET']}")
        print(f"{CLR['CYAN']}-" * 69 + f"{CLR['RESET']}") # Stretched divider line to fit the new column flawlessly
        
        for comm, price in current_market.prices.items():
            if comm == "Neural Stims": 
                continue # Kept hidden inside baseline retail nodes
            qty = self.player.rig.cargo[comm] # <-- This is our raw inventory integer
            weight = COMMODITIES[comm]['weight']
            
            # Format colors based on holdings
            qty_str = f"{CLR['GREEN']}{qty:<3}{CLR['RESET']}" if qty > 0 else f"{qty:<3}"
            
            # FIXED MATHEMATICS EXECUTOR:
            total_val = qty * price            
            
            # Clean grid alignment output print:
            print(f"{comm:<18} | {CLR['GREEN']}${price:04d}{CLR['RESET']} USDC | {weight:04d}  lbs | {qty_str}units | {CLR['CYAN']}${total_val:05d}{CLR['RESET']} USDC")

    def handle_buy(self):
        from game import COMMODITIES, CLR, SoundEngine
        current_market = self.markets[self.player.current_hub]
        print("\nSelect item to BUY (or press Enter to cancel):")
        comms_list = list(COMMODITIES.keys())
        for idx, comm in enumerate(comms_list, 1):
            print(f"[{idx}] {comm} (${current_market.prices[comm]})")
        
        choice = input(">> ").strip()
        if not choice.isdigit() or int(choice) not in range(1, len(comms_list) + 1):
            return

        commodity = comms_list[int(choice) - 1]
        price = current_market.prices[commodity]
        weight = COMMODITIES[commodity]["weight"]

        # Calculate limits
        max_afford = self.player.cash // price
        max_fit = self.player.rig.free_cargo // weight
        max_purchasable = min(max_afford, max_fit)

        if max_purchasable <= 0:
            print("🚫 Insufficient cargo space or cash funds!")
            print()
            time.sleep(1.5)
            return

        print()
        print(f"How many {commodity} to buy? (Max: {max_purchasable})")
        print("Type M to buy Maximum")
        qty_input = input(">> ").strip().lower()
        if qty_input == 'm' or qty_input == 'max':
            qty = max_purchasable
        elif qty_input.isdigit():
            qty = int(qty_input)
        else:
            qty = 0

        if 0 < qty <= max_purchasable:  # <-- CHANGED FROM max_sell TO max_purchasable
            self.player.cash -= qty * price
            self.player.rig.cargo[commodity] += qty
            SoundEngine.play("cash")
            print(f"🟩 Successfully purchased {qty}x {commodity}.")
            print()
            time.sleep(1)

    def handle_sell(self):
        current_market = self.markets[self.player.current_hub]
        print("\nSelect item to SELL (or press Enter to cancel):")
        print()
        comms_list = [c for c in COMMODITIES.keys() if self.player.rig.cargo[c] > 0]
        
        if not comms_list:
            print("You have no cargo to sell.")
            print()
            time.sleep(1.5)
            return

        for idx, comm in enumerate(comms_list, 1):
            print(f"[{idx}] {comm} (Owned: {self.player.rig.cargo[comm]} | Value: ${current_market.prices[comm]})")
        
        choice = input(">> ").strip()
        if not choice.isdigit() or int(choice) not in range(1, len(comms_list) + 1):
            return

        commodity = comms_list[int(choice) - 1]
        price = current_market.prices[commodity]
        max_sell = self.player.rig.cargo[commodity]

        print()
        print(f"How many {commodity} to sell? (Max: {max_sell})")
        print("Type M to sell Maximum")
        print()
        qty_input = input(">> ").strip().lower()
        if qty_input == 'm' or qty_input == 'max':
            qty = max_sell
        elif qty_input.isdigit():
            qty = int(qty_input)
        else:
            qty = 0

        if 0 < qty <= max_sell:
            self.player.cash += qty * price
            self.player.rig.cargo[commodity] -= qty
            SoundEngine.play("cash")  # <-- TRIGER AUDIO
            print(f"🟨 Successfully sold {qty}x {commodity}.")
            print()
            time.sleep(1)

    def handle_travel(self):
        from game import HUBS, SoundEngine, CLR
        print("\nSelect destination hub to route flight plan:")
        print()
        destinations = [h for h in HUBS if h != self.player.current_hub]
        
        # Pull dynamic fuel cost based on engine tier
        fuel_cost = self.player.rig.fuel_per_jump
        
        for idx, hub in enumerate(destinations, 1):
            # Dynamic text printout reflecting upgrades
            print(f"[{idx}] {hub} (Cost: {fuel_cost}L Fuel, 5% Wear & Tear)")
        
        choice = input(">> ").strip()
        if not choice.isdigit() or int(choice) not in range(1, len(destinations) + 1):
            return

        destination = destinations[int(choice) - 1]
        
        # Dynamic validation check
        if self.player.rig.fuel < fuel_cost:
            print(f"❌ Not enough fuel  to complete jump! Needs {fuel_cost}L.")
            print()
            time.sleep(1.5)
            return
        if self.player.rig.condition <= 0:
            print("❌ Rig is completely disabled. Repair required!")
            print()
            time.sleep(1.5)
            return

        self.player.rig.fuel -= fuel_cost
        self.player.rig.condition = max(0, self.player.rig.condition - 5)
        self.player.current_hub = destination
        self.trigger_interception_event()
        self.generate_market_rumor()
        self.player.days_elapsed += 1

        if self.player.debt > 0:
            interest = int(self.player.debt * 0.10)
            self.player.debt += interest

        self.events.roll_turn_event(self.player, self.markets)
        SoundEngine.play("jump")  # <-- TRIGER AUDIO
        print(f"🚀 Jumping through transit lanes to {destination}...")
        print()
        time.sleep(1.5)
    
    def trigger_interception_event(self):
        from game import CLR, SoundEngine
        import random
        if random.random() > 0.25:
            return

        p = self.player
        r = p.rig

        if random.random() > 0.50:
            encounter_type = "syndicate raiders"
            SoundEngine.play("scary")
        else:
            encounter_type = "port authority"
            SoundEngine.play("siren")

        self.clear_screen()        
        
        self.clear_screen()
        print(f"{CLR['RED']}" + "🏴‍☠️ " * 18 + f"{CLR['RESET']}")
        print(f" {CLR['RED']}{CLR['BOLD']}CRITICAL WARNING: PROXIMITY ALERT{CLR['RESET']}")
        print(f" Your rig has been pulled out of warp by a rival syndicate cruiser!")
        print(f" They are locking weapon vectors onto your cargo bays.")
        print(f"{CLR['RED']}" + "🏴‍☠️ " * 18 + f"{CLR['RESET']}")
        print()

        # Build dynamic choice constraints based on current rig configurations
        print(f" {CLR['BOLD']}1. BURN FOIL TO EVADE{CLR['RESET']} (Costs 15L Fuel - Requires escape vectors)")
        print(f" {CLR['BOLD']}2. JETTISON CARGO{CLR['RESET']}     (Dump 1 random inventory asset line as a bribe)")
        print(f" {CLR['BOLD']}3. STAND YOUR GROUND{CLR['RESET']}   (Engage deflector shields and scrap with them)")
        print()

        choice = input("CHOOSE YOUR VECTOR >> ").strip()
        print()

        if choice == "1":
            if r.fuel >= 15:
                r.fuel -= 15
                self.events.active_event_text = "⚠️ Burned 15L fuel executing extreme evasive maneuvers. Escaped safely!"
            else:
                print(f"\n {CLR['RED']}INSUFFICIENT FUEL TO EVADE!{CLR['RESET']} You are forced to stand your ground...")
                print()
                self.execute_combat_sequence()

        elif choice == "2":
            # Filter down to see if the player actually has cargo lines to dump
            active_cargo = [item for item, qty in p.cargo.items() if qty > 0]
            if active_cargo:
                dumped_item = random.choice(active_cargo)
                p.cargo[dumped_item] -= 1
                # Recalculate free cargo space parameters
                r.free_cargo += 1 
                self.events.active_event_text = f"🏴‍☠️ Jettisoned 1 unit of {dumped_item.upper()} to bribe the raiders."
            else:
                print(f"\n {CLR['YELLOW']}YOUR CARGO BAY IS EMPTY!{CLR['RESET']} There is nothing to dump. Engaging combat...")
                print()
                self.execute_combat_sequence()

        elif choice == "3":
            self.execute_combat_sequence()
            
        else:
            print(f"\n {CLR['RED']}HESITATION WAS FATAL!{CLR['RESET']} They blew past your shields while you stalled.")
            print()
            self.execute_combat_sequence()
            
        # Pause briefly so the player can process the layout outcome before the main screen flashes
        input(f"\n{CLR['CYAN']}Press Enter to cycle thrusters...{CLR['RESET']}")
    
    def execute_combat_sequence(self):
        """Evaluates dice-roll outcomes based on rig integrity structural limits."""
        import random
        p = self.player
        r = p.rig
        
        print(f"\n{CLR['YELLOW']}🔋 Cycling kinetic energy fields... Engaging defense grids...{CLR['RESET']}")
        print()
        
        # Win chance scales beautifully with the rig's actual physical health status
        win_chance = 0.50 + (r.condition / 200.0) # E.g., 90% condition adds a sweet bonus
        
        if random.random() < win_chance:
            salvage_bounty = random.randint(400, 950)
            p.cash += salvage_bounty
            # Take minor structural damage from the kinetic crossfire
            damage = random.uniform(5.0, 15.0)
            r.condition = max(0.0, r.condition - damage)
            
            self.events.active_event_text = f"🟩 SUCCESS: Outmaneuvered the rival rig! Salvaged ${salvage_bounty} from scraps. Structural Integrity lost: -{damage:.1f}%"
        else:
            # Failure drops severe damage parameters and a massive cash deduction penalty
            theft_loss = min(p.cash, random.randint(500, 1500))
            p.cash -= theft_loss
            damage = random.uniform(20.0, 40.0)
            r.condition = max(0.0, r.condition - damage)
            
            self.events.active_event_text = f"🚨 DEFEAT: Rig breached! Raiders looted ${theft_loss} and decimated systems. Structural Integrity lost: -{damage:.1f}%"
    
    def check_game_conditions(self):
        p = self.player
        
        # Win Condition
        if p.cash >= 100000 and p.debt <= 0:
            self.clear_screen()
            SoundEngine.play("jump")
            print(f"\n🏆 {CLR['GREEN']}{CLR['BOLD']}VICTORY ACHIEVED!{CLR['RESET']}")
            print("="*60)
            print(f"With ${p.cash:,} in corporate cash reserves and zero standing debt,")
            print(f"you bought out your contract on Day {p.days_elapsed}! You are a Trade Baron.")
            print("="*60)
            print()
            self.running = False
            return True
            
        # Loss Condition 1: Structural Catastrophe
        if p.rig.condition <= 0:
            self.clear_screen()
            SoundEngine.play("alarm")
            print(f"\n☠️ {CLR['RED']}{CLR['BOLD']}GAME OVER: CRITICAL STRUCTURAL FAILURE{CLR['RESET']}")
            print("="*60)
            print("Your rig's frame completely decoupled in deep space transit lanes.")
            print("Emergency pods failed to deploy. Operator footprint cleared.")
            print("="*60)
            print()
            self.running = False
            return True

        # Loss Condition 2: Syndicate Bankruptcy
        if p.cash <= 0 and p.debt > p.cash + 10000:
            self.clear_screen()
            SoundEngine.play("alarm")
            print(f"\n☠️ {CLR['RED']}{CLR['BOLD']}GAME OVER: LIQUIDATED BY SYNDICATE{CLR['RESET']}")
            print("="*60)
            print("Your debt spiraled completely out of financial projection parameters.")
            print("Corporate loan sharks have repossessed your ship and your lungs.")
            print("="*60)
            print()
            self.running = False
            return True
            
        return False
    
    def handle_banking(self):
        from game import CLR, SoundEngine
        p = self.player
        SoundEngine.play("guzzle")
        while True:
            self.draw_header()
            interest_preview = int(p.debt * 0.10)
            print(f"\n===================== 🏦 MEGACORP BANKING HUB 🏦 =====================")
            print(f" Current Outstanding Debt: {CLR['RED']}${p.debt}{CLR['RESET']} USDC")
            print(f" Daily Accumulated Interest rate: 10% (+${interest_preview}/jump)")
            print(f"----------------------------------------------------------------------")
            print(f" [1] Take Out Corporate Loan (+$2,000 USDC)")
            print(f" [2] Make Debt Repayment Payment")
            print(f" [{CLR['GREEN']}B{CLR['RESET']}] Back to Main Terminal Menu")
            print(f"======================================================================")
            print()
            
            choice = input("Bank Command >> ").strip().lower()

            if choice == "1":
                if p.debt >= 15000:
                    print("❌ Credit line denied. Your leverage risk threshold is maximized.")
                    print()
                else:
                    p.cash += 2000
                    p.debt += 2000
                    SoundEngine.play("cash")
                    print("🟩 $2,000 wired to your liquidity accounts.")
                    print()
                time.sleep(1)
            elif choice == "2":
                if p.debt <= 0:
                    print("You have no outstanding obligations.")
                    print()
                    time.sleep(1)
                    continue
                print(f"Enter amount to pay down (Max: ${min(p.cash, p.debt)} USDC):")
                print(f"or simply press to [{CLR['RED']}C{CLR['RESET']}]ancel repayment")
                print()
                amt_input = input(">> Enter repayment amount in USDC: $").strip()
                if amt_input.isdigit():
                    print(f"\033[A>> ${amt_input} USDC") # \033[A moves the cursor UP one line to overwrite the raw input neatly                if amt_input.isdigit():
                    amt = int(amt_input)
                    if 0 < amt <= p.cash and amt <= p.debt:
                        p.cash -= amt
                        p.debt -= amt
                        SoundEngine.play("cash")
                        print(f"🟩 Repaid ${amt} off your syndicate ledger.")                        
                        print()
                    elif choice == "b" or choice == "":
                        break                        
                    else:
                        print("❌ Invalid balance transaction requested.")
                        print()
                time.sleep(1)
            elif choice == "b" or choice == "":
                break
    
    def handle_maintenance(self):
        from game import CLR, SoundEngine
        r = self.player.rig
        
        # Maintenance math
        fuel_needed = r.max_fuel - r.fuel
        fuel_cost = fuel_needed * 4
        repair_needed = 100 - r.condition
        repair_cost = int(repair_needed * 30)

        # Upgrade costs and balancing tiers
        cargo_upgrade_cost = r.cargo_tier * 3500
        engine_upgrade_cost = r.engine_tier * 4000
        armor_upgrade_cost = r.armor_tier * 3000

        while True:
            self.draw_header()
            print(f"\n====================== 🛠️  HANGAR & UPGRADE SHOP 🛠️  ===================")
            print()
            print(f" [1] Top off Fuel  -------------------------> ${fuel_cost:04d} (+{fuel_needed}L)")
            print(f" [2] Structural Repairs  -------------------> ${repair_cost:04d} (+{repair_needed:.1f}%)")
            print(f"----------------------------------------------------------------------")
            print(f" [3] Expand Cargo Hull (Tier{r.cargo_tier}->{r.cargo_tier + 1}) ----------> ${cargo_upgrade_cost} (+10 Space)")
            print(f" [4] Fine-Tune Hyper-Drive (Tier{r.engine_tier}->{r.engine_tier + 1}) ------> ${engine_upgrade_cost} (-4L Fuel/Jump)")
            print(f" [5] Reinforce Titanium Armor (Tier{r.armor_tier}->{r.armor_tier + 1}) ---> ${armor_upgrade_cost} (+25% Dmg Resist)")
            print(f" [B]ack to Main Terminal Menu")
            print()
            print(f"======================================================================")
            print()
            
            choice = input("Hangar Command >> ").strip().lower()

            if choice == "1" and fuel_needed > 0:
                if self.player.cash >= fuel_cost:
                    self.player.cash -= fuel_cost
                    r.fuel = r.max_fuel
                    fuel_needed, fuel_cost = 0, 0
                    SoundEngine.play("guzzle")
                    print("🟩 Fuel tanks fully pressurized.")
                    print()
                else:
                    print("❌ Insufficient corporate liquid cash reserves.")
                    print()
                time.sleep(1)
            elif choice == "2" and repair_needed > 0:
                if self.player.cash >= repair_cost:
                    self.player.cash -= repair_cost
                    r.condition = 100.0
                    repair_needed, repair_cost = 0, 0
                    print("🟩 Frame integrated. Structural safety index: 100%")
                    print()
                else:
                    print("❌ Insufficient corporate liquid cash reserves.")
                    print()
                time.sleep(1)
            elif choice == "3":
                if self.player.cash >= cargo_upgrade_cost:
                    self.player.cash -= cargo_upgrade_cost
                    r.cargo_tier += 1
                    r.max_cargo += 10
                    print(f"🟩 Hull Expanded! New maximum volume: {r.max_cargo}")
                    print()
                    break # Break out to refresh master screen assets
                else:
                    print("❌ Upgrades require hard capital up front.")
                    print()
                time.sleep(1)
            elif choice == "4":
                if r.engine_tier >= 4:
                    print("❌ Drive core is already operating at maximum efficiency.")
                    print()
                elif self.player.cash >= engine_upgrade_cost:
                    self.player.cash -= engine_upgrade_cost
                    r.engine_tier += 1
                    print(f"🟩 Engine optimized! Flight burn rate dropped to: {r.fuel_per_jump}L/jump.")
                    print()
                    break
                else:
                    print("❌ Upgrades require hard capital up front.")
                    print()
                time.sleep(1)
            elif choice == "5":
                if r.armor_tier >= 4:
                    print("❌ Hull shielding matrix cannot be augmented further.")
                    print()
                elif self.player.cash >= armor_upgrade_cost:
                    self.player.cash -= armor_upgrade_cost
                    r.armor_tier += 1
                    print(f"🟩 Armor reinforced! Passive event damage absorption: {r.damage_reduction * 100}%")
                    print()
                    break
                else:
                    print("❌ Upgrades require hard capital up front.")
                    print()
                time.sleep(1)
            elif choice == "b" or choice == "":
                break

    def generate_market_rumor(self):
        """Randomly generates a high-impact market shift event in a distant hub."""
        import random
        # 35% chance a rumor drops during a flight transition
        if random.random() > 0.35:
            return

        # Pick a random hub that ISN'T where the player just landed
        other_hubs = [h for h in self.markets.keys() if h != self.player.current_hub]
        if not other_hubs:
            return
        target_hub = random.choice(other_hubs)
        market = self.markets[target_hub]

        # Pick a random commodity (excluding Neural Stims)
        available_comms = [c for c in market.prices.keys() if c != "Neural Stims"]
        if not available_comms:
            return
        target_comm = random.choice(available_comms)

        # Determine if it's a massive boom or a total crash
        is_boom = random.random() > 0.5
        if is_boom:
            market.current_modifier = "Supply Crunch"
            # Spike the price instantly by 2.5x to 4x
            market.prices[target_comm] = int(market.prices[target_comm] * random.uniform(2.5, 4.0))
            flavor_text = f"🚨 INTERCEPTED INTEL: A massive supply breakdown reported in {market.name}! Prices for {target_comm.upper()} are skyrocketing!"
        else:
            market.current_modifier = "Resource Glut"
            # Tank the price down to 20% - 40% of baseline
            market.prices[target_comm] = max(10, int(market.prices[target_comm] * random.uniform(0.2, 0.4)))
            flavor_text = f"📉 MARKET ALERT: Unloading drones dumping surplus inventory at {market.name}. {target_comm.upper()} prices have absolutely cratered!"

        # Push this message directly to your game's active alert notifications ticker
        if hasattr(self, 'events'):
            self.events.active_event_text = flavor_text
        else:
            print(f"\n{CLR['YELLOW']}{flavor_text}{CLR['RESET']}")
            input(f"{CLR['CYAN']}Press Enter to acknowledge feed...{CLR['RESET']}")

    def run(self):
        """Main operational execution loop."""
        from game import CLR
        while self.running:
            # First, check if the player won or lost during the last action tick
            if self.check_game_conditions():
                break
                
            self.draw_header()
            if self.player.debt > 0:
                print(f" {CLR['RED']}⚠️  OUTSTANDING BALANCE OWED ⚠️ :${self.player.debt}{CLR['RESET']}")
                print(f"{CLR['BLUE']}=" * 70 + f"{CLR['RESET']}")
                
            self.display_market()
            
            # Updated to explicitly display the Financial Bank option to the operator
            print(f"\n [{CLR['GREEN']}B{CLR['RESET']}]uy Cargo  |  [{CLR['GREEN']}S{CLR['RESET']}]ell Cargo  |  [{CLR['CYAN']}T{CLR['RESET']}]ravel to Hub")
            print(f" [{CLR['YELLOW']}M{CLR['RESET']}]aintenance  |  [{CLR['YELLOW']}F{CLR['RESET']}]inancial Bank  |  [{CLR['RED']}Q{CLR['RESET']}]uit Game")
            action = input(f"\n{CLR['BOLD']}Command >> {CLR['RESET']}").strip().lower()

            if action == 'b':
                self.handle_buy()
            elif action == 's':
                self.handle_sell()
            elif action == 't':
                self.handle_travel()
            elif action == 'm':
                self.handle_maintenance()
            elif action == 'f':
                self.handle_banking()  # <-- REGISTERED THE ACTION MAPPING
            elif action == 'q':
                print("\nShutting down central operating systems. Safe travels, spacer.")
                print()
                self.running = False
            else:
                continue