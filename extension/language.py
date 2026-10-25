from automata.fa.dfa import DFA
from automata.fa.nfa import NFA
from automata.fa.gnfa import GNFA
import automata.fa.fa as fa
from automate import AutomataExtended
from typing import (
    AbstractSet,
    Any,
    Callable,
    DefaultDict,
    Deque,
    Dict,
    FrozenSet,
    Generator,
    Iterator,
    List,
    Mapping,
    Optional,
    Set,
    Tuple,
    Type,
    cast,
)

class Language():

    REGEX_OPERATORS = {"|", "*", "(", ")", "ε", "∅", "?"}

    def __init__(self, alphabet: set, regex):
        self.alphabet = alphabet
        self.regex = regex

        self._validate_regex()

    def _validate_regex(self):
        for char in self.regex:
            if char not in self.alphabet and char not in self.REGEX_OPERATORS:
                raise ValueError(
                    f"Symbol '{char}' is not in the alphabet"
                )

    @classmethod
    def from_dfa(cls, alphabet: set, automate: DFA):
        regex = GNFA.from_dfa(automate).to_regex()
        return cls(alphabet, regex)

    @classmethod
    def from_set(cls, alphabet: set, language_set: set):
        regex = "|".join(
            word if word else "ε"
            for word in language_set
        )
        return cls(alphabet, regex)

    @classmethod
    def from_regex(cls, alphabet: set, regex):
        return cls(alphabet, regex)
        

    def accept(word, self): #Je suis pas trop sûr de ce que language veut dire
        nfa = NFA.from_regex(self.regex, input_symbols=self.alphabet)
        return nfa.accepts_input(word)

    def to_regex(self):
        return self.regex

    def to_dfa(self):
        nfa = NFA.from_regex(
            self.regex,
            input_symbols=self.alphabet
        )
        return DFA.from_nfa(nfa, minify= True)

    def reverse(self) -> None:
        nfa1 = NFA.from_regex(self.regex, input_symbols=self.alphabet)
        dfa = DFA.from_nfa(nfa1)
        self.regex = GNFA.from_dfa(dfa).to_regex()
        self.alphabet = dfa.input_symbols

    def concatenate(self, l2) -> None:
        nfa1 = NFA.from_regex(self.regex, input_symbols=self.alphabet)
        nfa2 = NFA.from_regex(l2.regex, input_symbols=l2.alphabet)

        nfa1.concatenate(nfa2)
        dfa = DFA.from_nfa(nfa1)

        self.regex = GNFA.from_dfa(dfa).to_regex()
        self.alphabet = dfa.input_symbols

    def union(self,l2) -> None:
        nfa1 = NFA.from_regex(self.regex, input_symbols=self.alphabet)
        nfa2 = NFA.from_regex(l2.regex, input_symbols=l2.alphabet)

        nfa1.union(nfa2)
        dfa = DFA.from_nfa(nfa1)

        self.regex = GNFA.from_dfa(dfa).to_regex()
        self.alphabet = dfa.input_symbols

    def shuffle(self,l2) -> None:
        nfa1 = NFA.from_regex(self.regex, input_symbols=self.alphabet)
        nfa2 = NFA.from_regex(l2.regex, input_symbols=l2.alphabet)

        nfa1.shuffle_product(nfa2)
        dfa = DFA.from_nfa(nfa1)

        self.regex = GNFA.from_dfa(dfa).to_regex()
        self.alphabet = dfa.input_symbols

    def star(self):
        return Language(
            self.alphabet,
            f"({self.regex})*"
        )

    #alors j'ai pas vérifier ça, c'est l'ia qui me l'a pondu , Je sais aussi pas ce que doit faire la fonction:
    def to_cfg(self):
        dfa = self.to_dfa()

        # Step 1: Give each state a grammar variable.
        variables = {
            state: f"Q{i}"
            for i, state in enumerate(dfa.states)
        }

        # Step 2: Create an empty set of rules for each variable.
        productions = {
            variables[state]: set()
            for state in dfa.states
        }

        # Step 3: Convert every transition into a grammar rule.
        for state, transitions in dfa.transitions.items():
            for symbol, target in transitions.items():
                productions[variables[state]].add(
                    (symbol, variables[target])
                )

        # Step 4: Allow the grammar to stop at accepting states.
        for state in dfa.final_states:
            productions[variables[state]].add(())

        return {
            "start": variables[dfa.initial_state],
            "productions": productions,
        }