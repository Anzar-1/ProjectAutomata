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

import json
from collections import defaultdict
from pyvis.network import Network


import numpy as np
from PIL import Image
from potrace import Bitmap, POTRACE_TURNPOLICY_MINORITY 

class AutomataExtended(DFA):

    #-------------------------------------------------------
    #Algorithme classique
    #-------------------------------------------------------

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

        return DFA.from_nfa(NFA(
            states=states,
            input_symbols=input_symbols,
            transitions=new_transitions,
            initial_state=self.initial_state,
            final_states=final_states,
            allow_partial= True           
        ))

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
        states = self.states
        new_states = set(self.states)
        transitions = {
                    state: dict(self.transitions[state])
                    for state in self.states
                }
        initial_state = self.initial_state
        final_states = set(self.final_states)
        treated = set()

        print("final state : type : ", type(final_states))

        #Je dois changer l'autre algo pour qu'il me donne juste un bout du triangle mdr.
        for state1 in states:
            for states2 in states:
                pair = frozenset((state1, states2))
                if table[state1][states2] == '[]' and pair not in treated:

                    new_states.remove(state1); new_states.remove(states2); 
                    new_states.add("{"+ state1 +" ; " + states2 + "}")

                    for state in states:
                        for a in self.input_symbols:
                            if transitions[state][a] == state1 or transitions[state][a] == states2:
                                transitions[state][a] = "{"+ state1 +" ; " + states2 + "}"

                    transitions["{"+ state1 +" ; " + states2 + "}"]= transitions[state1]
                    transitions.pop(state1), transitions.pop(states2)

                    treated.add(pair)

                    if states2 == initial_state or state1 == initial_state:
                        initial_state = "{"+ state1 +" ; " + states2 + "}"

                    if state1 in final_states and states2 in final_states:
                        final_states.add("{"+ state1 +" ; " + states2 + "}")                        
                        final_states.remove(state1)
                        final_states.remove(states2)
                    elif state1 in final_states:
                        final_states.remove(state1)
                    elif states2 in final_states:
                        final_states.remove(states2)

        return DFA(
            states=new_states,
            input_symbols=self.input_symbols,
            transitions=transitions,
            initial_state=initial_state,
            final_states=final_states,
            allow_partial=True
        )

    #-------------------------------------------------------
    #Relation sur les automates:
    #-------------------------------------------------------

    def is_isomorphic(self, other) -> bool:
        regex1 = GNFA.from_dfa(self).to_regex()
        regex2 = GNFA.from_dfa(other).to_regex()

        nbrState1 =  len(self.states)
        nbrState2 =  len(other.states)

        alphabet1 = self.input_symbols
        alphabet2 = other.input_symbols

        finalState1 = len(self.final_states)
        finalState2 = len(other.final_states)

        return regex1 == regex2 and nbrState1 == nbrState2 and alphabet1 == alphabet2 and finalState1 == finalState2


    def is_equivalent(self,other) -> bool: #Verifie si les deux languages sont equivalents
        first_automate = GNFA.from_dfa(self).to_regex()
        second_automate = GNFA.from_dfa(other).to_regex()

        return first_automate == second_automate
    
    def laguage_equal(self,other) -> bool: #Verifie si les deux languages sont equivalents
            first_automate = GNFA.from_dfa(self).to_regex()
            second_automate = GNFA.from_dfa(other).to_regex()
    
            return first_automate == second_automate

    def language_disjoint(self, other) -> bool:
        return self.isdisjoint(other)

    def language_subset(self, other) -> bool: #Verifie si le language de l'un d'entre eu est subset de l'autre
        #De base j'avais l'intention de le faire avec regex, mais je viens de me rendre compte que y a une 
        #fonction pour ça issuperset(re1, re2, *, input_symbols=None)

        not_self = self.complementarity()
        not_other = other.complementarity()
        intersection_other_in_self = not_self.intersection(other)
        intersection_self_in_other = not_other.intersection(self)

        return (intersection_other_in_self.isempty() or intersection_self_in_other.isempty())

    #J'ai pas encore fait "is isomorphic" parce que je sais pas ce que ça veut dire.

    #-------------------------------------------------------
    #Transformation vers d'autres formats
    #-------------------------------------------------------

    def to_pdf(self,file_name):
        image = Image.open(file_name).convert("RGB")
        image.save("output.pdf")

    def to_TikZ(self, file_name): #Je sais pas trop encore pour ça.
        img = Image.open(file_name).convert("RGB")

        with open("output.tex", "w") as f:
            f.write(r"\begin{tikzpicture}" + "\n")

            for y in range(img.height):
                for x in range(img.width):
                    r, g, b = img.getpixel((x, y))

                    if (r, g, b) != (255, 255, 255):
                        f.write(
                            f"\\fill[fill={{rgb,255:red,{r};green,{g};blue,{b}}}] "
                            f"({x},{-y}) rectangle ({x+1},{-y-1});\n"
                        )

            f.write(r"\end{tikzpicture}" + "\n")

    def to_svg(self, filename):
        try:
            image = Image.open(filename)
        except IOError:
            print("Image (%s) could not be loaded." % filename)
            return

        bm = Bitmap(image, blacklevel=0.5)
        # bm.invert()
        plist = bm.trace(
            turdsize=2,
            turnpolicy=POTRACE_TURNPOLICY_MINORITY,
            alphamax=1,
            opticurve=False,
            opttolerance=0.2,
        )
        with open(f"output.svg", "w") as fp:
            fp.write(
                f'''<svg version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{image.width}" height="{image.height}" viewBox="0 0 {image.width} {image.height}">''')
            parts = []
            for curve in plist:
                fs = curve.start_point
                parts.append(f"M{fs.x},{fs.y}")
                for segment in curve.segments:
                    if segment.is_corner:
                        a = segment.c
                        b = segment.end_point
                        parts.append(f"L{a.x},{a.y}L{b.x},{b.y}")
                    else:
                        a = segment.c1
                        b = segment.c2
                        c = segment.end_point
                        parts.append(f"C{a.x},{a.y} {b.x},{b.y} {c.x},{c.y}")
                parts.append("z")
            fp.write(f'<path stroke="none" fill="black" fill-rule="evenodd" d="{"".join(parts)}"/>')
            fp.write("</svg>")

    #-------------------------------------------------------
    #Run et animation
    #-------------------------------------------------------

    def run(self,word: str):
        state= self.initial_state
        path: list =[]; path.append(state)
        transitions = {
                            state: dict(self.transitions[state])
                            for state in self.states
                        }
        alphabet = self.input_symbols
        i: int = 0

        while(i!=len(word) and word[i] in alphabet and word[i] in transitions[state]):
            state = transitions[state][word[i]]
            path.append(state)
            i+=1

        if state in self.final_states:
            path.append("accept")
        else:
            path.append("reject")

        print(f" " + " -> ".join(path))

        return path


    def animate(self, input_string, delay=800, output="dfa.html"):
        # Get the execution trace from your existing run() method.
        path = self.run(input_string)
        accepted = True if path[len(path)-1 ]== 'accept' else False

        # Create the graph.
        net = Network(
            height="600px",
            width="100%",
            directed=True,
            bgcolor="#ffffff",
            font_color="#222222",
            cdn_resources="in_line",
        )

        # Group transitions with the same source and destination.
        grouped = defaultdict(list)
        for source, transitions in self.transitions.items():
            for symbol, target in transitions.items():
                grouped[(source, target)].append(symbol)

        # Add states.
        states = set(self.transitions)
        for transitions in self.transitions.values():
            states.update(transitions.values())

        for state in states:
            is_final = state in self.final_states

            net.add_node(
                state,
                label=state,
                shape="circle",
                size=30,
                color={
                    "background": "#dcfce7" if is_final else "#e5e7eb",
                    "border": "#16a34a" if is_final else "#6b7280",
                },
                borderWidth=3 if is_final else 1,
            )

        # Add labeled, directed edges with stable IDs.
        edge_ids = {}
        for index, ((source, target), symbols) in enumerate(grouped.items()):
            edge_id = f"edge_{index}"
            edge_ids[(source, target)] = edge_id

            net.add_edge(
                source,
                target,
                id=edge_id,
                label=", ".join(sorted(symbols)),
                arrows="to",
                color="#9ca3af",
                width=2,
            )

        # Mark the initial state with an incoming arrow.
        net.add_node("__start__", label="", shape="text")
        net.add_edge("__start__", self.initial_state, arrows="to")

        # Generate the HTML graph.
        html = net.generate_html()

        # Determine which transitions the input actually follows.
        steps = []
        for i, symbol in enumerate(input_string):
            source = path[i]
            target = path[i + 1]
            steps.append({
                "state": source,
                "next": target,
                "symbol": symbol,
                "edge": edge_ids[(source, target)],
            })

        animation_data = json.dumps({
            "steps": steps,
            "path": path,
            "accepted": accepted,
            "delay": delay,
        })

        # Add JavaScript that animates the existing graph.
        script = f"""
        <div style="padding:12px;font-family:Arial,sans-serif">
            <button id="play">▶ Play animation</button>
            <button id="reset">↺ Reset</button>
            <span id="status" style="margin-left:16px">
                Ready to run
            </span>
        </div>

        <script>
        (() => {{
            const data = {animation_data};
            const originalNodes = nodes.get();
            const originalEdges = edges.get();

            let timer = null;

            function reset() {{
                if (timer !== null) clearTimeout(timer);
                timer = null;

                nodes.update(originalNodes.map(n => ({{
                    id: n.id,
                    color: n.color
                }})));

                edges.update(originalEdges.map(e => ({{
                    id: e.id,
                    color: e.color,
                    width: e.width
                }})));

                document.getElementById("status").textContent =
                    "Ready to run";
            }}

            function play() {{
                reset();
                let i = 0;

                function step() {{
                    if (i >= data.steps.length) {{
                        const last = data.path[data.path.length - 1];
                        nodes.update({{
                            id: last,
                            color: {{
                                background: data.accepted
                                    ? "#86efac" : "#fca5a5",
                                border: data.accepted
                                    ? "#15803d" : "#dc2626"
                            }}
                        }});

                        document.getElementById("status").textContent =
                            data.accepted ? "Accepted ✓" : "Rejected ✗";
                        timer = null;
                        return;
                    }}

                    const s = data.steps[i];

                    nodes.update({{
                        id: s.state,
                        color: {{
                            background: "#fde68a",
                            border: "#d97706"
                        }}
                    }});

                    edges.update({{
                        id: s.edge,
                        color: "#2563eb",
                        width: 5
                    }});

                    document.getElementById("status").textContent =
                        "Reading '" + s.symbol + "': " +
                        s.state + " → " + s.next;

                    timer = setTimeout(() => {{
                        nodes.update({{
                            id: s.state,
                            color: {{ background: "#e5e7eb",
                                      border: "#6b7280" }}
                        }});

                        edges.update({{
                            id: s.edge,
                            color: "#9ca3af",
                            width: 2
                        }});

                        nodes.update({{
                            id: s.next,
                            color: {{ background: "#bfdbfe",
                                      border: "#2563eb" }}
                        }});

                        i++;
                        timer = setTimeout(step, data.delay);
                    }}, data.delay);
                }}

                step();
            }}

            document.getElementById("play").onclick = play;
            document.getElementById("reset").onclick = reset;
        }})();
        </script>
        """

        html = html.replace("</body>", script + "</body>")

        with open(output, "w", encoding="utf-8") as f:
            f.write(html)

        return html
        
        
