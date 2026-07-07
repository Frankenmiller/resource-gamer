#!/usr/bin/env python3
import random
import os
import sys
import time

# ============================================================================
# CONFIGURATION & CONSTANTS
# ============================================================================
HUBS = ["Neo-Chicago", "Detroit Foundry", "Austin Megaplex", "Silicon Valley", "New Orleans Port"]

COMMODITIES = {
    "Fuel Cells":  {"base_price": 50,  "volatility": 0.15, "weight": 1},
    "Heavy Metals": {"base_price": 120, "volatility": 0.25, "weight": 3},
    "Biotech Meds": {"base_price": 450, "volatility": 0.40, "weight": 1},
    "Cybernetics": {"base_price": 800, "volatility": 0.30, "weight": 2},
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
        # Current Stats
        self.max_cargo = max_cargo
        self.max_fuel = max_fuel
        self.fuel = max_fuel
        self.condition = 100.0  # Percentage
        self.cargo = {comm: 0 for comm in COMMODITIES}
        
        # Upgrade Tiers (Level 1 is baseline)
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


# ============================================================================
# SYSTEM ENGINE CLASSES
# ============================================================================

class EventEngine:
    def __init__(self):
        self.active_global_modifier = 1.0
        self.active_event_text = "Markets are calm across the sectors."
        self.market_modifier_name = "Stable"

    def roll_turn_event(self, player, markets):
        """Triggers turn-by-turn events impacting the player or global markets."""
        ...  # (rest of body, indented one level under the class)
        roll = random.random()
        # Reset turn defaults
        self.active_global_modifier = 1.0
        self.market_modifier_name = "Stable"
        self.active_event_text = "Markets are calm across the sectors."

        if roll < 0.12:
            self.active_event_text = "⚠️ CRISIS: Solar flare causes supply chain blockages! High-tech prices soaring."
            self.active_global_modifier = 1.6
            self.market_modifier_name = "Supply Crunch"
            
        elif roll < 0.24:
            self.active_event_text = "📉 GLUT: A massive corporate asset liquidation floods regional markets!"
            self.active_global_modifier = 0.5
            self.market_modifier_name = "Resource Glut"
        
        elif roll < 0.35:
            base_damage = random.randint(15, 30)
            # Apply armor damage reduction math
            reduction = base_damage * player.rig.damage_reduction
            final_damage = max(0, int(base_damage - reduction))
            
            player.rig.condition = max(0, player.rig.condition - final_damage)
            self.active_event_text = f"⚙️ BREAKDOWN: Coolant manifold blew. Armor absorbed {int(reduction)}% damage. Rig took -{final_damage}% Condition."            

        elif roll < 0.45:
            fine = random.randint(300, 700)
            self.active_event_text = f"🛂 CUSTOMS: Border patrols hit you with transit tariffs. Cost you ${fine}."
            player.cash = max(0, player.cash - fine)
            
        elif roll < 0.55:
            found_cash = random.randint(400, 1000)
            self.active_event_text = f"💰 WINDFALL: You recovered abandoned corporate scrap! Scrapped for ${found_cash}."
            player.cash += found_cash

        # CRITICAL REFACTOR: Update all markets respecting local identities
        for market in markets.values():
            if market.name == player.current_hub and self.market_modifier_name != "Stable":
                # The local market is directly rocked by the global market event multiplier
                market.randomize_market(self.active_global_modifier, self.market_modifier_name)
            else:
                # Other hubs experience routine baseline shifts relative to their archetype
                market.randomize_market(1.0, "Stable")


class GameEngine:
    def __init__(self):
        self.player = Player()
        self.markets = {hub: Market(hub) for hub in HUBS}
        self.events = EventEngine()
        self.running = True

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def draw_header(self):
        self.clear_screen()
        p = self.player
        r = p.rig
        print("=" * 70)
        print(f" OPERATOR: {p.name:<15} | DAY: {p.days_elapsed:<3} | LOCATION: {p.current_hub}")
        print(f" CASH: ${p.cash:<18} | FUEL: {r.fuel}/{r.max_fuel}L | RIG COND: {r.condition:.1f}%")
        print(f" CARGO SPACE: {r.free_cargo}/{r.max_cargo} Units Free")
        print("=" * 70)
        print(f" LOG: {self.events.active_event_text}")
        print("=" * 70)

    def display_market(self):
        current_market = self.markets[self.player.current_hub]
        print(f"\n--- {current_market.name} Exchange [Status: {current_market.current_modifier}] ---")
        print(f"{'Commodity':<18} | {'Price':<8} | {'Weight (U)':<10} | {'In Cargo':<8}")
        print("-" * 50)
        for comm, price in current_market.prices.items():
            qty = self.player.rig.cargo[comm]
            weight = COMMODITIES[comm]['weight']
            print(f"{comm:<18} | ${price:<7} | {weight:<10} | {qty:<8}")
        print("-" * 50)

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
            time.sleep(1.5)
            return

        print(f"How many {commodity} to buy? (Max: {max_purchasable})")
        qty_input = input(">> ").strip()
        if not qty_input.isdigit(): return
        qty = int(qty_input)

        if 0 < qty <= max_purchasable:
            self.player.cash -= qty * price
            self.player.rig.cargo[commodity] += qty
            print(f"🟩 Successfully purchased {qty}x {commodity}.")
            time.sleep(1)

    def handle_sell(self):
        current_market = self.markets[self.player.current_hub]
        print("\nSelect item to SELL (or press Enter to cancel):")
        comms_list = [c for c in COMMODITIES.keys() if self.player.rig.cargo[c] > 0]
        
        if not comms_list:
            print("You have no cargo to sell.")
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

        print(f"How many {commodity} to sell? (Max: {max_sell})")
        qty_input = input(">> ").strip()
        if not qty_input.isdigit(): return
        qty = int(qty_input)

        if 0 < qty <= max_sell:
            self.player.cash += qty * price
            self.player.rig.cargo[commodity] -= qty
            print(f"🟨 Successfully sold {qty}x {commodity}.")
            time.sleep(1)

    def handle_travel(self):
        print("\nSelect destination hub to route flight plan:")
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
            print(f"❌ Not enough fuel to complete jump! Needs {fuel_cost}L.")
            time.sleep(1.5)
            return
        if self.player.rig.condition <= 0:
            print("❌ Rig is completely disabled. Repair required!")
            time.sleep(1.5)
            return

        # Execute travel overhead deductions using dynamic value
        self.player.rig.fuel -= fuel_cost
        self.player.rig.condition = max(0, self.player.rig.condition - 5)
        self.player.current_hub = destination
        self.player.days_elapsed += 1

        # Run random engine ticks upon new day jump
        self.events.roll_turn_event(self.player, self.markets)
        print(f"🚀 Jumping through transit lanes to {destination}...")
        time.sleep(1.5)

    def handle_maintenance(self):
        r = self.player.rig
        fuel_needed = r.max_fuel - r.fuel
        fuel_cost = fuel_needed * 4
        repair_needed = 100 - r.condition
        repair_cost = int(repair_needed * 30)

        print(f"\n--- Maintenance Bay ---")
        print(f"[1] Top off Fuel (+{fuel_needed}L)  -->  ${fuel_cost}")
        print(f"[2] Structural Repairs (+{repair_needed:.1f}%) -->  ${repair_cost}")
        print("[Press Enter to Return]")

        choice = input(">> ").strip()
        if choice == "1" and fuel_needed > 0:
            if self.player.cash >= fuel_cost:
                self.player.cash -= fuel_cost
                r.fuel = r.max_fuel
                print("Fuel tanks full.")
            else:
                print("Insufficient cash.")
            time.sleep(1)
        elif choice == "2" and repair_needed > 0:
            if self.player.cash >= repair_cost:
                self.player.cash -= repair_cost
                r.condition = 100.0
                print("Chassis structural integrity restored.")
            else:
                print("Insufficient cash.")
            time.sleep(1)

    def run(self):
        """Main operational execution loop."""
        while self.running:
            self.draw_header()
            self.display_market()
            
            print("\n[B]uy Cargo  |  [S]ell Cargo  |  [T]ravel to Hub  |  [M]aintenance  |  [Q]uit Game")
            action = input("Command >> ").strip().lower()

            if action == 'b':
                self.handle_buy()
            elif action == 's':
                self.handle_sell()
            elif action == 't':
                self.handle_travel()
            elif action == 'm':
                self.handle_maintenance()
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
