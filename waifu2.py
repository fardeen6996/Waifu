import streamlit as st
import random
import time

# -------------------- SETUP --------------------

st.set_page_config(layout="wide")

st.markdown(
    """
    <style>
    .title { font-size: 2.5em; font-weight: bold; text-align: center; }
    .subtitle { font-size: 1.5em; font-weight: bold; text-align: center; }
    .waifu-card {
        border: 2px solid #ddd;
        border-radius: 10px;
        padding: 10px;
        margin: 5px;
        text-align: center;
    }
    .war { background-color: #ffdddd; }
    .production { background-color: #ddffdd; }
    .support { background-color: #ddddff; }
    .turn-bar {
        display: flex;
        overflow-x: auto;
        padding: 10px;
        background: #f0f0f0;
        border-radius: 10px;
        margin-bottom: 15px;
    }
    .turn-box {
        flex: 0 0 auto;
        width: 120px;
        height: 120px;
        margin-right: 10px;
        padding: 10px;
        border-radius: 10px;
        text-align: center;
        font-size: 0.9em;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# -------------------- CLASSES --------------------

class Ability:
    def __init__(self, name, effect_type, cost, value):
        self.name = name
        self.effect_type = effect_type  # "damage", "heal", or "buff"
        self.cost = cost
        self.value = value

class Waifu:
    def __init__(self, name, role):
        self.name = name
        self.role = role
        self.hp = 100
        self.speed = random.randint(5, 15)
        self.abilities = self.generate_abilities()

    def generate_abilities(self):
        abilities = []
        if self.role == "War":
            abilities.append(Ability("💥 Strike", "damage", 3, random.randint(20, 30)))
        elif self.role == "Production":
            abilities.append(Ability("⚙️ Overdrive", "buff", 2, 0))
        elif self.role == "Support":
            abilities.append(Ability("💖 Heal", "heal", 4, random.randint(15, 25)))
        abilities.append(Ability("🌟 Inspire", "buff", 2, 0))
        return abilities

class Player:
    def __init__(self, name, is_ai=False):
        self.name = name
        self.is_ai = is_ai
        self.waifus = []
        self.production_points = 10
        self.production_rate = 3

# -------------------- INITIALIZATION --------------------

if "game_phase" not in st.session_state:
    st.session_state.game_phase = "start"

if "player1" not in st.session_state:
    st.session_state.player1 = Player("Player 1")
    st.session_state.player2 = Player("AI", is_ai=True)

if "selected_waifus" not in st.session_state:
    st.session_state.selected_waifus = []

# -------------------- FUNCTIONS --------------------

def generate_waifus():
    roles = ["War", "Production", "Support"]
    return [Waifu(f"Waifu {i+1}", random.choice(roles)) for i in range(15)]

def display_waifu_card(waifu):
    color_class = "war" if waifu.role == "War" else "production" if waifu.role == "Production" else "support"
    st.markdown(f"""
        <div class="waifu-card {color_class}">
            <b>{waifu.name}</b><br>
            Role: {waifu.role}<br>
            Speed: {waifu.speed}<br>
            HP: {waifu.hp}<br>
            Abilities:
            <ul>
                {''.join([f"<li>{a.name} ({a.effect_type}, cost {a.cost})</li>" for a in waifu.abilities])}
            </ul>
        </div>
        """, unsafe_allow_html=True)

def team_selection_phase():
    st.title("Team Selection Phase")
    st.markdown("Each player selects 5 waifus. Max 3 per role.")

    all_waifus = generate_waifus()

    roles = ["War", "Production", "Support"]
    role_counts = {"War": 0, "Production": 0, "Support": 0}
    player = st.session_state.player1

    st.subheader(f"{player.name} - Select Your Team")

    available_waifus = [w for w in all_waifus if w not in st.session_state.selected_waifus]
    for waifu in available_waifus:
        if st.button(f"Select {waifu.name} ({waifu.role})"):
            if len(player.waifus) < 5 and role_counts[waifu.role] < 3:
                player.waifus.append(waifu)
                st.session_state.selected_waifus.append(waifu)
                role_counts[waifu.role] += 1
                st.rerun()

    if len(player.waifus) == 5:
        # AI picks remaining 5
        ai = st.session_state.player2
        ai_pool = [w for w in all_waifus if w not in st.session_state.selected_waifus]
        ai_choices = random.sample(ai_pool, 5)
        ai.waifus = ai_choices
        st.session_state.selected_waifus.extend(ai_choices)
        st.success("AI has selected its waifus!")
        st.session_state.game_phase = "battle_setup"
        st.rerun()

def setup_battle():
    waifus = st.session_state.player1.waifus + st.session_state.player2.waifus
    waifus.sort(key=lambda w: w.speed, reverse=True)
    st.session_state.turn_order = [(w, st.session_state.player1 if w in st.session_state.player1.waifus else st.session_state.player2) for w in waifus]
    st.session_state.current_battle_turn = 0
    st.session_state.use_ability = False
    st.session_state.game_phase = "battle"

def display_action_order_bar():
    st.markdown('<div class="turn-bar">', unsafe_allow_html=True)
    for waifu, _ in st.session_state.turn_order:
        opacity = "0.3" if waifu.hp <= 0 else "1.0"
        st.markdown(f"""
        <div class="turn-box" style="background-color: {'#fdd' if waifu.role == 'War' else '#dfd' if waifu.role == 'Production' else '#ddf'}; opacity: {opacity};">
            <b>{waifu.name}</b><br>
            {waifu.role}<br>
            ❤️ {waifu.hp}<br>
            ⚡ {waifu.speed}
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def next_turn():
    while True:
        st.session_state.current_battle_turn = (st.session_state.current_battle_turn + 1) % len(st.session_state.turn_order)
        waifu, _ = st.session_state.turn_order[st.session_state.current_battle_turn]
        if waifu.hp > 0:
            break
    st.session_state.use_ability = False
    st.rerun()

def ai_take_turn(current_waifu, current_player):
    time.sleep(1.5)
    abilities = current_waifu.abilities
    ability = None

    # Try damage or heal first
    for a in abilities:
        if a.cost <= current_player.production_points and a.effect_type in ["damage", "heal"]:
            ability = a
            break

    if not ability:
        for a in abilities:
            if a.cost <= current_player.production_points:
                ability = a
                break

    if not ability:
        st.warning(f"{current_waifu.name} (AI) has no abilities to use!")
        next_turn()
        return

    targets = [w for w in st.session_state.player1.waifus if w.hp > 0] if ability.effect_type == "damage" else \
              [w for w in st.session_state.player2.waifus if w.hp > 0]
    if not targets:
        st.warning("No valid targets.")
        next_turn()
        return

    target = random.choice(targets)
    st.session_state.selected_ability = ability
    st.session_state.selected_target = target
    st.session_state.use_ability = True
    st.rerun()

def battle_phase():
    st.title("⚔️ Battle Phase")
    display_action_order_bar()

    current_waifu, current_player = st.session_state.turn_order[st.session_state.current_battle_turn]
    st.subheader(f"{current_player.name}'s turn - {current_waifu.name} ({current_waifu.role})")
    st.text(f"HP: {current_waifu.hp} | Production Points: {current_player.production_points}")

    if current_waifu.hp <= 0:
        next_turn()
        return

    if current_player.is_ai and not st.session_state.use_ability:
        ai_take_turn(current_waifu, current_player)
        return

    if not current_player.is_ai:
        for ability in current_waifu.abilities:
            if st.button(f"Use {ability.name} ({ability.effect_type}, Cost {ability.cost})"):
                st.session_state.selected_ability = ability
                st.session_state.use_ability = True
                st.rerun()

    if st.session_state.use_ability:
        ability = st.session_state.selected_ability
        targets = st.session_state.player2.waifus if ability.effect_type == "damage" else st.session_state.player1.waifus
        targets = [w for w in targets if w.hp > 0]

        if not current_player.is_ai:
            target = st.selectbox("Select Target", targets, format_func=lambda w: f"{w.name} ({w.hp} HP)")
            if st.button("Confirm"):
                if ability.effect_type == "damage":
                    target.hp -= ability.value
                    st.error(f"{current_waifu.name} used {ability.name} on {target.name} for {ability.value} damage!")
                elif ability.effect_type == "heal":
                    target.hp += ability.value
                    st.success(f"{current_waifu.name} healed {target.name} for {ability.value} HP!")
                current_player.production_points -= ability.cost
                current_player.production_points += current_player.production_rate
                next_turn()
        else:
            target = st.session_state.selected_target
            if ability.effect_type == "damage":
                target.hp -= ability.value
                st.error(f"{current_waifu.name} (AI) used {ability.name} on {target.name} for {ability.value} damage!")
            elif ability.effect_type == "heal":
                target.hp += ability.value
                st.success(f"{current_waifu.name} (AI) healed {target.name} for {ability.value} HP!")
            current_player.production_points -= ability.cost
            current_player.production_points += current_player.production_rate
            next_turn()

# -------------------- MAIN --------------------

if st.session_state.game_phase == "start":
    st.markdown("<div class='title'>🎴 Waifu Tactical Card Game</div>", unsafe_allow_html=True)
    if st.button("Start Game"):
        st.session_state.game_phase = "team_selection"
        st.rerun()

elif st.session_state.game_phase == "team_selection":
    team_selection_phase()

elif st.session_state.game_phase == "battle_setup":
    setup_battle()

elif st.session_state.game_phase == "battle":
    battle_phase()
