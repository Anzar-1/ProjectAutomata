from automata.fa.dfa import DFA
import automata.fa.fa as fa
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

class AutomataExtended(DFA):

    def __init__(self,*,states: AbstractSet[fa.FAStateT],input_symbols: AbstractSet[str],
                 transitions:  Mapping[fa.FAStateT, Mapping[str, fa.FAStateT]],
                 initial_state: fa.FAStateT,final_states: AbstractSet[fa.FAStateT],allow_partial: bool = False,) -> None:
        super().__init__(
            states=states,
            input_symbols=input_symbols,
            transitions=transitions,
            initial_state=initial_state,
            final_states=final_states,
            allow_partial=allow_partial,
        )   


    def isComplete(self) -> bool: #Fonction qui vérifie si l'algorithme est complet.
        params = self.input_parameters
        states = params["states"]
        input_symbols = params["input_symbols"]
        transitions = params["transitions"]
        isComplete = True

        #Tu check si tout les états on une transition vers chacun des etats
    
        for a in states:
            for symbol in input_symbols:
                if not symbol in transitions[a].keys():
                    isComplete = False

        return isComplete

    def isAWell(self, node) -> bool : #fonction qui vérifie si le noeud est un puit.
        params = self.input_parameters
        input_symbols = params["input_symbols"]
        transitions = params["transitions"]
        isAWell = True
        for symbol in input_symbols:
            if symbol in transitions[node].keys():
                if transitions[node][symbol] != node:
                    isAWell = False
            else:
                isAWell = False

        return isAWell

    def thereIsAWell(self): #fonction qui vérifie si l'automate a un noeud puit
        params = self.input_parameters
        states = params["states"]
        well = None

        for state in states:
            if self.isAWell(state):
                well = state

        return well


    def completion(self): #Complete l'automate
        if self.isComplete():
            return self

        params = self.input_parameters
        states = set(self.states)
        input_symbols = set(self.input_symbols)
        transitions = {
            state: dict(self.transitions[state])
            for state in self.states }


        well = self.thereIsAWell()
        if well is None: #Si l epuit n'existe pas, on le crée
            well = "well"
            states.add(well)
            transitions[well] = {}

        #Alors, ça va pas marcher parce que c'est des frozen dictionary. 
        #Je sais pas trop comment les copier pour l'instant
        for state in states:
            for symbol in input_symbols:
                if not symbol in transitions[state].keys():
                        transitions[state][symbol] = well

        self.input_parameters["state"] = states
        self.input_parameters["transitions"] = transitions

        return DFA(
            states=states,
            input_symbols=input_symbols,
            transitions=transitions,
            initial_state=self.initial_state,
            final_states=set(self.final_states)
        )
    

    def complementarity(self): #Donne la complementaire de l'automate
        self = self.completion()
        states = set(self.states)
        input_symbols = set(self.input_symbols)

        transitions = {
            state: dict(self.transitions[state])
            for state in self.states
        }

        final_states = states - set(self.final_states)

        return DFA(
            states=states,
            input_symbols=input_symbols,
            transitions=transitions,
            initial_state=self.initial_state,
            final_states=final_states
        )

    def accessible_states(self): #ça fait un parcours pour pouvoir renvoyer la liste des états accessible
        to_visit = [self.initial_state]
        visited = set()

        while to_visit:
            state = to_visit.pop()

            if state in visited:
                continue

            visited.add(state)

            for symbol in self.input_symbols:
                if symbol in self.transitions[state].keys():
                    next_state = self.transitions[state][symbol]

                    if next_state not in visited:
                        to_visit.append(next_state)

        return visited

        
