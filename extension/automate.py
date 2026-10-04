from automata.fa.dfa import DFA
from automata.fa.nfa import NFA
from automata.fa.gnfa import GNFA
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


import numpy as np
from PIL import Image
from pyautotrace import Bitmap
from pyautotrace import VectorFormat

class AutomataExtended(DFA):

    #Algorithme classique

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
                #Je suis pas très sur de ce côté là.
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
        if well is None: #Si le puit n'existe pas, on le crée
            well = "well"
            states.add(well)
            transitions[well] = {}

        for state in states:
            for symbol in input_symbols:
                if not symbol in transitions[state].keys():
                        transitions[state][symbol] = well

        self.input_parameters["state"] = states
        self.input_parameters["transitions"] = transitions

        return AutomataExtended(
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

        return AutomataExtended(
            states=states,
            input_symbols=input_symbols,
            transitions=transitions,
            initial_state=self.initial_state,
            final_states=final_states
        )

    def accessible_states(self, initial_state): #ça fait un parcours pour pouvoir renvoyer la liste des états accessible
        to_visit = [initial_state]
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


    def coaccessible_states(self): #Retourne l'ensemble des états coaccessible.
        states = set(self.states)
        final_states = self.final_states
        co_accessible_states = []
        visited = []
        for state in states : 
            visited = self.accessible_states(state)
            for final_state in final_states:
                if (final_state in visited) and (final_state not in co_accessible_states):
                    co_accessible_states.append(state)

        return co_accessible_states

    def trim(self): #émonde l'automate (lui enleve les etats non accessible et non coaccessible)
        accessible_states =self.accessible_states(self.initial_state)
        coaccessible_states = self.coaccessible_states()
        trimmed_states = set(accessible_states and coaccessible_states)

        if self.initial_state not in trimmed_states:
            print("The initial state is not coaccessible")
            return DFA(
                states={self.initial_state},
                input_symbols=self.input_symbols,
                transitions={'q0': {'1': 'q0'},},
                initial_state=self.initial_state,
                final_states=set(),
                allow_partial=True
        )

        trimmed_transitions = {
            state: {
                symbol: self.transitions[state][symbol]
                for symbol in self.input_symbols
                if symbol in self.transitions[state].keys()
                if self.transitions[state][symbol] in trimmed_states
            }
            for state in trimmed_states
        }        

        return AutomataExtended(
            states=trimmed_states,
            input_symbols=self.input_symbols,
            transitions=trimmed_transitions,
            initial_state=self.initial_state,
            final_states=self.final_states and trimmed_states,
            allow_partial= True  
        )


    def reverse(self):#Renverser l'automate. ça renverse pas les états initiaux et finaux tho.
        states = set(self.states)
        input_symbols = set(self.input_symbols)
        final_states = self.final_states
        transitions = {
                    state: dict(self.transitions[state])
                    for state in self.states
                }
        new_transitions = {state: {symbol: set() for symbol in input_symbols} for state in states}

        print(transitions)

        for state in states:
            for symbol in input_symbols:
                if symbol in self.transitions[state].keys():
                    destination = self.transitions[state][symbol]
                    new_transitions[destination][symbol].add(state)

        return NFA(
            states=states,
            input_symbols=input_symbols,
            transitions=new_transitions,
            initial_state=self.initial_state,
            final_states=final_states,
            allow_partial= True           
        )

    def print_pair_table(self,show_round: bool): #ça imprime la table là des paires equivalent/dinstingable

        finished : bool = False
        modified : bool = False
        states = self.states
        input_symbols = self.input_symbols
        transitions = self.transitions
        final_states = self.final_states
        print("Final states : ", final_states)
        table = {
            state1: {
                state2: None
                for state2 in states
            }
            for state1 in states
        }

        i : int= 0

        #Etats finaux/ non états finaux sont mis à zero

        for state1 in states:
            for state2 in states:
                if state1 == state2:
                    continue
                
                elif ((state1 in final_states and not state2 in final_states) 
                    or (state2 in final_states and not state1 in final_states)):
                    if show_round:  
                        table[state1][state2] = "0"
                    else :
                        table[state1][state2] = 'X'


        while not finished:
            modified = False
            for state1 in states:
                for state2 in states:
                    if state1 == state2:
                        continue

                    #Si la transition existe et qu'on l'a pas défini on le mets dans le tableau
                    for a in input_symbols:
                        if(a in transitions[state1].keys() and a in transitions[state2].keys()):
                            if (table[transitions[state1][a]][transitions[state2][a]] not in ["[]" , None]
                                and table[state1][state2] == None):

                                if show_round:
                                    table[state1][state2] = str(i)
                                else:
                                    table[state1][state2] = 'X'
                                modified = True

                                break

                    if (table[state1][state2] == None or table[state1][state2] == "[]" ):
                        table[state1][state2] = "[]"

            if not modified:
                finished = True

            i += 1

        self.print_The_actual_pair_table(table,states)

        return table
    
    def print_The_actual_pair_table(self, table : dict, states):

        #Ici ça print la pyramide;

        treated = set()

        print("      " + "   ".join(states))
      
        for row in states:
            values = []

            for col in states:
                pair = frozenset((row, col))

                if pair in treated or row == col:
                    values.append(" ")
                else:
                    value = table[row][col]
                    values.append(" " + value)

                    treated.add(pair)

            print(f"{row}   " + "   ".join(values))
        pass


    def quotient(self): #C'est l'algorithme minimize mais qui montre les ensembles qui on été assemblé.
        table = self.print_pair_table(True)
        states = set(self.states)
        transitions = {
                    state: dict(self.transitions[state])
                    for state in self.states
                }
        initial_state = self.initial_state

        #Je dois changer l'autre algo pour qu'il me donne juste un bout du triangle mdr.
        for state1 in states:
            for states2 in states:
                if table[state1][states2] == '[]':
                    states.remove(state1); states.remove(states2); states.add("{"+ state1 +" ; " + states2 + "}")
                    transitions["{"+ state1 +" ; " + states2 + "}"]= transitions[state1]
                    transitions.pop(state1), transitions.pop(states2)
                    if states2 == initial_state or state1 == initial_state:
                        initial_state = "{"+ state1 +" ; " + states2 + "}"


        return DFA(
            states=states,
            input_symbols=self.input_symbols,
            transitions=transitions,
            initial_state=initial_state,
            final_states=self.final_states
        )


    #Relation sur les automates:

    #IsDisjoint existe déjà, is_equivalent() et laguage_equal sont aussi pareil

    def is_equivalent(self,other): #Verifie si les deux languages sont equivalents
        first_automate = GNFA.from_dfa(self).to_regex()
        second_automate = GNFA.from_dfa(other).to_regex()

        return first_automate == second_automate

    def language_subset(self, other): #Verifie si le language de l'un d'entre eu est subset de l'autre
        #De base j'avais l'intention de le faire avec regex, mais je viens de me rendre compte que y a une 
        #fonction pour ça issuperset(re1, re2, *, input_symbols=None)

        not_self = self.complementarity()
        not_other = other.complementarity()
        intersection_other_in_self = not_self.intersection(other)
        intersection_self_in_other = not_other.intersection(self)

        return (intersection_other_in_self.isempty() or intersection_self_in_other.isempty())

    #J'ai pas encore fait "is isomorphic" parce que je sais pas ce que ça veut dire.


    def to_pdf(self,file_name):
        image = Image.open(file_name).convert("RGB")
        bitmap_data = np.array(image)
        bitmap = Bitmap(bitmap_data)
        vector = bitmap.trace()
        vector.save("output_image.pdf", format=VectorFormat.PDF)

    def to_svg(self, file_name):
        image = Image.open(file_name).convert("RGB")
        bitmap_data = np.array(image)
        bitmap = Bitmap(bitmap_data)
        vector = bitmap.trace()
        vector.save("output_image.svg")





        
