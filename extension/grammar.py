from automata.fa.dfa import DFA
from automata.fa.nfa import NFA
from automata.fa.gnfa import GNFA
from automata.pda.pda import PDA
import automata.fa.fa as fa
import graphviz
import random
from collections import deque


class GrammarValidationError(Exception):
    """Raised when a grammar definition is invalid."""
    pass

class Grammar():

    #-------------------------------------------
        #Constructeur
    #-------------------------------------------
    

    def __init__(self, variables, terminals, productions, start_variable):
        self.variables = set(variables)
        self.terminals = set(terminals)
        self.productions = productions
        self.start_variable = start_variable
        self.validate()

    def validate(self):
        if self.start_variable not in self.variables:
            raise GrammarValidationError("Start symbol must be one of the variables.")
        if not self.variables.isdisjoint(self.terminals):
            raise GrammarValidationError("Variables and terminals must be disjoint sets.")
        for lhs, rhs_list in self.productions.items():
            if lhs not in self.variables:
                raise GrammarValidationError(f"Left-hand side '{lhs}' must be a variable.")
            for rhs in rhs_list:
                for symbol in rhs:
                    if symbol != '' and symbol not in self.variables and symbol not in self.terminals:
                        raise GrammarValidationError(f"Symbol '{symbol}' in production is neither variable nor terminal.")

    class ParseTree:
        def __init__(self, root):
            self.root = root  # Node or Leaf

        def to_dot(self):
            dot = ["digraph ParseTree {", "  node [fontname=\"Helvetica\"];"]
            counter = [0]

            def traverse(node):
                node_id = f"node_{counter[0]}"
                counter[0] += 1
                label = node.symbol if node.symbol != '' else 'ε'
                dot.append(f'  {node_id} [label="{label}"];')

                if hasattr(node, 'children'):
                    for child in node.children:
                        child_id, child_dot = traverse(child)
                        dot.extend(child_dot)
                        dot.append(f'  {node_id} -> {child_id};')
                return node_id, dot

            traverse(self.root)
            dot.append("}")
            return "\n".join(dot)

        def to_svg(self, filename=None):
            try:
                src = graphviz.Source(self.to_dot())
                if filename:
                    src.render(filename, format='svg', cleanup=True)
                return src.pipe(format='svg').decode('utf-8')
            except ImportError:
                raise ImportError("The 'graphviz' package is required for drawing parse trees. Run `pip install graphviz`.")

        def draw(self):
            try:
                src = graphviz.Source(self.to_dot())
                return src.view()
            except ImportError:
                raise ImportError("The 'graphviz' package is required for rendering.")

    class Node:
        def __init__(self, symbol, children=None):
            self.symbol = symbol
            self.children = children or []

    class Leaf:
        def __init__(self, symbol):
            self.symbol = symbol

    # Extension methods for CFG / Grammar derivation & parsing
    def _derivation_step(sentential_form, cfg, leftmost=True):
        for i, symbol in enumerate(sentential_form):
            if symbol in cfg.variables:
                target_idx = i
                target_var = symbol
                if leftmost:
                    break # take the first one found
                else:
                    # keep searching for rightmost
                    continue
        else:
            return None, None

        # For a robust search, choose a production rule for target_var
        return target_var, target_idx

    def parse(self, cfg, target_word):
        target_tokens = list(target_word) if isinstance(target_word, str) else list(target_word)

        def parse_symbol(symbol, tokens):
            if symbol in cfg.terminals:
                if tokens and tokens[0] == symbol:
                    return [(self.Leaf(symbol), tokens[1:])]
                return []

            if symbol == "":
                if not tokens:
                    return [(self.Leaf(""), tokens)]
                return []

            results = []
            for rhs in cfg.productions.get(symbol, []):
                current_tokens = tokens
                valid = True
                sub_nodes = []

                for sym in rhs:
                    if sym == "":
                        sub_nodes.append(self.Leaf(""))
                        continue

                    matches = parse_symbol(sym, current_tokens)
                    if not matches:
                        valid = False
                        break

                    node, current_tokens = matches[0]
                    sub_nodes.append(node)

                if valid:
                    results.append((self.Node(symbol, sub_nodes), current_tokens))

            return results

        matches = parse_symbol(cfg.start_variable, target_tokens)
        for root_node, rem_tokens in matches:
            if not rem_tokens:
                return self.ParseTree(root_node)

        raise ValueError(f"Word '{target_word}' cannot be parsed by the grammar.")

    def derive(self, sentential_form, index, replacement):
        """Apply one listed production to a variable at the given index."""
        sentential_form = tuple(sentential_form)
        replacement = tuple(replacement)
    
        if index < 0 or index >= len(sentential_form):
            raise IndexError("index is outside the sentential form")
    
        variable = sentential_form[index]
        if variable not in self.variables:
            raise ValueError(f"Symbol at index {index} is not a variable: {variable!r}")
    
        if replacement not in self.productions.get(variable, []):
            raise ValueError(
                f"{replacement!r} is not a production for variable {variable!r}"
            )
    
        # Treat ("",) as epsilon, represented by no symbols in the sentential form.
        replacement = tuple(symbol for symbol in replacement if symbol != "")
    
        return sentential_form[:index] + replacement + sentential_form[index + 1:]

    def _find_derivation(self, target_word, leftmost, max_steps=25, max_length=None):
        target = tuple(target_word) if not isinstance(target_word, str) else tuple(target_word)
        start = (self.start_variable,)

        if max_length is None:
            max_length = len(target) + 10

        queue = deque([(start, [start])])
        visited = {start}

        while queue:
            form, history = queue.popleft()

            if form == target:
                return [
                    " ".join(step) if step else "ε"
                    for step in history
                ]

            if len(history) - 1 >= max_steps:
                continue

            variable_indices = [
                i for i, symbol in enumerate(form)
                if symbol in self.variables
            ]

            if not variable_indices:
                continue

            index = variable_indices[0] if leftmost else variable_indices[-1]
            variable = form[index]

            for rhs in self.productions.get(variable, []):
                # An empty tuple, or ("",), represents ε.
                replacement = tuple(symbol for symbol in rhs if symbol != "")
                new_form = form[:index] + replacement + form[index + 1:]

                if len(new_form) > max_length or new_form in visited:
                    continue

                visited.add(new_form)
                queue.append((new_form, history + [new_form]))

        
        raise ValueError(f"No derivation found for word: {target_word}")
        



    def leftmost_derivation(self, target_word, max_steps=25, max_length=None):
        return self._find_derivation(
            target_word, leftmost=True,
            max_steps=max_steps, max_length=max_length
        )


    def rightmost_derivation(self, target_word, max_steps=25, max_length=None):
        return self._find_derivation(
            target_word, leftmost=False,
            max_steps=max_steps, max_length=max_length
        )


