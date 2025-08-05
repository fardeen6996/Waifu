import streamlit as st
import random

# Game classes from the original code
ROLES = ["War", "Production", "Support"]

class Ability:
    def __init__(self, name, role, cost=1, effect_type="damage"):
        self.name = name
        self.role = role  # War, Production, or Support
        self.cost = cost  # Production points required
        self.effect_type = effect_type  # damage, buff, heal
        self.value = random.randint(15, 25) if effect_type == "damage" else random.randint(1, 3)

    def __str__(self):
        return f"{self.role} ability: {self.name} (Cost: {self.cost})"

class Waifu:
    def __init__(self, name, specialty):
        self.name = name
        self.specialty = specialty  # One of the roles
        self.stats = {"War": 8, "Production": 8, "Support": 8}
        self.speed = random.randint(85, 115)  # Random speed for turn order
        self.abilities = self._generate_abilities(name)
        self.current_position = None  # Position in battle grid
        self.hp = 100  # Health points
        self.max_hp = 100
    
    def _generate_abilities(self, name):
        """Generate unique abilities for each character"""
        ability_templates = {
            "War": [
                ("Strike", "damage", 2), ("Defend", "heal", 1), 
                ("Charge", "damage", 3), ("Rally", "buff", 2)
            ],
            "Production": [
                ("Craft", "buff", 1), ("Build", "buff", 2), 
                ("Gather", "buff", 1), ("Forge", "buff", 3)
            ],
            "Support": [
                ("Heal", "heal", 2), ("Boost", "buff", 1), 
                ("Shield", "buff", 2), ("Inspire", "buff", 3)
            ]
        }
        
        abilities = {}
        for role in ROLES:
            templates = ability_templates[role]
            # Pick 2 random abilities for each role
            selected = random.sample(templates, 2)
            abilities[role] = [
                Ability(f"{name}'s {selected[0][0]}", role, selected[0][2], selected[0][1]),
                Ability(f"{name}'s {selected[1][0]}", role, selected[1][2], selected[1][1])
            ]
        return abilities

    def get_stat(self, current_slot):
        base = self.stats[current_slot]
        if current_slot == self.specialty:
            return base + 1
        return base

    def get_active_abilities(self, slot):
        return self.abilities[slot]

    def __str__(self):
        return f"{self.name} ({self.specialty}) - W:{self.stats['War']} P:{self.stats['Production']} S:{self.stats['Support']}"

class Player:
    def __init__(self, name):
        self.name = name
        self.waifus = []
        self.production_points = 5  # Start with some points
        self.production_rate = 0  # Points per turn from production waifus

    def add_waifu(self, waifu):
        self.waifus.append(waifu)
    
    def calculate_production_rate(self):
        """Calculate production points generated per turn"""
        base_rate = 0
        for waifu in self.waifus:
            if waifu.specialty == "Production" and waifu.hp > 0:
                base_rate += 2  # Base production per production waifu
        self.production_rate = base_rate
        return base_rate
    
    def generate_production_points(self):
        """Generate production points at start of turn"""
        generated = self.calculate_production_rate()
        self.production_points += generated
        return generated

