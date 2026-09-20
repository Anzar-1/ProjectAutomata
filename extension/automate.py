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
                print(transitions[a].keys())
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

    def thereIsAWell(self):
        params = self.input_parameters
        states = params["states"]
        well = None

        for state in states:
            if self.isAWell(state):
                well = state

        return well


    def completion(self):
        if not self.isComplete():
            return #ça renvoie None

        params = self.input_parameters
        states = params["states"]
        input_symbols = params["input_symbols"]
        transitions = params["transitions"]

        #Tu check si tout les états on une transition vers chacun des etats
        for a in states:
            for b in input_symbols:
                #Si il existe une transition de a vers b, on la crée la transition vers un état puit.
                #Jsp is je fais genre, je cherche si de base y a un etat non accepteur dont toute les transition
                #mène a lui même, et je l'utilise, sinon je le crée, où je crée un truc dans tout les 
                #cas et je minimize l'automate
                pass
        pass
        #Après je creer une nouvelle automate avec ces parametres et je la renvoie
    

    def complementarity(self):
        self.completion()
        params = self.input_parameters
        states = params["states"]
        final_state = params["final_states"]

        #Je check si l'état est dans final states. si il l'est, je l'enleve, si il ne l'est pas, je le mets dedans
        for a in states:
            pass
        
        #Après je creer une nouvelle automate avec ces parametres et je la renvoie