class RegularGrammar(Grammar):
    """Regular Grammar (Type 3): Productions are A -> aB, A -> a, or A -> epsilon."""

    def __init__(self, variables, terminals, productions, start_variable):
        super().__init__(variables, terminals, productions, start_variable)
        self.validate()

    def validate(self):
        for lhs, rhs_list in self.productions.items():
            for rhs in rhs_list:
                # Check right-regular or left-regular constraints (e.g. A -> aB or A -> a)
                if len(rhs) > 2:
                    raise GrammarValidationError("Regular grammar productions can have at most 2 symbols on RHS.")
                if len(rhs) == 2 and not (rhs[0] in self.terminals and rhs[1] in self.variables):
                    raise GrammarValidationError("Right-regular rule must be of form Variable -> Terminal Variable.")
                if len(rhs) == 1 and rhs[0] not in self.terminals and rhs[0] != '':
                    raise GrammarValidationError("Single-symbol RHS in regular grammar must be a terminal or epsilon ('').")
    
    def grammar_to_nfa(self ) -> NFA:
        """Converts a Regular Grammar to an equivalent Nondeterministic Finite Automaton (NFA)."""
        states = self.variables.copy()
        accept_state = "q_accept"
        states.add(accept_state)

        transitions = {state: {} for state in states}

        for lhs, rhs_list in self.productions.items():
            for rhs in rhs_list:
                if len(rhs) == 1:
                    term = rhs[0] if rhs[0] != '' else ''
                    if accept_state not in transitions[lhs].setdefault(term, set()):
                        transitions[lhs][term].add(accept_state)
                elif len(rhs) == 2:
                    term, var = rhs[0], rhs[1]
                    if var not in transitions[lhs].setdefault(term, set()):
                        transitions[lhs][term].add(var)

        return NFA(
            states=states,
            input_symbols=self.terminals,
            transitions=transitions,
            initial_state=self.start_variable,
            final_states={accept_state}
        )





class ContextFreeGrammar(Grammar):

    def __init__(self, variables, terminals, productions, start_variable):
            super().__init__(variables, terminals, productions, start_variable)

    #Je viens de voir que ça est pas fini.
    def grammar_to_pda(self) -> PDA:
        """Converts a Context-Free Grammar to an equivalent Pushdown Automaton (PDA) via empty stack / final state."""
        # Standard PDA conversion construction (single state q, transitions for variables and terminals)
        states = {'q0', 'q1', 'q2'}
        input_symbols = self.terminals
        stack_symbols = self.variables.union(self.terminals).union({'$'})

        # Define transitions matching CFG production rules...
        transitions = {
            'q0': {
                '': {
                    '$': {('q1', tuple([self.start_variable, '$']))}
                }
            },
            'q1': {
                # Add variable expansion and terminal matching transitions here
            },
            'q2': {}
        }

        return PDA(
            states=states,
            input_symbols=input_symbols,
            stack_symbols=stack_symbols,
            transitions=transitions,
            initial_state='q0',
            initial_stack_symbol='$',
            final_states={'q2'}
        )


class ContextSensitiveGrammar(Grammar):
    pass


class UnrestrictedGrammar(Grammar):
    pass