# Initialize session state
def init_session_state():
    if 'game_phase' not in st.session_state:
        st.session_state.game_phase = 'start'  # start, team_selection, gameplay, game_over
    if 'current_player' not in st.session_state:
        st.session_state.current_player = 1
    if 'current_turn' not in st.session_state:
        st.session_state.current_turn = 1
    if 'max_turns' not in st.session_state:
        st.session_state.max_turns = 5
    if 'players' not in st.session_state:
        st.session_state.players = [Player("Player 1"), Player("Player 2")]
    if 'available_waifus' not in st.session_state:
        st.session_state.available_waifus = [
            # War specialists
            Waifu("Mary", "War"),
            Waifu("Ivy", "War"),
            Waifu("Rei", "War"),
            Waifu("Zara", "War"),
            Waifu("Akira", "War"),
            Waifu("Blade", "War"),
            
            # Production specialists
            Waifu("Luna", "Production"),
            Waifu("Kira", "Production"),
            Waifu("Mira", "Production"),
            Waifu("Sage", "Production"),
            Waifu("Ava", "Production"),
            Waifu("Echo", "Production"),
            
            # Support specialists
            Waifu("Sora", "Support"),
            Waifu("Nova", "Support"),
            Waifu("Lily", "Support"),
            Waifu("Rose", "Support"),
            Waifu("Hope", "Support"),
            Waifu("Grace", "Support")
        ]
    if 'role_counts' not in st.session_state:
        st.session_state.role_counts = [
            {"War": 0, "Production": 0, "Support": 0},
            {"War": 0, "Production": 0, "Support": 0}
        ]
    if 'battle_grid' not in st.session_state:
        st.session_state.battle_grid = {
            'player1': [None, None, None, None, None],  # 5 positions for each player
            'player2': [None, None, None, None, None]
        }
    if 'turn_order' not in st.session_state:
        st.session_state.turn_order = []
    if 'current_battle_turn' not in st.session_state:
        st.session_state.current_battle_turn = 0
    if 'battle_phase' not in st.session_state:
        st.session_state.battle_phase = 'position'  # position, battle

def get_available_waifus_for_player(player_idx):
    """Get waifus not selected by any player"""
    selected_waifus = []
    for player in st.session_state.players:
        selected_waifus.extend([w.name for w in player.waifus])
    
    return [w for w in st.session_state.available_waifus if w.name not in selected_waifus]

def display_waifu_list(waifus, current_player, current_player_idx, role_count, tab_prefix=""):
    """Display a list of waifus with selection buttons"""
    if not waifus:
        st.write("No waifus available in this category.")
        return
    
    for waifu in waifus:
        col1, col2, col3, col4 = st.columns([2, 1, 2, 1])
        with col1:
            st.write(f"**{waifu.name}**")
        with col2:
            # Role emoji
            role_emoji = {"War": "⚔️", "Production": "🏭", "Support": "🛡️"}
            st.write(f"{role_emoji[waifu.specialty]} {waifu.specialty}")
        with col3:
            stat = waifu.get_stat(waifu.specialty)
            st.write(f"Stat: {stat}")
        with col4:
            # Check if player can select this role
            can_select = role_count[waifu.specialty] < 3
            if st.button(f"Select", key=f"select_{tab_prefix}_{waifu.name}_{current_player_idx}", disabled=not can_select):
                current_player.add_waifu(waifu)
                st.session_state.role_counts[current_player_idx][waifu.specialty] += 1
                st.rerun()
            
            if not can_select:
                st.caption("Max 3 per role")

def setup_battle_grid():
    """Initialize battle positions for both players in FIFA-style formation"""
    # Place waifus organized by role for formation display
    for i, player in enumerate(st.session_state.players):
        player_key = f'player{i+1}'
        
        # Group waifus by role
        waifus_by_role = {"War": [], "Production": [], "Support": []}
        for waifu in player.waifus:
            waifus_by_role[waifu.specialty].append(waifu)
        
        # Flatten back to grid in role order for storage
        grid_waifus = []
        for role in ["War", "Production", "Support"]:
            grid_waifus.extend(waifus_by_role[role])
        
        # Fill the grid
        for j, waifu in enumerate(grid_waifus):
            st.session_state.battle_grid[player_key][j] = waifu
            waifu.current_position = j
        
        # Fill remaining slots with None
        for j in range(len(grid_waifus), 5):
            st.session_state.battle_grid[player_key][j] = None

def calculate_turn_order():
    """Calculate turn order based on speed"""
    all_waifus = []
    for player_idx, player in enumerate(st.session_state.players):
        for waifu in player.waifus:
            all_waifus.append((waifu, player_idx))
    
    # Sort by speed (highest first)
    all_waifus.sort(key=lambda x: x[0].speed, reverse=True)
    st.session_state.turn_order = all_waifus

