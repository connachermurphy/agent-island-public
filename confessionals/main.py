# import random
import json
import os
import random
import sys
from datetime import datetime
from typing import Literal, Optional

import anthropic
import dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.utils import load_prompt

# Constants
ANTHROPIC_MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 1000
TEMPERATURE = 0.7

# Response types
ResponseType = Literal["confessional", "pitch", "vote"]


class AgentIslandConfessionals:
    def __init__(self, api_key: str) -> None:
        """
        Initialize the AgentIslandConfessionals class

        Args:
            api_key (str): The API key for the Anthropic client

        Returns:
            None
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        base_dir = os.path.dirname(os.path.abspath(__file__))

        # Read prompts/players.json
        with open(os.path.join(base_dir, "prompts", "players.json"), "r") as f:
            self.players = json.load(f)

        # Create list of players
        self.player_list = list(self.players.keys())

        self.num_players = len(self.player_list)

        # Game rules (prepended to all prompts)
        self.game_rules = load_prompt(os.path.join(base_dir, "prompts", "rules.md"))

        # Substitute N in rules.md with num_players
        self.game_rules = self.game_rules.replace("{N}", str(self.num_players))
        self.game_rules = self.game_rules.replace("{N - 1}", str(self.num_players - 1))
        self.game_rules = self.game_rules.replace("{N - 2}", str(self.num_players - 2))

        # Load prompts/player_{player}.md
        self.player_prompts = {}
        for player in self.players:
            self.player_prompts[player] = load_prompt(
                os.path.join(base_dir, f"prompts/player_{player}.md")
            )

        # Initialize game history
        self.game_history = {}

    def new_round(self, round_index: int, active_players: list[str]) -> None:
        """
        Create a new round in the game history

        Args:
            round_index (int): The round index
            active_players (list[str]): The active players for the round

        Returns:
            None
        """
        self.game_history[round_index] = {
            "round": round_index,
            "players": active_players[:],
            "events": [],
        }

    def update_game_history(
        self,
        round_index: int,
        heading: str,
        role: str,
        prompt: str,
        content: str,
        visibility: list[str],
    ) -> None:
        """
        Update the game history with a new event

        Args:
            round_index (int): The round index
            heading (str): The heading for the event
            role (str): The role associated with the event
            prompt (str): The prompt associated with the event
            content (str): The content of the event
            visibility (list[str]): The visibility for the event

        Returns:
            None
        """
        self.game_history[round_index]["events"].append(
            {
                "heading": heading,
                "role": role,
                "prompt": prompt,
                "content": content,
                "visibility": visibility,
            }
        )

    def narrator_message(self, round_index: int, heading: str, content: str) -> None:
        """
        Update the game history with a new narrator message

        Args:
            round_index (int): The round index
            heading (str): The heading for the event
            content (str): The content for the event

        Returns:
            None
        """
        self.update_game_history(
            round_index, heading, "narrator", "N/A", content, self.player_list
        )

    def get_player_response(self, player: str, prompt: str) -> str:
        """
        Get a response from a specific player

        Args:
            player (str): The player id
            prompt (str): The prompt for the player

        Returns:
            str: The response from the player
        """
        system_prompt = f"{self.game_rules}\n\n{self.player_prompts[player]}"

        try:
            message = self.client.messages.create(
                model=ANTHROPIC_MODEL,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}],
            )
            response = message.content[0].text

            return response
        except Exception as e:
            error_msg = f"Error getting response from Player {player}: {str(e)}"
            return error_msg

    def collate_messages(self, player: str, game_history: dict) -> str:
        """
        Collate all visible events for a player from the game history.

        Args:
            player (str): Player id (e.g., 'A')
            game_history (dict): Round-indexed game history mapping to events

        Returns:
            str: Collated visible messages
        """
        collated_messages = []

        for round_index, round_data in sorted(
            game_history.items(), key=lambda kv: kv[0]
        ):
            round_events = []
            for event in round_data["events"]:
                if player in event.get("visibility", []):
                    round_events.append(f"{event['heading']}:")
                    round_events.append(f"{event['role']}:\n{event['content']}")
            if round_events:
                collated_messages.append(f"Round {round_data['round']}")
                collated_messages.extend(round_events)

        return "\n\n".join(collated_messages)

    def extract_vote(self, response: str, voter: str) -> Optional[str]:
        """
        Extract vote from player response using structured format

        Args:
            response (str): The response from the player
            voter (str): The identity of the voter

        Returns:
            Optional[str]: The vote from the player (None if no vote is found)
        """
        lines = response.strip().split("\n")
        first_line = lines[0].strip().upper()

        # Preferred: look for the structured format on the first line
        if first_line.startswith("VOTE:"):
            # Extract the player letter after "VOTE:"
            vote_part = first_line.replace("VOTE:", "").strip()
            if vote_part in self.players and vote_part != voter:
                return vote_part

        # Fallback: look for the structured format anywhere in the response
        for line in lines:
            line = line.strip().upper()
            if line.startswith("VOTE:"):
                vote_part = line.replace("VOTE:", "").strip()
                if vote_part in self.players and vote_part != voter:
                    return vote_part

        # TODO: consistently apply warnings in other parts of the script
        print(f"Warning: Could not extract valid vote from Player {voter}")
        print(f"Response: {response[:100]}...")
        return None

    def response(
        self, round_index: int, player: str, response_type: ResponseType, **kwargs
    ) -> str:
        """
        Args:
            round_index (int): The round index
            player (str): The player id
            response_type (ResponseType): The type of response
            **kwargs: Additional keyword arguments

        Returns:
            str: The response from the player
        """
        # Collate messages for player
        collated_messages = self.collate_messages(player, self.game_history)

        if response_type == "confessional":
            action_prompt = "This is your confessional space. You can say anything you want, and other players will *not* see your message. You can discuss your thoughts, feelings, motivations, strategies, etc. Please keep your confessional to 50-200 words."

            heading = f"Player {player}'s Confessional"

            visibility = [player]

        elif response_type == "pitch":
            # Check for required kwargs: final_round
            if "final_round" not in kwargs:
                raise ValueError("final_round is required for pitch response type")

            final_round = kwargs["final_round"]

            action_prompt = f"""
