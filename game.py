#!/usr/bin/env python3
import random
import os
import sys
import time
import subprocess
from engine import GameEngine

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
        import sys, subprocess
        try:
            if sys.platform == "darwin":  # Mac OS X
                if sound_type == "cash":
                    subprocess.Popen(["afplay", "/System/Library/Sounds/Pop.aiff"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    subprocess.Popen(["afplay", "/System/Library/Sounds/Glass.aiff"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                elif sound_type == "jump":
                    subprocess.Popen(["afplay", "/System/Library/Sounds/Submarine.aiff"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                elif sound_type == "alarm" or sound_type == "siren":
                    # Sosumi is an aggressive alert, perfect for authority lockdowns
                    subprocess.Popen(["afplay", "/System/Library/Sounds/Sosumi.aiff"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                elif sound_type == "scary":
                    # Basso is a deep, ominous rumbling tone
                    subprocess.Popen(["afplay", "/System/Library/Sounds/Basso.aiff"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                elif sound_type == "bank":
                    # Tink is a sharp, pristine digital chime for wire transfers
                    subprocess.Popen(["afplay", "/System/Library/Sounds/Tink.aiff"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                elif sound_type == "metal":
                    # Funk has a metallic, industrial resonance for upgrading components
                    subprocess.Popen(["afplay", "/System/Library/Sounds/Funk.aiff"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                elif sound_type == "guzzle":
                    # Blow is a hollow air rush that sounds exactly like liquid fuel pressure loading
                    subprocess.Popen(["afplay", "/System/Library/Sounds/Blow.aiff"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            elif sys.platform == "win32":  # Windows Fallback mapping
                if sound_type in ["cash", "bank"]:
                    subprocess.Popen(["powershell", "[console]::beep(1200,100); [console]::beep(1800,150)"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                elif sound_type in ["alarm", "siren", "scary"]:
                    subprocess.Popen(["powershell", "[console]::beep(250,500)"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                elif sound_type in ["metal", "guzzle", "jump"]:
                    subprocess.Popen(["powershell", "[console]::beep(600,150)"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
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
        print("=" * 65)
        print("🛂  CUSTOMS AUTHORITIES  🛂  HAVE INTERCEPTED YOUR RIG  🛂")
        print("=" * 65)
        print("Sector security forces have flagged your transport for scanning")
        
        has_contraband = player.rig.cargo["Neural Stims"] > 0
        
        if has_contraband:
            print(f"\n{CLR['RED']}🚨 WARNING 🚨: You are carrying highly illegal Neural Stims 🚨!!!{CLR['RESET']}")
            print("[1] Attempt to bribe the officers ($1,500)")
            print("[2] Submit to the scanner matrix (Risk seizure and massive fine)")
        else:
            print(f"\n{CLR['GREEN']}💯 Your cargo manifest appears entirely legal 💯{CLR['RESET']}")
            print()
            print("[1] Cooperate fully and pay basic transit tariff ($300 USDC)")
            print("[2] Argue administrative technicalities (Risk delay/fines)")

        choice = input("\nAction >> ").strip()

        if has_contraband:
            if choice == "1" and player.cash >= 1500:
                player.cash -= 1500
                self.active_event_text = "🛂 CUSTOMS 🛂: Paid a $1,500 bribe. The guards looked the other way."
            else:
                # Caught red-handed!
                stims_count = player.rig.cargo["Neural Stims"]
                fine = stims_count * 2000 + 1000
                player.rig.cargo["Neural Stims"] = 0
                player.cash = max(0, player.cash - fine)
                self.active_event_text = f"🚨 BUSTED 🚨: Customs seized {stims_count}x Neural Stims and fined you ${fine} USDC!"
        else:
            if choice == "2" and random.random() < 0.5:
                self.active_event_text = "🛂 CUSTOMS 🛂: Your administrative arguments worked. No fees charged!"
            else:
                fee = 300 if choice == "1" else 600
                player.cash = max(0, player.cash - fee)
                self.active_event_text = f"🛂 CUSTOMS 🛂: Processed checkpoint clearance. Paid tariff fees of ${fee} USDC."
        time.sleep(1)

    def trigger_black_market_dealer(self, player):
        if player.rig.free_cargo < 1:
            return # No room for shady deals
            
        self.clear_screen()
        print("=" * 70)
        print("🛸 BACK-ALLEY INTERCEPT: SHADY DEALER")
        print("=" * 70)
        print("An unmarked stealth hauler hails your comms channel, offering an off-market asset.")
        print(f"They offer 1 Unit of [Neural Stims] for an absolute steal of $1200 USDC")
        print(f"Current Cargo Space: {player.rig.free_cargo}/{player.rig.max_cargo}")
        print(f"Current Liquid Cash: ${player.cash} USDC")
        print("\n[1] Purchase the contraband ($1200 USDC)")
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
        print("=" * 65)
        print("🏴‍☠️ WARNING: EMERGENCE PROTOCOL - RADAR LOCK")
        print("=" * 65)
        print("A band of sector raiders has cornered your rig in deep transit space!")
        print("They demand a corporate tribute or threaten total structural disassembly.")
        print("\n[1] Pay extortion tribute ($2,000 USDC)")
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