def get_waifu_color(specialty):
    """Get color for waifu based on specialty"""
    colors = {
        "War": "#ff4444",      # Red
        "Production": "#ff8844", # Orange  
        "Support": "#4444ff"    # Blue
    }
    return colors.get(specialty, "#888888")

def start_screen():
    # Custom title with styling
    st.markdown('<h1 class="main-title">🎮 WAIFU BATTLE ARENA</h1>', unsafe_allow_html=True)
    
    # Game description with custom styling
    st.markdown("""
    <div style="text-align: center; font-family: 'Courier New', monospace; font-size: 1.2rem; margin: 2rem 0;">
        Welcome to the ultimate tactical battle experience!
    </div>
    """, unsafe_allow_html=True)
    
    # Rules in styled containers
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="battle-card war-card">
            <h3>⚔️ COMBAT</h3>
            <p>Strategic turn-based battles with speed-based action order</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="battle-card production-card">
            <h3>🏭 PRODUCTION</h3>
            <p>Manage production points to fuel powerful abilities</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="battle-card support-card">
            <h3>🛡️ SUPPORT</h3>
            <p>Heal allies and boost team effectiveness</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Game rules
    st.markdown("""
    <div style="background: linear-gradient(145deg, #2a2a2a, #1e1e1e); 
                 border: 1px solid #444; border-radius: 15px; padding: 20px; 
                 font-family: 'Courier New', monospace; margin: 20px 0;">
        <h3 style="color: #ff6b6b; text-align: center;">BATTLE RULES</h3>
        <ul style="color: #ffffff; font-size: 1.1rem;">
            <li>🎯 Each player builds a team of 5 waifus</li>
            <li>⚖️ Maximum 3 waifus per role (War/Production/Support)</li>
            <li>💰 Production waifus generate points for abilities</li>
            <li>⚡ Turn order determined by speed stats</li>
            <li>🏆 Battle until one team is defeated</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Start button
    if st.button("🚀 ENTER BATTLE", use_container_width=True):
        st.session_state.game_phase = 'team_selection'
        st.session_state.current_player = 1
        st.rerun()

def team_selection_screen():
    current_player_idx = st.session_state.current_player - 1
    current_player = st.session_state.players[current_player_idx]
    
    player_color = "🔵" if current_player_idx == 0 else "🔴"
    st.markdown(f'<h1 class="main-title">{player_color} {current_player.name.upper()} - TEAM SELECTION</h1>', unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="text-align: center; font-family: 'Courier New', monospace; font-size: 1.3rem; 
                 color: #ff6b6b; margin: 1rem 0;">
        SELECT 5 WAIFUS FOR YOUR TEAM ({len(current_player.waifus)}/5)
    </div>
    """, unsafe_allow_html=True)
    
    # Show current team
    if current_player.waifus:
        st.markdown("### 🌟 Your Team:")
        for i, waifu in enumerate(current_player.waifus):
            col1, col2, col3 = st.columns([2, 1, 2])
            with col1:
                st.write(f"**{waifu.name}**")
            with col2:
                st.write(f"*{waifu.specialty}*")
            with col3:
                stat = waifu.get_stat(waifu.specialty)
                st.write(f"Stat: {stat}")
    
    # Show role counts
    role_count = st.session_state.role_counts[current_player_idx]
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("⚔️ War", f"{role_count['War']}/3")
    with col2:
        st.metric("🏭 Production", f"{role_count['Production']}/3")
    with col3:
        st.metric("🛡️ Support", f"{role_count['Support']}/3")
    
    # Show available waifus
    if len(current_player.waifus) < 5:
        st.markdown("### 📋 Available Waifus:")
        available = get_available_waifus_for_player(current_player_idx)
        
        # Filter by role tabs
        tab1, tab2, tab3, tab4 = st.tabs(["All", "⚔️ War", "🏭 Production", "🛡️ Support"])
        
        with tab1:
            st.markdown("**All Available Characters:**")
            display_waifu_list(available, current_player, current_player_idx, role_count, "all")
        
        with tab2:
            war_waifus = [w for w in available if w.specialty == "War"]
            st.markdown(f"**War Specialists ({len(war_waifus)} available):**")
            display_waifu_list(war_waifus, current_player, current_player_idx, role_count, "war")
        
        with tab3:
            prod_waifus = [w for w in available if w.specialty == "Production"]
            st.markdown(f"**Production Specialists ({len(prod_waifus)} available):**")
            display_waifu_list(prod_waifus, current_player, current_player_idx, role_count, "prod")
        
        with tab4:
            support_waifus = [w for w in available if w.specialty == "Support"]
            st.markdown(f"**Support Specialists ({len(support_waifus)} available):**")
            display_waifu_list(support_waifus, current_player, current_player_idx, role_count, "support")
    
    # Progress to next phase
    if len(current_player.waifus) == 5:
        if st.session_state.current_player == 1:
            if st.button("✅ Confirm Team & Continue to Player 2", use_container_width=True):
                st.session_state.current_player = 2
                st.rerun()
        else:
            if st.button("🎮 Start Battle!", use_container_width=True):
                st.session_state.game_phase = 'battle_setup'
                st.session_state.current_player = 1
                st.session_state.battle_phase = 'position'
                setup_battle_grid()
                st.rerun()

