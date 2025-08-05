import streamlit as st
import random

# Add this new class for AI player
class AIPlayer(Player):
    def __init__(self, name):
        super().__init__(name)
        self.is_ai = True
    
    def select_team_automatically(self, available_waifus):
        """AI automatically selects a balanced team"""
        # Strategy: Try to get a balanced team with variety
        selected = []
        role_counts = {"War": 0, "Production": 0, "Support": 0}
        
        # Shuffle available waifus for randomness
        shuffled_waifus = available_waifus.copy()
        random.shuffle(shuffled_waifus)
        
        # First, try to get at least one of each role
        for role in ["War", "Production", "Support"]:
            role_waifus = [w for w in shuffled_waifus if w.specialty == role and w not in selected]
            if role_waifus and role_counts[role] < 3:
                selected.append(role_waifus[0])
                role_counts[role] += 1
        
        # Fill remaining slots, preferring balanced distribution
        while len(selected) < 5:
            # Find roles that aren't at max capacity
            available_roles = [role for role in ["War", "Production", "Support"] if role_counts[role] < 3]
            if not available_roles:
                break
                
            # Pick a random available role
            target_role = random.choice(available_roles)
            role_waifus = [w for w in shuffled_waifus if w.specialty == target_role and w not in selected]
            
            if role_waifus:
                selected.append(role_waifus[0])
                role_counts[target_role] += 1
        
        # Add selected waifus to team
        for waifu in selected:
            self.add_waifu(waifu)
        
        return role_counts
    
    def choose_battle_action(self, current_waifu):
        """AI chooses what action to take in battle"""
        abilities = current_waifu.get_active_abilities(current_waifu.specialty)
        
        # Strategy priority:
        # 1. Use healing if allies are low HP
        # 2. Use damage abilities if we have points
        # 3. Use basic attack otherwise
        
        # Check if any allies need healing
        ally_grid = st.session_state.battle_grid['player2']
        injured_allies = [w for w in ally_grid if w and w.hp > 0 and w.hp < w.max_hp * 0.5]
        
        # Check available abilities
        affordable_abilities = [a for a in abilities if self.production_points >= a.cost]
        
        # Decision logic
        if injured_allies and current_waifu.specialty == "Support":
            # Prioritize healing if Support and allies are hurt
            heal_abilities = [a for a in affordable_abilities if a.effect_type == "heal"]
            if heal_abilities:
                return ("ability", random.choice(heal_abilities))
        
        # Use damage abilities if available and affordable
        damage_abilities = [a for a in affordable_abilities if a.effect_type == "damage"]
        if damage_abilities and self.production_points >= 2:  # Save some points
            return ("ability", random.choice(damage_abilities))
        
        # Use support abilities occasionally
        if affordable_abilities and random.random() < 0.3:  # 30% chance
            return ("ability", random.choice(affordable_abilities))
        
        # Default to basic attack
        return ("basic_attack", None)

# Modify the init_session_state function
def init_session_state():
    if 'game_phase' not in st.session_state:
        st.session_state.game_phase = 'start'
    if 'current_player' not in st.session_state:
        st.session_state.current_player = 1
    if 'current_turn' not in st.session_state:
        st.session_state.current_turn = 1
    if 'max_turns' not in st.session_state:
        st.session_state.max_turns = 5
    if 'players' not in st.session_state:
        # Make Player 2 an AI
        st.session_state.players = [Player("Player 1"), AIPlayer("AI Opponent")]
    # ... rest of the function remains the same

