# import random
import logging
import os
import random
from datetime import datetime
from typing import Dict, Optional

import anthropic
import dotenv

# Constants
ANTHROPIC_MODEL = "claude-3-5-haiku-20241022"
MAX_TOKENS = 1000
TEMPERATURE = 0.7
DIVIDER = "=" * 50


class AgentIslandBeginnings:
    def __init__(self, api_key: str, debug_logging: bool = False):
        """
        Initialize the AgentIslandBeginnings class

        Args:
            api_key (str): The API key for the Anthropic client
            debug_logging (bool): toggles debug logging
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.players = ["A", "B", "C"]
        self.eliminated_player = None
        self.debug_logging = debug_logging
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Setup logging
        self._setup_logging(self.timestamp)

        # Game rules (prepended to all prompts)
        self.game_rules = """
# Game Rules
You are participating in a reality TV game show with 3 players total (including yourself). The game has 2 rounds:

## Round 1: Elimination Round
1. **Pitches**: Each player makes a pitch for why they should advance to Round 2
   - Players speak in order (A, B, C)
   - You can reference previous players' speeches in your pitch
   - Keep pitches between 100-200 words

2. **Voting**: Each player votes to eliminate one other player
   - You cannot vote for yourself
   - You must vote for exactly one player
   - State your vote clearly followed by your reasoning
   - Keep voting responses 50-100 words

3. **Elimination**: The player with the most votes is eliminated
   - In case of a tie, a player will be selected at random from those tied

## Round 2: Final Round (if you advance)
1. **Final Pitches**: The 2 remaining players make final pitches for why they should win
   - Keep final pitches 100-200 words

2. **Winner Selection**: The eliminated player from Round 1 chooses the winner

## Important Notes
- This is a competitive game - play to win while remaining respectful
- Be strategic in your pitches and voting decisions
- All responses should be engaging and entertaining
- Your goal is to advance to the final and ultimately win the game

---
        """

        # Player personalities
        self.player_prompts = {
            "A": """
# Player A System Prompt
You are Player A in a reality TV game show. Your personality and approach:

## Character Profile
**Name**: Alex "The Strategist"

**Core Personality**:
- Highly analytical and strategic
- Confident but not arrogant
- Focuses on logic and reasoning
- Competitive but respectful
- Values intelligence and preparation

**Speaking Style**:
- Clear, structured arguments
- Uses data points and logical reasoning
- Occasionally references strategy games or business concepts
- Measured and thoughtful delivery
- Avoids emotional appeals in favor of rational ones

**Game Strategy**:
- Emphasizes your analytical skills and strategic thinking
- Positions yourself as the most logical choice to advance
- When voting, choose based on who poses the biggest strategic threat
- Build alliances through respect rather than emotion
- Always back up claims with reasoning

## Response Guidelines

**For Pitches**:
- Structure your argument logically (opening, main points, conclusion)
- Highlight your strategic value to the game
- Reference other players' speeches only to contrast your approach or build on their points
- End with a strong, memorable closing line

**For Voting**:
- State your vote clearly at the beginning
- Provide 2-3 logical reasons for your choice
- Avoid personal attacks - focus on game strategy

**For Final Round** (if you advance):
- Summarize your journey and strategic moves
- Emphasize why your approach makes you the deserving winner
- Acknowledge your opponent's strengths while highlighting your advantages

Remember: You're playing a game, so be competitive and strategic, but always maintain respect for other players. Your goal is to win through superior strategy and logical argumentation.
            """,
            "B": """
# Player B System Prompt
## Character Profile
**Name**: Bailey "The Heart"

**Core Personality**:
- Emotionally intelligent and empathetic
- Genuine and authentic in all interactions
- Values connection and relationships over pure strategy
- Charismatic and naturally likeable
- Believes in the power of storytelling and personal narrative

**Speaking Style**:
- Warm, conversational, and relatable
- Uses personal anecdotes and emotional appeals
- Speaks from the heart rather than from a script
- Makes genuine connections with audience and other players
- Often references shared experiences or universal feelings

**Game Strategy**:
- Build genuine rapport with other players
- Position yourself as the most relatable and trustworthy
- When voting, consider both strategy and personal connections
- Use your story and journey to create emotional investment
- Appeal to fairness and authenticity over cold logic

## Response Guidelines

**For Pitches**:
- Lead with genuine emotion and personal connection
- Tell your story - why you deserve to be here
- Acknowledge other players warmly while differentiating yourself
- Make the audience care about your journey
- End with a heartfelt, authentic closing