def battle_setup_screen():
    """Screen for positioning waifus before battle"""
    st.markdown('<h1 class="main-title">⚔️ BATTLE SETUP</h1>', unsafe_allow_html=True)
    
    if st.session_state.battle_phase == 'position':
        st.markdown("### 📋 Team Positioning")
        st.markdown("Your waifus are automatically positioned by role. Ready to battle?")
        
        # Display battle formation and action order
        st.markdown("### ⚔️ Battle Formation")
        
        col_battle, col_action_bar = st.columns([3, 1])
        
        with col_battle:
            display_battle_grid_vertical()
        
        with col_action_bar:
            calculate_turn_order()
            display_action_order_bar()
        
        # Start battle button
        if st.button("🚀 Start Battle!", use_container_width=True):
            st.session_state.battle_phase = 'battle'
            st.session_state.current_battle_turn = 0
            st.session_state.game_phase = 'battle'
            st.rerun()

def display_battle_grid_vertical():
    """Display the vertical battle grid with FIFA-style formation layout"""
    # Player 2 at top (opponent) - reversed formation
    st.markdown("#### 🔴 Player 2")
    grid2 = st.session_state.battle_grid['player2']
    display_formation_layout(grid2, player_idx=1, reverse=True)
    
    # Empty space between formations
    st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)
    
    # Player 1 at bottom (you)
    st.markdown("#### 🔵 Player 1")
    grid1 = st.session_state.battle_grid['player1']
    display_formation_layout(grid1, player_idx=0, reverse=False)

def display_formation_layout(grid, player_idx, reverse=False):
    """Display waifus in FIFA-style formation based on roles"""
    # Get waifus and group by role
    waifus_by_role = {"War": [], "Production": [], "Support": []}
    for waifu in grid:
        if waifu:
            waifus_by_role[waifu.specialty].append(waifu)
    
    # Define formation order (normal or reversed)
    role_order = ["Support", "Production", "War"] if reverse else ["War", "Production", "Support"]
    
    for role in role_order:
        waifus_in_role = waifus_by_role[role]
        if waifus_in_role:
            # Display role row with centering
            cols = st.columns([1, 2, 1])  # Add padding columns for centering
            with cols[1]:
                role_cols = st.columns(len(waifus_in_role))
                for i, waifu in enumerate(waifus_in_role):
                    with role_cols[i]:
                        display_waifu_card(waifu, waifu.specialty)
        else:
            # Display empty role indication
            display_empty_role_row(role)

