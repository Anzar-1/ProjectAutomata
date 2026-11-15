from automata.fa.dfa import DFA
from automata.fa.nfa import NFA
from automata.fa.gnfa import GNFA
import automata.fa.fa as fa

class Language():

    REGEX_OPERATORS = {"|", "*", "(", ")", "ε", "∅", "?"}

    #-------------------------------------------
    #Constructeur
    #-------------------------------------------

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

    #-------------------------------------------
    #autre fonctions
    #-------------------------------------------

    def accept(self ,word): #Je suis pas trop sûr de ce que language veut dire
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

    def _replace_with_nfa(self, nfa):
        """Store an equivalent regex for an NFA in this Language."""
        dfa = DFA.from_nfa(nfa)
        self.regex = GNFA.from_dfa(dfa).to_regex()
        self.alphabet = set(dfa.input_symbols)
    
    
    def reverse(self):
        nfa = NFA.from_regex(
            self.regex,
            input_symbols=self.alphabet,
        )
        reversed_nfa = nfa.reverse()
        self._replace_with_nfa(reversed_nfa)
    
    
    def concatenate(self, other):
        nfa1 = NFA.from_regex(self.regex, input_symbols=self.alphabet)
        nfa2 = NFA.from_regex(other.regex, input_symbols=other.alphabet)
    
        combined_nfa = nfa1.concatenate(nfa2)
        self.alphabet = self.alphabet | other.alphabet
        self._replace_with_nfa(combined_nfa)
    
    
    def union(self, other):
        nfa1 = NFA.from_regex(self.regex, input_symbols=self.alphabet)
        nfa2 = NFA.from_regex(other.regex, input_symbols=other.alphabet)
    
        combined_nfa = nfa1.union(nfa2)
        self.alphabet = self.alphabet | other.alphabet
        self._replace_with_nfa(combined_nfa)
    
    
    def shuffle(self, other):
        nfa1 = NFA.from_regex(self.regex, input_symbols=self.alphabet)
        nfa2 = NFA.from_regex(other.regex, input_symbols=other.alphabet)
    
        combined_nfa = nfa1.shuffle_product(nfa2)
        self.alphabet = self.alphabet | other.alphabet
        self._replace_with_nfa(combined_nfa)
    

    def star(self):
        return Language(
            self.alphabet,
            f"({self.regex})*"
        )

    #! alors j'ai pas vérifier ça, c'est l'ia qui me l'a pondu , Je sais aussi pas ce que doit faire la fonction:
    def to_cfg(self):
        dfa = self.to_dfa()
    
        # Assign one grammar variable to each DFA state.
        # Using the state's index avoids relying on the state object's name.
        states = list(dfa.states)
        variables = {
            state: f"Q{i}"
            for i, state in enumerate(states)
        }
    
        # Start with no productions for each variable.
        productions = {
            variables[state]: set()
            for state in states
        }
    
        # For each DFA transition:
        #   state --symbol--> target
        # add the grammar rule:
        #   Q_state -> symbol Q_target
        for state in states:
            for symbol, target in dfa.transitions.get(state, {}).items():
                productions[variables[state]].add(
                    (symbol, variables[target])
                )
    
        # A final DFA state can stop, so add an epsilon production.
        for state in dfa.final_states:
            productions[variables[state]].add(())
    
        return {
            "start": variables[dfa.initial_state],
            "productions": productions,
        }
    