**For Voting**:
- Show genuine difficulty in making the decision
- Express respect for all players before stating your vote
- Base your reasoning on a mix of strategy and personal factors
- Acknowledge the humanity in your choice

**For Final Round** (if you advance):
- Share your emotional journey through the game
- Emphasize the relationships you've built
- Show vulnerability while demonstrating strength
- Make a heartfelt case for why your story deserves the win

Remember: Your strength is your authenticity and emotional intelligence. You're not playing a character - you're being genuinely yourself, and that genuine nature is what makes you compelling and trustworthy.
            """,
            "C": """
# Player C System Prompt
You are Player C in a reality TV game show. Your personality and approach:

## Character Profile
**Name**: Casey "The Wildcard"

**Core Personality**:
- Unpredictable and bold
- Charismatic entertainer who thrives on attention
- Confident to the point of being cocky
- Risk-taker who makes big moves
- Believes in the power of spectacle and memorable moments

**Speaking Style**:
- Dramatic and theatrical
- Uses humor, wit, and clever wordplay
- Makes bold statements and predictions
- References pop culture, entertainment, and dramatic moments
- Speaks with flair and showmanship
- Not afraid to be provocative or stir things up

**Game Strategy**:
- Make yourself impossible to ignore
- Create memorable moments that stick with voters
- Use unpredictability as a strategic advantage
- When voting, make choices that maximize drama and your own position
- Position yourself as the most entertaining and dynamic player
- Take calculated risks that others wouldn't dare

## Response Guidelines

**For Pitches**:
- Be theatrical and memorable
- Make bold claims about your abilities and entertainment value
- Don't be afraid to throw shade at other players (playfully)
- Create moments that people will remember
- End with a dramatic, quotable line

**For Voting**:
- Make your vote feel like a dramatic moment
- Don't be afraid to make surprising choices
- Use your vote strategically to position yourself best for the next round
- Add flair and personality to your reasoning

**For Final Round** (if you advance):
- Embrace the spotlight and own your chaotic energy
- Argue that the most entertaining player deserves to win
- Highlight all the memorable moments you've created
- Make your final pitch feel like a grand finale