def display_waifu_card(waifu, slot):
    """Display a waifu card with role-specific styling"""
    if not waifu:
        return
    
    # Get role-specific colors and emojis
    role_colors = {
        "War": "#ff4444",      # Red
        "Production": "#ff8844", # Orange
        "Support": "#4444ff"    # Blue
    }
    
    role_emoji = {"War": "⚔️", "Production": "🏭", "Support": "🛡️"}
    
    color = role_colors.get(slot, "#888888")
    emoji = role_emoji.get(slot, "❓")
    
    # Health bar color
    hp_percentage = (waifu.hp / waifu.max_hp) * 100
    if hp_percentage > 60:
        health_color = "#4CAF50"
    elif hp_percentage > 30:
        health_color = "#FF9800"
    else:
        health_color = "#F44336"
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(145deg, {color}, {color}cc);
        border: 2px solid #333;
        border-radius: 15px;
        padding: 15px;
        text-align: center;
        color: white;
        font-weight: bold;
        font-family: 'Courier New', monospace;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        margin: 8px;
        min-height: 120px;
    ">
        <div style="font-size: 20px; margin-bottom: 5px;">{emoji}</div>
        <div style="font-size: 14px; margin-bottom: 5px;">{waifu.name}</div>
        <div style="font-size: 12px; margin-bottom: 5px;">SPD: {waifu.speed}</div>
        <div style="background: #333; border-radius: 10px; height: 8px; margin: 5px 0;">
            <div style="background: {health_color}; height: 100%; width: {hp_percentage}%; border-radius: 10px;"></div>
        </div>
        <div style="font-size: 10px;">{waifu.hp}/{waifu.max_hp} HP</div>
    </div>
    """, unsafe_allow_html=True)

def display_empty_role_row(role):
    """Display an empty row for a role with no waifus"""
    role_emoji = {"War": "⚔️", "Production": "🏭", "Support": "🛡️"}
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(145deg, #2a2a2a, #1e1e1e);
        border: 2px dashed #444;
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        color: #666;
        margin: 8px;
        font-family: 'Courier New', monospace;
    ">
        <div style="font-size: 20px;">{role_emoji[role]}</div>
        <div>No {role} Units</div>
    </div>
    """, unsafe_allow_html=True)

def display_action_order_bar():
    """Display the vertical action order bar like HSR"""
    st.markdown("""
    <div style="text-align: center; color: #ff6b6b; font-weight: bold; 
                font-family: 'Courier New', monospace; margin-bottom: 15px;">
        ⚡ ACTION ORDER
    </div>
    """, unsafe_allow_html=True)
    
    # Get current turn order
    if not st.session_state.turn_order:
        calculate_turn_order()
    
    # Display each character in turn order
    for i, (waifu, player_idx) in enumerate(st.session_state.turn_order):
        player_color = "#4488ff" if player_idx == 0 else "#ff4444"
        player_symbol = "🔵" if player_idx == 0 else "🔴"
        role_emoji = {"War": "⚔️", "Production": "🏭", "Support": "🛡️"}
        
        # Highlight current turn
        is_current = i == st.session_state.current_battle_turn
        border_color = "#ffff00" if is_current else "#333"
        glow = "box-shadow: 0 0 15px rgba(255, 255, 0, 0.8);" if is_current else ""
        
        st.markdown(f"""
        <div style="
            background: linear-gradient(145deg, {player_color}, {player_color}cc);
            border: 2px solid {border_color};
            border-radius: 10px;
            padding: 8px;
            margin: 5px 0;
            text-align: center;
            color: white;
            font-weight: bold;
            font-family: 'Courier New', monospace;
            font-size: 11px;
            {glow}
            {'transform: scale(1.05);' if is_current else ''}
        ">
            <div style="font-size: 14px;">{role_emoji[waifu.specialty]}</div>
            <div style="font-size: 12px;">{waifu.name}</div>
            <div style="font-size: 10px;">SPD: {waifu.speed}</div>
            <div style="font-size: 10px;">{player_symbol}</div>
            {'<div style="color: #ffff00; font-size: 10px;">◄ ACTIVE</div>' if is_current else ''}
        </div>
        """, unsafe_allow_html=True)

