ALPHABET = ["0", "1", "2", "3"]


class State(str):
    """A state in an automaton."""

    @staticmethod
    def start():
        """Return the start state.

        Returns
        -------
        State
            The start state labeled "S".
        """
        return State("S")

    @staticmethod
    def dead():
        """Return the dead state.

        Returns
        -------
        State
            The dead state labeled "F0".
        """
        return State("F0")

    def is_start(self):
        """Check if this is the start state.

        Returns
        -------
        bool
            True if this state is the start state.
        """
        return self == State.start()

    def is_final(self):
        """Check if this is a final state.

        Returns
        -------
        bool
            True if state label starts with "F".
        """
        return self.startswith("F")

    def is_dead(self):
        """Check if this is the dead state.

        Returns
        -------
        bool
            True if this is the dead state.
        """
        return self == State.dead()

    def is_accept(self):
        """Check if this is an accepting state.

        Returns
        -------
        bool
            True if final and not dead.
        """
        return self.is_final() and not self.is_dead()


class TransitionMap(dict):
    """Represents transitions from a state to target states."""

    def __iter__(self):
        """Iterate over (symbol, target) pairs.

        Yields
        ------
        tuple
            (symbol, target_state) pairs.
        """
        return iter(self.items())

    def symbols(self):
        """Return all symbols in the transition map.

        Returns
        -------
        dict_keys
            Symbols that have transitions defined.
        """
        return self.keys()

    def targets(self):
        """Return all target states.

        Returns
        -------
        dict_values
            States reachable via transitions.
        """
        return self.values()

    def target(self, symbol):
        """Get the target state for a symbol.

        Parameters
        ----------
        symbol : str
            The transition symbol.

        Returns
        -------
        State
            The target state.
        """
        return self[symbol]

    def add(self, symbol, target):
        """Add a transition.

        Parameters
        ----------
        symbol : str
            The transition symbol.
        target : State
            The target state.
        """
        self[symbol] = target

    def remove(self, symbol):
        """Remove a transition.

        Parameters
        ----------
        symbol : str
            The symbol to remove.
        """
        self.pop(symbol)


class Automaton(dict):
    """A finite automaton."""

    def __iter__(self):
        """Iterate over automaton states.

        Yields
        ------
        tuple
            (state, transition_map) pairs.
        """
        return iter(self.items())

    def __repr__(self):
        """Return string representation of the automaton.

        Returns
        -------
        str
            Formatted automaton.
        """
        return "\n".join(
            f"{state}: {self.transition_map(state)}"
            for state in sorted(self.states(), key=lambda s: (-ord(s[0]), len(s), s))
        )

    def states(self):
        """Return all states.

        Returns
        -------
        set
            All states in the automaton.
        """
        return set(self.keys())

    def final_states(self):
        """Return all final states.

        Returns
        -------
        set
            States with labels starting with "F".
        """
        return set(state for state in self.states() if state.is_final())

    def accept_states(self):
        """Return all accepting states.

        Returns
        -------
        set
            Accept states.
        """
        return set(state for state in self.final_states() if state.is_accept())

    def non_accept_states(self):
        """Return all non-accepting states.

        Returns
        -------
        set
            Non-accept states.
        """
        return set(state for state in self.states() if not state.is_accept())

    def transition_map(self, state):
        """Get the transitions for a state.

        Parameters
        ----------
        state : State
            The state.

        Returns
        -------
        TransitionMap
            Transitions from the given state.
        """
        return self[state]

    def evaluate(self, word):
        """Evaluate a word in the automaton.

        Parameters
        ----------
        word : str
            Sequence of symbols to process.

        Returns
        -------
        State
            The state reached after processing the word.
        """
        state = State.start()

        for symbol in word:
            transition_map = self.transition_map(state)

            if symbol in transition_map.symbols():
                target = transition_map.target(symbol)

                if state == target:
                    return State.dead()

                state = target

        return state

    def add_transition(self, source, symbol, target):
        """Add a transition to the automaton.

        Parameters
        ----------
        source : State
            The source state.
        symbol : str
            The transition symbol.
        target : State
            The target state.
        """
        if source not in self.states():
            self[source] = TransitionMap()

        self[source][symbol] = target


def make_automaton(ddt):
    """Construct an automaton from a difference distribution table.

    Parameters
    ----------
    ddt : matrix
        A difference distribution table.

    Returns
    -------
    Automaton
        The constructed automaton.
    """

    def patch_table(table):
        for i in range(table.nrows()):
            table.add_to_entry(i, 0, -table[i, 0])

        for i in range(1, table.ncols()):
            table.add_to_entry(0, i, -table[0, i])


    def make_state(i, j, size, encoding=""):
        if size == 1:
            value = int(ddt[i, j])
            state = f"F{value}"

            for symbol in ALPHABET:
                automaton.add_transition(state, symbol, State.dead())

            return state

        mid = size // 2

        children = (
            make_state(i, j, mid, encoding + "0"),
            make_state(i, j + mid, mid, encoding + "1"),
            make_state(i + mid, j, mid, encoding + "2"),
            make_state(i + mid, j + mid, mid, encoding + "3"),
        )

        if children in U:
            return U[children]

        if len(set(children)) == 1:
            return children[0]

        state = f"S{encoding}"
        U[children] = state

        for symbol, target in zip(ALPHABET, children):
            automaton.add_transition(state, symbol, target)

        return state

    U = dict()

    patch_table(ddt)
    automaton = Automaton()
    make_state(0, 0, ddt.nrows())

    return automaton


if __name__ == "__main__":
    from sage.crypto.sboxes import SEA

    print("=" * 60)
    print("Automaton Construction from DDT")
    print("=" * 60)

    print("\nLoading SEA S-box...")
    ddt = SEA.difference_distribution_table()

    print("\nConstructing automaton from the DDT...")
    automaton = make_automaton(ddt)

    print(f"\nAutomaton successfully created!")
    print(f"\nNumber of states: {len(automaton)}")

    print("\nAutomaton structure:")
    print("-" * 60)
    print(automaton)
    print("-" * 60)
