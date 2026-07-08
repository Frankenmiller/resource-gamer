#!/usr/bin/env python3
import random
import os
import sys
import time
import subprocess

CLR = {
    "RESET":   "\033[0m",
    "BOLD":    "\033[1m",
    "RED":     "\033[31m",
    "GREEN":   "\033[32m",
    "YELLOW":  "\033[33m",
    "BLUE":    "\033[34m",
    "CYAN":    "\033[36m",
    "WHITE":   "\033[37m",
    "BG_RED":  "\033[41m",
    "BG_BLUE": "\033[44m"
}

class SoundEngine:
    @staticmethod
    def play(sound_type):
        """Plays native cross-platform terminal synth sounds without external dependencies."""
        try:
            if sys.platform == "darwin":  # Mac OS X
                if sound_type == "cash":
                    # Stacks two distinct tones simultaneously to simulate a classic register pull
                    subprocess.Popen(["afplay", "/System/Library/Sounds/Pop.aiff"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    subprocess.Popen(["afplay", "/System/Library/Sounds/Glass.aiff"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                elif sound_type == "jump":
                    # Uses a cool sci-fi sounding built-in pulse
                    subprocess.Popen(["afplay", "/System/Library/Sounds/Submarine.aiff"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                elif sound_type == "alarm":
                    subprocess.Popen(["afplay", "/System/Library/Sounds/Basso.aiff"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            elif sys.platform == "win32":  # Windows
                if sound_type == "cash":
                    subprocess.Popen(["powershell", "[console]::beep(1200,100); [console]::beep(1800,150)"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                elif sound_type == "jump":
                    subprocess.Popen(["powershell", "[console]::beep(400,100); [console]::beep(600,100); [console]::beep(900,200)"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                elif sound_type == "alarm":
                    subprocess.Popen(["powershell", "[console]::beep(300,400)"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                # Fallback for Linux / Others
                print("\a", end="", flush=True)
        except Exception:
            pass

# ============================================================================
# CONFIGURATION & CONSTANTS
# ============================================================================
HUBS = ["Neo-Chicago", "Detroit Foundry", "Austin Megaplex", "Silicon Valley", "New Orleans Port"]

COMMODITIES = {
    "Fuel Cells":  {"base_price": 50,  "volatility": 0.15, "weight": 1},
    "Heavy Metals": {"base_price": 120, "volatility": 0.20, "weight": 3},
    "Biotech Meds": {"base_price": 450, "volatility": 0.35, "weight": 1},
    "Cybernetics": {"base_price": 800, "volatility": 0.25, "weight": 2},
    "Neural Stims":  {"base_price": 2500, "volatility": 0.60, "weight": 1}, # NEW: Black market contraband
}

HUB_ARCHETYPES = {
    "Detroit Foundry":  {"Heavy Metals": 0.5, "Biotech Meds": 1.8, "Fuel Cells": 1.0, "Cybernetics": 1.1},
    "Silicon Valley":   {"Cybernetics": 0.6, "Fuel Cells": 0.7, "Heavy Metals": 1.6, "Biotech Meds": 1.0},
    "New Orleans Port": {"Fuel Cells": 0.5, "Cybernetics": 1.5, "Heavy Metals": 1.1, "Biotech Meds": 0.9},
    "Austin Megaplex":  {"Biotech Meds": 0.5, "Heavy Metals": 1.5, "Cybernetics": 1.0, "Fuel Cells": 1.1},
    "Neo-Chicago":      {"Fuel Cells": 1.0, "Heavy Metals": 1.0, "Biotech Meds": 1.0, "Cybernetics": 1.0} # Baseline
}

# ============================================================================
# GAME STATE CLASSES
# ============================================================================

class Rig:
    def __init__(self, max_cargo=20, max_fuel=100):
        self.max_cargo = max_cargo
        self.max_fuel = max_fuel
        self.fuel = max_fuel
        self.condition = 100.0
        # This will automatically include Neural Stims now
        self.cargo = {comm: 0 for comm in COMMODITIES}
        
        self.cargo_tier = 1
        self.engine_tier = 1
        self.armor_tier = 1

    @property
    def used_cargo(self):
        return sum(self.cargo[comm] * COMMODITIES[comm]["weight"] for comm in self.cargo)

    @property
    def free_cargo(self):
        return self.max_cargo - self.used_cargo

    @property
    def fuel_per_jump(self):
        # Base is 20L, drops by 4L per engine tier upgrade
        return max(8, 24 - (self.engine_tier * 4))

    @property
    def damage_reduction(self):
        # Every armor tier reduces incoming event damage by 25%
        return (self.armor_tier - 1) * 0.25

class Market:
    def __init__(self, name):
        self.name = name
        self.prices = {}
        self.current_modifier = "Stable"
        self.randomize_market()

    def randomize_market(self, event_mod=1.0, modifier_name="Stable"):
        """Calculates prices based on regional biases * random ambient volatility * event spikes."""
        self.current_modifier = modifier_name
        archetype = HUB_ARCHETYPES.get(self.name, {})

        for comm, data in COMMODITIES.items():
            base = data["base_price"]
            regional_bias = archetype.get(comm, 1.0)
            ambient_fluctuation = random.uniform(-data["volatility"], data["volatility"])
            final_price = int(base * regional_bias * (1 + ambient_fluctuation) * event_mod)
            self.prices[comm] = max(5, final_price)

class Player:
    def __init__(self, name="Hustler", starting_cash=5000):
        self.name = name
        self.cash = starting_cash
        self.current_hub = random.choice(HUBS)
        self.rig = Rig()
        self.days_elapsed = 1
        self.debt = 2500

class EventEngine:
    def __init__(self):
        self.active_global_modifier = 1.0
        self.active_event_text = "Flight transit completed smoothly."
        self.market_modifier_name = "Stable"

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def roll_turn_event(self, player, markets):
        """Triggers interactive choices or global economic disruptions during jumps."""
        roll = random.random()
        
        # Reset baseline defaults
        self.active_global_modifier = 1.0
        self.market_modifier_name = "Stable"
        self.active_event_text = "Flight transit completed smoothly."

        # 1. MARKET SPECIAL EVENTS (Ambient)
        if roll < 0.10:
            self.active_event_text = "⚠️ CRISIS: Solar flare blocks supply chains! High-tech prices soaring."
            self.active_global_modifier = 1.6
            self.market_modifier_name = "Supply Crunch"
            self.update_all_markets(player, markets)
            return
            
        elif roll < 0.20:
            self.active_event_text = "📉 GLUT: Corporate liquidation floods regional sectors with cheap assets!"
            self.active_global_modifier = 0.5
            self.market_modifier_name = "Resource Glut"
            self.update_all_markets(player, markets)
            return

        # 2. INTERACTIVE ENCOUNTERS (Stops execution for player choice)
        elif roll < 0.35:
            self.trigger_customs_checkpoint(player)
            
        elif roll < 0.50:
            self.trigger_black_market_dealer(player)
            
        elif roll < 0.65:
            self.trigger_space_pirate_encounter(player)

        # Ambient updates for non-event ticks
        self.update_all_markets(player, markets)

    def update_all_markets(self, player, markets):
        for market in markets.values():
            if market.name == player.current_hub and self.market_modifier_name != "Stable":
                market.randomize_market(self.active_global_modifier, self.market_modifier_name)
            else:
                market.randomize_market(1.0, "Stable")

    # ================= INTERACTIVE SCENARIOS =================
    
    def trigger_customs_checkpoint(self, player):
        self.clear_screen()
        print("=" * 70)
        print("🛂 CUSTOMS AUTHORITIES INTERCEPTED YOUR RIG")
        print("=" * 70)
        print("Sector security forces have flagged your transport for scanning.")
        
        has_contraband = player.rig.cargo["Neural Stims"] > 0
        
        if has_contraband:
            print("\n🚨 WARNING: You are carrying highly illegal Neural Stims!")
            print("[1] Attempt to bribe the officers ($1,500)")
            print("[2] Submit to the scanner matrix (Risk seizure and massive fine)")
        else:
            print("\nYour cargo manifest appears entirely legal.")
            print("[1] Cooperate fully and pay basic transit tariff ($300)")
            print("[2] Argue administrative technicalities (Risk delay/fines)")

        choice = input("\nAction >> ").strip()

        if has_contraband:
            if choice == "1" and player.cash >= 1500:
                player.cash -= 1500
                self.active_event_text = "🛂 CUSTOMS: Paid a $1,500 bribe. The guards looked the other way."
            else:
                # Caught red-handed!
                stims_count = player.rig.cargo["Neural Stims"]
                fine = stims_count * 2000 + 1000
                player.rig.cargo["Neural Stims"] = 0
                player.cash = max(0, player.cash - fine)
                self.active_event_text = f"🚨 BUSTED: Customs seized {stims_count}x Neural Stims and fined you ${fine}!"
        else:
            if choice == "2" and random.random() < 0.5:
                self.active_event_text = "🛂 CUSTOMS: Your administrative arguments worked. No fees charged!"
            else:
                fee = 300 if choice == "1" else 600
                player.cash = max(0, player.cash - fee)
                self.active_event_text = f"🛂 CUSTOMS: Processed checkpoint clearance. Paid tariff fees of ${fee}."
        time.sleep(1)

    def trigger_black_market_dealer(self, player):
        if player.rig.free_cargo < 1:
            return # No room for shady deals
            
        self.clear_screen()
        print("=" * 70)
        print("🛸 BACK-ALLEY INTERCEPT: SHADY DEALER")
        print("=" * 70)
        print("An unmarked stealth hauler hails your comms channel, offering an off-market asset.")
        print(f"They offer 1 Unit of [Neural Stims] for an absolute steal of $1,200.")
        print(f"Current Cargo Space: {player.rig.free_cargo}/{player.rig.max_cargo}")
        print(f"Current Liquid Cash: ${player.cash}")
        print("\n[1] Purchase the contraband ($1,200)")
        print("[2] Decline the transactional risk")

        choice = input("\nAction >> ").strip()

        if choice == "1":
            if player.cash >= 1200:
                player.cash -= 1200
                player.rig.cargo["Neural Stims"] += 1
                self.active_event_text = "🛸 BLACK MARKET: Acquired 1 Unit of Neural Stims. Keep an eye out for customs!"
            else:
                self.active_event_text = "🛸 BLACK MARKET: You couldn't afford the package. The dealer warped away."
        else:
            self.active_event_text = "🛸 BLACK MARKET: You turned down the deal."
        time.sleep(1)

    def trigger_space_pirate_encounter(self, player):
        self.clear_screen()
        print("=" * 70)
        print("🏴‍☠️ WARNING: EMERGENCE PROTOCOL - RADAR LOCK")
        print("=" * 70)
        print("A band of sector raiders has cornered your rig in deep transit space!")
        print("They demand a corporate tribute or threaten total structural disassembly.")
        print("\n[1] Pay extortion tribute ($2,000)")
        print("[2] Push engines to maximum and break blockades")

        choice = input("\nAction >> ").strip()

        if choice == "1" and player.cash >= 2000:
            player.cash -= 2000
            self.active_event_text = "🏴‍☠️ PIRATES: Extortion payment accepted. Raiders jumped out of system."
        else:
            # Player chooses to run, armor shields protect them
            damage = random.randint(30, 50)
            reduction = damage * player.rig.damage_reduction
            final_damage = max(0, int(damage - reduction))
            
            player.rig.condition = max(0, player.rig.condition - final_damage)
            
            # Pirates steal random cargo if you break away poorly
            stolen_stuff = False
            for c in player.rig.cargo:
                if player.rig.cargo[c] > 0:
                    player.rig.cargo[c] = max(0, player.rig.cargo[c] - 1)
                    stolen_stuff = True
                    break
                    
            text = f"🏴‍☠️ PIRATES: Gunfire punctured your hull! Took -{final_damage}% integrity (Armor blocked {int(reduction)}%)."
            if stolen_stuff:
                text += " They siphoned some cargo in the escape!"
            self.active_event_text = text
        time.sleep(1)

class GameEngine:
    def __init__(self):
        self.player = Player()
        self.markets = {hub: Market(hub) for hub in HUBS}
        self.events = EventEngine()
        self.running = True

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def generate_sector_map(self):
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
        current_market = self.markets[self.player.current_hub]
        
        # Color codes based on market modifier state
        mod_colors = {"Stable": CLR["WHITE"], "Supply Crunch": CLR["RED"], "Resource Glut": CLR["CYAN"]}
        m_color = mod_colors.get(current_market.current_modifier, CLR['WHITE'])
        
        print(f"\n--- {CLR['YELLOW']}{current_market.name}{CLR['RESET']} Exchange [Status: {m_color}{CLR['BOLD']}{current_market.current_modifier}{CLR['RESET']}] ---")
        print(f"{CLR['BOLD']}{'Commodity':<18} | {'Price':<8}   | {'Weight(U)':<10}| {'In Cargo':<8}{CLR['RESET']}")
        print(f"{CLR['CYAN']}-" * 50 + f"{CLR['RESET']}")
        
        for comm, price in current_market.prices.items():
            if comm == "Neural Stims": 
                continue # Kept hidden inside baseline retail nodes
            qty = self.player.rig.cargo[comm]
            weight = COMMODITIES[comm]['weight']
            
            # Format colors based on holdings
            qty_str = f"{CLR['GREEN']}{qty:<8}{CLR['RESET']}" if qty > 0 else f"{qty:<8}"
            
            # THIS IS THE LINE TO EDIT (Around line 450-460):
            print(f"{comm:<18} | {CLR['GREEN']}${price:04d}{CLR['RESET']} USDC | {weight:04d}  lbs| {qty_str}")
            print()

    def handle_buy(self):
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

        # Execute travel overhead deductions using dynamic value
        # Execute travel overhead deductions using dynamic value
        self.player.rig.fuel -= fuel_cost
        self.player.rig.condition = max(0, self.player.rig.condition - 5)
        self.player.current_hub = destination
        self.player.days_elapsed += 1

        # NEW: Add daily interest accumulation
        if self.player.debt > 0:
            interest = int(self.player.debt * 0.10)
            self.player.debt += interest

        # Run random engine ticks upon new day jump
        self.events.roll_turn_event(self.player, self.markets)
        SoundEngine.play("jump")  # <-- TRIGER AUDIO
        print(f"🚀 Jumping through transit lanes to {destination}...")
        print()
        time.sleep(1.5)

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
        p = self.player
        while True:
            self.draw_header()
            interest_preview = int(p.debt * 0.10)
            print(f"\n================ 🏦 MEGACORP BANKING HUB ================")
            print(f" Current Outstanding Debt: {CLR['RED']}${p.debt}{CLR['RESET']}")
            print(f" Daily Accumulated Interest rate: 10% (+${interest_preview}/jump)")
            print(f"-----------------------------------------------------------")
            print(f" [1] Take Out Corporate Loan (+$2,000)")
            print(f" [2] Make Debt Repayment Payment")
            print(f" [{CLR['GREEN']}B{CLR['RESET']}]ack to Main Terminal Menu")
            print(f"===========================================================")
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
                print(f"Enter amount to pay down (Max: ${min(p.cash, p.debt)}):")
                print()
                amt_input = input(">> ").strip()
                if amt_input.isdigit():
                    amt = int(amt_input)
                    if 0 < amt <= p.cash and amt <= p.debt:
                        p.cash -= amt
                        p.debt -= amt
                        SoundEngine.play("cash")
                        print(f"🟩 Repaid ${amt} off your syndicate ledger.")
                        print()
                    else:
                        print("❌ Invalid balance transaction requested.")
                        print()
                time.sleep(1)
            elif choice == "b" or choice == "":
                break
    
    def handle_maintenance(self):
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
            print(f"\n================= 🛠️ HANGAR & UPGRADE SHOP 🛠️ ================")
            print(f" [1] Top off Fuel (+{fuel_needed}L)             -->  ${fuel_cost}")
            print(f" [2] Structural Repairs (+{repair_needed:.1f}%)        -->  ${repair_cost}")
            print(f"-----------------------------------------------------------")
            print(f" [3] Expand Cargo Hull (Tier {r.cargo_tier} -> {r.cargo_tier + 1}) --------->  ${cargo_upgrade_cost} (+10 Space)")
            print(f" [4] Fine-Tune Hyper-Drive (Tier {r.engine_tier} -> {r.engine_tier + 1}) ----->  ${engine_upgrade_cost} (-4L Fuel/Jump)")
            print(f" [5] Reinforce Titanium Armor (Tier {r.armor_tier} -> {r.armor_tier + 1}) -->  ${armor_upgrade_cost} (+25% Dmg Resist)")
            print(f" [B]ack to Main Terminal Menu")
            print(f"===========================================================")
            print()
            
            choice = input("Hangar Command >> ").strip().lower()

            if choice == "1" and fuel_needed > 0:
                if self.player.cash >= fuel_cost:
                    self.player.cash -= fuel_cost
                    r.fuel = r.max_fuel
                    fuel_needed, fuel_cost = 0, 0
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

    def run(self):
        """Main operational execution loop."""
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


# ============================================================================
# ENTRY POINT
# ============================================================================
if __name__ == "__main__":
    try:
        engine = GameEngine()
        engine.run()
    except KeyboardInterrupt:
        print("\n\nSession terminated by operator. Goodbye.")
        print()
        sys.exit(0)