def battle_screen():
    """Main battle screen with turn-based combat"""
    st.markdown('<h1 class="main-title">⚔️ BATTLE IN PROGRESS</h1>', unsafe_allow_html=True)
    
    # Check for game over
    if check_game_over():
        return
    
    # Get current turn info
    current_waifu, current_player_idx = st.session_state.turn_order[st.session_state.current_battle_turn]
    current_player = st.session_state.players[current_player_idx]
    
    # Generate production points at start of turn
    if st.session_state.current_battle_turn == 0 or \
       st.session_state.turn_order[st.session_state.current_battle_turn - 1][1] != current_player_idx:
        generated = current_player.generate_production_points()
        if generated > 0:
            st.success(f"💰 {current_player.name} generated {generated} production points!")
    
    # Display current turn info
    player_color = "🔵" if current_player_idx == 0 else "🔴"
    st.markdown(f"### {player_color} {current_player.name}'s Turn")
    st.markdown(f"**Active Waifu:** {current_waifu.name} ({current_waifu.specialty})")
    
    # Display production points
    col1, col2 = st.columns(2)
    with col1:
        st.metric("💰 Production Points", current_player.production_points)
    with col2:
        st.metric("⚡ Production Rate", f"{current_player.calculate_production_rate()}/turn")
    
    # Display battle grid and turn order side by side
    st.markdown("---")
    col_battle, col_action_bar = st.columns([3, 1])
    
    with col_battle:
        display_battle_grid_vertical()
    
    with col_action_bar:
        display_action_order_bar()
    
    st.markdown("---")
    
    # Show available abilities for current waifu
    abilities = current_waifu.get_active_abilities(current_waifu.specialty)
    st.markdown(f"### ⚡ {current_waifu.name}'s Abilities:")
    
    # Ability buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        for i, ability in enumerate(abilities):
            can_afford = current_player.production_points >= ability.cost
            if st.button(f"💥 {ability.name} (Cost: {ability.cost})", 
                        key=f"ability_{i}", 
                        disabled=not can_afford,
                        use_container_width=True):
                use_ability(ability, current_waifu, current_player_idx)
    
    with col2:
        if st.button("🔄 Basic Attack", use_container_width=True):
            basic_attack(current_waifu, current_player_idx)
    
    with col3:
        if st.button("⏭️ Skip Turn", use_container_width=True):
            next_turn()
    
    # Show ability details
    st.markdown("#### Ability Details:")
    for ability in abilities:
        cost_color = "🟢" if current_player.production_points >= ability.cost else "🔴"
        st.markdown(f"{cost_color} **{ability.name}** - Cost: {ability.cost} - Type: {ability.effect_type}")

def use_ability(ability, current_waifu, current_player_idx):
    """Use an ability in battle"""
    current_player = st.session_state.players[current_player_idx]
    
    # Check cost
    if current_player.production_points < ability.cost:
        st.error("Not enough production points!")
        return
    
    # Deduct cost
    current_player.production_points -= ability.cost
    
    # Apply ability effect
    if ability.effect_type == "damage":
        # Target enemy team
        enemy_player_idx = 1 - current_player_idx
        enemy_grid = st.session_state.battle_grid[f'player{enemy_player_idx + 1}']
        
        # Find alive enemies
        alive_enemies = [w for w in enemy_grid if w and w.hp > 0]
        if alive_enemies:
            target = random.choice(alive_enemies)
            damage = ability.value
            target.hp = max(0, target.hp - damage)
            st.success(f"💥 {current_waifu.name} used {ability.name}! {target.name} takes {damage} damage!")
    
    elif ability.effect_type == "heal":
        # Target ally team
        ally_grid = st.session_state.battle_grid[f'player{current_player_idx + 1}']
        injured_allies = [w for w in ally_grid if w and w.hp > 0 and w.hp < w.max_hp]
        if injured_allies:
            target = random.choice(injured_allies)
            heal = ability.value * 10  # Scale healing
            target.hp = min(target.max_hp, target.hp + heal)
            st.success(f"💚 {current_waifu.name} used {ability.name}! {target.name} heals {heal} HP!")
    
    elif ability.effect_type == "buff":
        st.success(f"✨ {current_waifu.name} used {ability.name}! Team receives buff!")
    
    next_turn()