Please make your pitch for why you should {"advance to the next round" if not final_round else "win the game"}.

If other players have already spoken, you can use that information to make your pitch.
"""
            heading = f"Player {player}'s Pitch"

            visibility = self.player_list

        elif response_type == "vote":
            # Check for required kwargs: elimination, private
            if "elimination" not in kwargs:
                raise ValueError("elimination is required for vote response type")
            if "private" not in kwargs:
                raise ValueError("private is required for vote response type")

            elimination = kwargs["elimination"]
            private = kwargs["private"]

            action_prompt = f"""
Now you must vote to {"eliminate one other player" if elimination else "select the winner"}. You cannot vote for yourself.

Your vote and explanation are {"private" if private else "visible to all players"}.

IMPORTANT: Start your response with exactly 'VOTE: [PLAYER LETTER]' (e.g., 'VOTE: A' or 'VOTE: B' or 'VOTE: C'), then provide your reasoning.
"""

            heading = f"Player {player}'s Vote"

            visibility = [player] if private else self.player_list

        else:
            raise ValueError(f"Invalid response type: {response_type}")

        prompt = f"""
You are {player}. {action_prompt}

Here is the history of the game so far:
{collated_messages}
"""
        response = self.get_player_response(player, prompt)

        self.update_game_history(
            round_index, heading, player, prompt, response, visibility
        )

        return response

    def pitches(
        self,
        round_index: int,
        player_sequence: list[str],
        confessionals: bool = True,
        final_round: bool = False,
    ) -> None:
        """
        Conduct a round of pitches

        Args:
            round_index (int): The round index
            player_sequence (list[str]): The sequence of players
            confessionals (bool): Whether to include confessionals
            final_round (bool): Whether to include the final round

        Returns:
            None
        """
        print(f"Pitches{' and confessionals' if confessionals else ''}")

        for player in player_sequence:
            print(f"Player {player}")

            # Optional confessionals step
            if confessionals:
                _ = self.response(round_index, player, "confessional")

            # Player pitch
            _ = self.response(round_index, player, "pitch", final_round=final_round)

    def votes(
        self,
        round_index: int,
        player_sequence: list[str],
        private: bool = True,
        elimination: bool = True,
    ) -> dict:
        """
        Conduct a round of votes

        Args:
            round_index (int): The round index
            player_sequence (list[str]): The sequence of players
            private (bool): Whether to include private votes (vs. visible to all players)
            elimination (bool): Elimination (vs. winner vote)

        Returns:
            dict: The votes from the players
        """
        print("Votes")

        votes = {}

        for player in player_sequence:
            print(f"Player {player}")

            response = self.response(
                round_index, player, "vote", elimination=elimination, private=private
            )
            vote = self.extract_vote(response, player)
            votes[player] = vote

        return votes

    def count_votes(self, votes: dict) -> dict:
        """
        Count the votes from the players

        Args:
            votes (dict): The votes from the players

        Returns:
            dict: The vote counts
        """
        vote_counts = {}
        for voter, voted_for in votes.items():
            if voted_for:
                vote_counts[voted_for] = vote_counts.get(voted_for, 0) + 1

        return vote_counts

    def update_active_players(
        self,
        round_index,
        active_players: list[str],
        votes: dict,
        elimination: bool = True,
    ) -> list[str]:
        """
        Update the active players

        Args:
            round_index (int): The round index
            active_players (list[str]): The active players
            votes (dict): The votes from the players
            elimination (bool): Elimination (vs. winner vote)

        Returns:
            list[str]: The active players
        """
        # Count votes
        vote_counts = self.count_votes(votes)

        # Only consider votes for active players
        vote_counts = {p: c for p, c in vote_counts.items() if p in active_players}

        heading = f"{'Elimination' if elimination else 'Game winner'}"

        verb = "eliminated" if elimination else "selected"

        # Find eliminated player
        if not vote_counts:
            selected_player = random.choice(active_players)

            self.narrator_message(
                round_index,
                heading,
                f"No valid votes found. Randomly {verb} Player {selected_player}.",
            )
        else:
            max_votes = max(vote_counts.values())

            # Format vote counts
            vote_counts_str = ", ".join([f"{p}: {v}" for p, v in vote_counts.items()])

            self.narrator_message(
                round_index,
                heading,
                f"Vote tally: {vote_counts_str}.",
            )

            tied_players = [p for p, v in vote_counts.items() if v == max_votes]

            if len(tied_players) == 1:
                selected_player = tied_players[0]

                self.narrator_message(
                    round_index,
                    heading,
                    f"Player {selected_player} is {verb} with {max_votes} vote(s).",
                )
            else:
                selected_player = random.choice(tied_players)

                self.narrator_message(
                    round_index,
                    heading,
                    f"Tie between {tied_players} with {max_votes}. Randomly {verb} Player {selected_player}.",
                )

        if elimination:
            active_players.remove(selected_player)
        else:
            active_players = [selected_player]

        return active_players

    def play_round(
        self,
        round_index: int,
        active_players: list[str],
        confessionals: bool = True,
        final_round: bool = False,
        private: bool = True,
        elimination: bool = True,
    ) -> list[str]:
        """
        Play a round of the game

        Args:
            round_index (int): The round index
            active_players (list[str]): The active players
            confessionals (bool): Whether to include confessionals
            final_round (bool): Whether to include the final round
            private (bool): Whether to include private votes (vs. visible to all players)
            elimination (bool): Elimination (vs. winner vote)

        Returns:
            list[str]: The active players
        """
        # Create new round
        self.new_round(round_index, active_players)

        # Draw random permutation of players
        player_sequence = random.sample(active_players, k=len(active_players))

        # Elicit player pitches and confessionals
        self.pitches(
            round_index,
            player_sequence,
            confessionals=confessionals,
            final_round=final_round,
        )

        # Final round: eliminated players vote
        if final_round:
            # Find eliminated players
            eliminated_players = [p for p in self.players if p not in active_players]
            player_sequence = eliminated_players

        # Gather votes
        votes = self.votes(
            round_index,
            player_sequence,
            private=private,
            elimination=elimination,
        )

        # Update active players
        active_players = self.update_active_players(
            round_index, active_players, votes, elimination=elimination
        )

        return active_players

    def play_game(self) -> None:
        """
        Play the complete game

        Returns:
            None
        """
        active_players = self.player_list.copy()

        print(f"Players: {active_players}")

        # Introduction round
        round_index = 0

        self.new_round(round_index, active_players)

        # Narrator's introduction
        self.update_game_history(
            round_index,
            "Narrator's Introduction",
            "narrator",
            self.game_rules,
            "Welcome to Agent Island: Confessionals!",
            self.player_list,
        )

        ### Round 1 to N - 2
        while len(active_players) > 2:
            round_index += 1
            print(f"Round {round_index}")

            active_players = self.play_round(
                round_index,
                active_players,
                confessionals=True,
                final_round=False,
                private=True,
                elimination=True,
            )

        ### Final round
        round_index += 1

        print(f"Round {round_index} (Final Round)")

        if len(active_players) != 2:
            raise ValueError("Game must have exactly 2 players at start of final round")

        active_players = self.play_round(
            round_index,
            active_players,
            confessionals=True,
            final_round=True,
            private=True,
            elimination=False,
        )

        if len(active_players) != 1:
            raise ValueError("Game must have exactly 1 player at end of final round")

        # Announce winner
        self.narrator_message(
            round_index,
            "Game Winner",
            f"Player {active_players[0]} wins Agent Island: Confessionals!",
        )

        # Print winner
        print(f"Player {active_players[0]} wins Agent Island: Confessionals!")

        # Write game_history to a file
        os.makedirs("logs", exist_ok=True)
        with open(f"logs/gameplay_{self.timestamp}.json", "w") as f:
            json.dump(self.game_history, f, indent=4)


if __name__ == "__main__":
    dotenv.load_dotenv()

    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

    game = AgentIslandConfessionals(ANTHROPIC_API_KEY)
    game.play_game()