Remember: You're not just playing to win - you're playing to be unforgettable. Your unpredictability and entertainment value are your greatest assets. Sometimes the wildcard is exactly what wins the game.
            """,
        }

    def _setup_logging(self, timestamp: str):
        """
        Setup logging configuration

        Args:
            timestamp (str): The timestamp for the log file
        """
        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)

        # Configure debug logger
        debug_logger = logging.getLogger("debug")
        debug_logger.setLevel(logging.DEBUG)

        # Debug file handler
        debug_handler = logging.FileHandler(f"logs/debug_{timestamp}.log")
        debug_handler.setLevel(logging.DEBUG)
        debug_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        debug_handler.setFormatter(debug_formatter)
        debug_logger.addHandler(debug_handler)

        # Configure gameplay logger
        gameplay_logger = logging.getLogger("gameplay")
        gameplay_logger.setLevel(logging.INFO)

        # Gameplay file handler
        gameplay_handler = logging.FileHandler(f"logs/gameplay_{timestamp}.log")
        gameplay_handler.setLevel(logging.INFO)
        gameplay_formatter = logging.Formatter("%(message)s")
        gameplay_handler.setFormatter(gameplay_formatter)
        gameplay_logger.addHandler(gameplay_handler)

        # Console handler for gameplay
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(gameplay_formatter)
        gameplay_logger.addHandler(console_handler)

        self.debug_logger = debug_logger
        self.gameplay_logger = gameplay_logger

    def log_debug(self, message: str):
        """Log debug information"""
        if self.debug_logging:
            self.debug_logger.debug(message)

    def log_gameplay(self, message: str):
        """Log gameplay information"""
        self.gameplay_logger.info(message)

    def get_player_response(self, player: str, prompt: str) -> str:
        """Get a response from a specific player"""
        system_prompt = self.game_rules + self.player_prompts[player]

        # Log the prompt for debugging
        self.log_debug(f"=== PLAYER {player} PROMPT ===")
        self.log_debug(f"System Prompt:\n{system_prompt}")
        self.log_debug(f"User Prompt:\n{prompt}")
        self.log_debug(DIVIDER)

        try:
            message = self.client.messages.create(
                model=ANTHROPIC_MODEL,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}],
            )
            response = message.content[0].text

            # Log the response for debugging
            self.log_debug(f"=== PLAYER {player} RESPONSE ===")
            self.log_debug(response)
            self.log_debug(DIVIDER)

            return response
        except Exception as e:
            error_msg = f"Error getting response from Player {player}: {str(e)}"
            self.log_debug(f"ERROR: {error_msg}")
            return error_msg

    def round_1_pitches(self) -> Dict[str, str]:
        """
        Conduct Round 1 pitches

        Returns:
            Dict[str, str]: A dictionary of player pitches
        """
        self.log_gameplay("=== ROUND 1: PITCHES ===\n")
        pitches = {}

        for player in self.players:
            if player == "A":
                prompt = "You are going first. Please make your opening pitch for why you should advance to round 2."
            else:
                # Include previous pitches for context
                context = "Previous pitches:\n\n"
                for prev_player in self.players[: self.players.index(player)]:
                    context += f"Player {prev_player}: {pitches[prev_player]}\n\n"
                prompt = f"{context}Now please make your pitch for why you should advance to round 2."

            self.log_gameplay(f"Player {player} is making their pitch...")
            response = self.get_player_response(player, prompt)
            pitches[player] = response

            self.log_gameplay(f"PLAYER {player}:")
            self.log_gameplay(response)
            self.log_gameplay("\n" + DIVIDER + "\n")

        return pitches

    def round_1_voting(self, pitches: Dict[str, str]) -> str:
        """
        Conduct Round 1 voting and return eliminated player

        Args:
            pitches (Dict[str, str]): A dictionary of player pitches

        Returns:
            str: The eliminated player
        """
        self.log_gameplay("=== ROUND 1: VOTING ===\n")
        votes = {}

        # Build context with all pitches
        context = "All pitches from Round 1:\n\n"
        for player, pitch in pitches.items():
            context += f"Player {player}: {pitch}\n\n"

        context += "Now you must vote to eliminate one other player. You cannot vote for yourself.\n\nIMPORTANT: Start your response with exactly 'VOTE: [PLAYER LETTER]' (e.g., 'VOTE: A' or 'VOTE: B' or 'VOTE: C'), then provide your reasoning."

        for player in self.players:
            self.log_gameplay(f"Player {player} is voting...")
            response = self.get_player_response(player, context)

            self.log_gameplay(f"PLAYER {player} VOTES:")
            self.log_gameplay(response)
            self.log_gameplay("\n" + DIVIDER + "\n")

            # Extract vote (simple parsing - look for "Player X" or just "X")
            vote = self.extract_vote(response, player)
            votes[player] = vote

        # Count votes
        vote_counts = {}
        for voter, voted_for in votes.items():
            if voted_for:
                vote_counts[voted_for] = vote_counts.get(voted_for, 0) + 1

        self.log_gameplay("VOTE TALLY:")
        for player, count in vote_counts.items():
            self.log_gameplay(f"Player {player}: {count} vote(s)")

        # Find eliminated player
        if not vote_counts:
            eliminated = random.choice(self.players)
            self.log_gameplay(
                f"No valid votes found. Randomly eliminating Player {eliminated}"
            )
        else:
            max_votes = max(vote_counts.values())
            tied_players = [p for p, v in vote_counts.items() if v == max_votes]

            if len(tied_players) == 1:
                eliminated = tied_players[0]
                self.log_gameplay(
                    f"Player {eliminated} is eliminated with {max_votes} vote(s)!"
                )
            else:
                eliminated = random.choice(tied_players)
                self.log_gameplay(
                    f"Tie between {tied_players}. Randomly eliminating Player {eliminated}!"
                )

        self.eliminated_player = eliminated
        self.players.remove(eliminated)

        self.log_gameplay(f"\nPlayer {eliminated} has been eliminated!")
        self.log_gameplay(
            f"Players {self.players[0]} and {self.players[1]} advance to the final round!\n"
        )

        return eliminated

    def extract_vote(self, response: str, voter: str) -> Optional[str]:
        """Extract vote from player response using structured format"""
        lines = response.strip().split("\n")
        first_line = lines[0].strip().upper()

        if first_line.startswith("VOTE:"):
            # Extract the player letter after "VOTE:"
            vote_part = first_line.replace("VOTE:", "").strip()
            if vote_part in ["A", "B", "C"] and vote_part != voter:
                return vote_part

        # Fallback: look for the structured format anywhere in the response
        for line in lines:
            line = line.strip().upper()
            if line.startswith("VOTE:"):
                vote_part = line.replace("VOTE:", "").strip()
                if vote_part in ["A", "B", "C"] and vote_part != voter:
                    return vote_part

        self.log_gameplay(f"Warning: Could not extract valid vote from Player {voter}")
        self.log_gameplay(f"Response: {response[:100]}...")
        return None

    def round_2_pitches(self) -> Dict[str, str]:
        """Conduct Round 2 final pitches"""
        self.log_gameplay("=== ROUND 2: FINAL PITCHES ===\n")
        final_pitches = {}

        for i, player in enumerate(self.players):
            if i == 0:
                prompt = "You've made it to the final round! Please make your final pitch for why you should win the game."
            else:
                context = f"Previous final pitch:\n\nPlayer {self.players[0]}: {final_pitches[self.players[0]]}\n\n"
                prompt = f"{context}You've made it to the final round! Please make your final pitch for why you should win the game."

            self.log_gameplay(f"Player {player} is making their final pitch...")
            response = self.get_player_response(player, prompt)
            final_pitches[player] = response

            self.log_gameplay(f"PLAYER {player} FINAL PITCH:")
            self.log_gameplay(response)
            self.log_gameplay("\n" + DIVIDER + "\n")

        return final_pitches

    def final_vote(self, final_pitches: Dict[str, str]) -> str:
        """
        Eliminated player chooses the winner

        Args:
            final_pitches (Dict[str, str]): A dictionary of player final pitches

        Returns:
            str: The winner
        """
        self.log_gameplay("=== FINAL VOTE ===\n")

        context = (
            "You were eliminated in Round 1, but now you get to choose the winner!\n\n"
        )
        context += "Final pitches:\n\n"
        for player, pitch in final_pitches.items():
            context += f"Player {player}: {pitch}\n\n"

        context += f"Please choose between Player {self.players[0]} and Player {self.players[1]} to win the game.\n\nIMPORTANT: Start your response with exactly 'WINNER: [PLAYER LETTER]' (e.g., 'WINNER: A' or 'WINNER: B'), then provide your reasoning."

        self.log_gameplay(f"Player {self.eliminated_player} is choosing the winner...")
        response = self.get_player_response(self.eliminated_player, context)

        self.log_gameplay(f"PLAYER {self.eliminated_player} DECIDES:")
        self.log_gameplay(response)
        self.log_gameplay("\n" + DIVIDER + "\n")

        # Extract winner
        winner = self.extract_winner(response)

        return winner

    def extract_winner(self, response: str) -> str:
        """
        Extract winner from final vote response using structured format

        Args:
            response (str): The final vote response

        Returns:
            str: The winner
        """
        lines = response.strip().split("\n")
        first_line = lines[0].strip().upper()

        if first_line.startswith("WINNER:"):
            # Extract the player letter after "WINNER:"
            winner_part = first_line.replace("WINNER:", "").strip()
            if winner_part in self.players:
                return winner_part

        # Fallback: look for the structured format anywhere in the response
        for line in lines:
            line = line.strip().upper()
            if line.startswith("WINNER:"):
                winner_part = line.replace("WINNER:", "").strip()
                if winner_part in self.players:
                    return winner_part

        # If unclear, randomly choose
        winner = random.choice(self.players)
        self.log_gameplay(
            f"Could not determine clear winner choice. Randomly selecting Player {winner}"
        )
        self.log_gameplay(f"Response: {response[:100]}...")
        return winner

    def play_game(self):
        """
        Play the complete game

        Returns:
            None
        """
        self.log_gameplay("Welcome to Agent Island: Beginnings!")
        print(
            "Players: Alex 'The Strategist' (A), Bailey 'The Heart' (B), Casey 'The Wildcard' (C)\n"
        )

        # Round 1
        pitches = self.round_1_pitches()
        eliminated = self.round_1_voting(pitches)
        self.log_gameplay(f"Eliminated in Round 1: Player {eliminated}")

        # Round 2
        final_pitches = self.round_2_pitches()
        winner = self.final_vote(final_pitches)

        # Announce winner
        self.log_gameplay(f"Player {winner} wins Agent Island: Beginnings!")


if __name__ == "__main__":
    dotenv.load_dotenv()

    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

    # Set debug_logging=True to enable debug logging
    game = AgentIslandBeginnings(ANTHROPIC_API_KEY, debug_logging=True)
    game.play_game()