def basic_attack(current_waifu, current_player_idx):
    """Perform a basic attack"""
    enemy_player_idx = 1 - current_player_idx
    enemy_grid = st.session_state.battle_grid[f'player{enemy_player_idx + 1}']
    
    # Find alive enemies
    alive_enemies = [w for w in enemy_grid if w and w.hp > 0]
    if alive_enemies:
        target = random.choice(alive_enemies)
        damage = random.randint(10, 20)
        target.hp = max(0, target.hp - damage)
        st.success(f"⚔️ {current_waifu.name} attacks {target.name} for {damage} damage!")
    
    next_turn()

def next_turn():
    """Advance to next turn"""
    st.session_state.current_battle_turn = (st.session_state.current_battle_turn + 1) % len(st.session_state.turn_order)
    st.rerun()

def check_game_over():
    """Check if the game is over"""
    for player_idx, player in enumerate(st.session_state.players):
        alive_count = sum(1 for w in player.waifus if w.hp > 0)
        if alive_count == 0:
            winner_idx = 1 - player_idx
            winner = st.session_state.players[winner_idx]
            st.success(f"🏆 {winner.name} WINS!")
            
            if st.button("🔄 Play Again"):
                # Reset game state
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
            return True
    return False

def apply_custom_css():
    """Apply custom dark theme CSS"""
    st.markdown("""
    <style>
        .main-title {
            text-align: center;
            color: #ff6b6b;
            font-family: 'Courier New', monospace;
            font-size: 2.5rem;
            font-weight: bold;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
            margin-bottom: 2rem;
        }
        
        .battle-card {
            background: linear-gradient(145deg, #2a2a2a, #1e1e1e);
            border: 2px solid #444;
            border-radius: 15px;
            padding: 20px;
            margin: 10px;
            text-align: center;
            font-family: 'Courier New', monospace;
            color: white;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        }
        
        .war-card {
            border-color: #ff4444;
        }
        
        .production-card {
            border-color: #ff8844;
        }
        
        .support-card {
            border-color: #4444ff;
        }
        
        .battle-card h3 {
            margin-top: 0;
            color: #ff6b6b;
        }
        
        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Custom button styling */
        .stButton > button {
            background: linear-gradient(145deg, #444444, #333333);
            color: white;
            border: 2px solid #666;
            border-radius: 10px;
            font-family: 'Courier New', monospace;
            font-weight: bold;
        }
        
        .stButton > button:hover {
            background: linear-gradient(145deg, #555555, #444444);
            border-color: #888;
        }
        
        /* Dark theme adjustments */
        .stApp {
            background-color: #1a1a1a;
        }
        
        .stMarkdown {
            color: #ffffff;
        }
    </style>
    """, unsafe_allow_html=True)

# Main application
def main():
    st.set_page_config(
        page_title="Waifu Battle Arena",
        page_icon="⚔️",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Apply custom styling
    apply_custom_css()
    
    # Initialize session state
    init_session_state()
    
    # Route to appropriate screen based on game phase
    if st.session_state.game_phase == 'start':
        start_screen()
    elif st.session_state.game_phase == 'team_selection':
        team_selection_screen()
    elif st.session_state.game_phase == 'battle_setup':
        battle_setup_screen()
    elif st.session_state.game_phase == 'battle':
        battle_screen()

if __name__ == "__main__":
    main()