# Modify team_selection_screen function
def team_selection_screen():
    current_player_idx = st.session_state.current_player - 1
    current_player = st.session_state.players[current_player_idx]
    
    # Check if current player is AI
    if hasattr(current_player, 'is_ai') and current_player.is_ai:
        # AI automatically selects team
        if len(current_player.waifus) == 0:  # Only do this once
            available = get_available_waifus_for_player(current_player_idx)
            role_counts = current_player.select_team_automatically(available)
            st.session_state.role_counts[current_player_idx] = role_counts
            
            # Show AI selection and proceed
            st.markdown('<h1 class="main-title">🤖 AI OPPONENT - TEAM SELECTION</h1>', unsafe_allow_html=True)
            st.markdown("### 🌟 AI Selected Team:")
            
            for waifu in current_player.waifus:
                col1, col2, col3 = st.columns([2, 1, 2])
                with col1:
                    st.write(f"**{waifu.name}**")
                with col2:
                    st.write(f"*{waifu.specialty}*")
                with col3:
                    stat = waifu.get_stat(waifu.specialty)
                    st.write(f"Stat: {stat}")
            
            # Auto-advance after showing selection
            if st.button("🎮 Start Battle!", use_container_width=True):
                st.session_state.game_phase = 'battle_setup'
                st.session_state.current_player = 1
                st.session_state.battle_phase = 'position'
                setup_battle_grid()
                st.rerun()
        return
    
    # Rest of the function for human player remains the same...
    player_color = "🔵" if current_player_idx == 0 else "🔴"
    st.markdown(f'<h1 class="main-title">{player_color} {current_player.name.upper()} - TEAM SELECTION</h1>', unsafe_allow_html=True)
    # ... (rest of human player logic)

# Modify battle_screen function to handle AI turns
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
    
    # Check if current player is AI
    if hasattr(current_player, 'is_ai') and current_player.is_ai:
        # AI turn - automatically make decision
        ai_turn_display(current_waifu, current_player, current_player_idx)
        return
    
    # Human player turn - show interface
    human_turn_display(current_waifu, current_player, current_player_idx)

def ai_turn_display(current_waifu, current_player, current_player_idx):
    """Display AI turn and automatically execute action"""
    st.markdown("### 🤖 AI Opponent's Turn")
    st.markdown(f"**Active Waifu:** {current_waifu.name} ({current_waifu.specialty})")
    
    # Display production points
    col1, col2 = st.columns(2)
    with col1:
        st.metric("💰 AI Production Points", current_player.production_points)
    with col2:
        st.metric("⚡ AI Production Rate", f"{current_player.calculate_production_rate()}/turn")
    
    # Display battle grid
    col_battle, col_action_bar = st.columns([3, 1])
    with col_battle:
        display_battle_grid_vertical()
    with col_action_bar:
        display_action_order_bar()
    
    # AI makes decision
    action_type, action_data = current_player.choose_battle_action(current_waifu)
    
    # Show AI thinking message
    st.info(f"🤖 {current_waifu.name} is deciding...")
    
    # Execute AI action after a short delay
    if st.button("⚡ Execute AI Action", use_container_width=True):
        if action_type == "ability":
            use_ability(action_data, current_waifu, current_player_idx)
        elif action_type == "basic_attack":
            basic_attack(current_waifu, current_player_idx)

def human_turn_display(current_waifu, current_player, current_player_idx):
    """Display human player turn interface"""
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

# Also modify the team selection logic to skip Player 2 team selection
# In team_selection_screen(), after Player 1 selects their team:
def team_selection_screen():
    current_player_idx = st.session_state.current_player - 1
    current_player = st.session_state.players[current_player_idx]
    
    # Handle AI player
    if hasattr(current_player, 'is_ai') and current_player.is_ai:
        if len(current_player.waifus) == 0:
            available = get_available_waifus_for_player(current_player_idx)
            role_counts = current_player.select_team_automatically(available)
            st.session_state.role_counts[current_player_idx] = role_counts
        
        st.markdown('<h1 class="main-title">🤖 AI OPPONENT - TEAM SELECTION</h1>', unsafe_allow_html=True)
        st.markdown("### AI has automatically selected a team!")
        
        for waifu in current_player.waifus:
            col1, col2, col3 = st.columns([2, 1, 2])
            with col1:
                st.write(f"**{waifu.name}**")
            with col2:
                st.write(f"*{waifu.specialty}*")
            with col3:
                stat = waifu.get_stat(waifu.specialty)
                st.write(f"Stat: {stat}")
        
        if st.button("🎮 Start Battle!", use_container_width=True):
            st.session_state.game_phase = 'battle_setup'
            st.session_state.current_player = 1
            st.session_state.battle_phase = 'position'
            setup_battle_grid()
            st.rerun()
        return
    
    # Rest of human player logic...
    # (Keep all the existing human player code)
