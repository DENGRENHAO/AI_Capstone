import itertools

class MineSweeperPlayer:
    def __init__(self, game):
        # A set representing the knowledge base of the AI agent. 
        # The knowledge base contains Conjunctive Normal Form (CNF) clauses.
        self.KB = set()
        # A set representing the list of single-literal clauses representing marked cells.
        self.KB0 = set()
        # An instance of the MinesweeperGame class representing the Minesweeper game.
        self.game = game
        # A set containing the initial safe cells in the game.
        self.initial_safe_cells = self.game.get_initial_safe_cells()
        # A list containing the length of the knowledge base at each step.
        self.KB_length_history = []

        # Add negative single-literal clauses for initial safe cells to the KB
        for cell in self.initial_safe_cells:
            # print(f"Initial safe cell: {cell}")
            self.KB.add(((cell[0], cell[1], False),))

    def mark_safe(self, literal):
        '''
        Mark a cell as safe
        '''
        self.game.mark_safe(literal[0], literal[1])

    def mark_mine(self, literal):
        '''
        Mark a cell as mine
        '''
        self.game.mark_mine(literal[0], literal[1])

    def get_unmarked_neighbors_and_mine_count(self, literal):
        '''
        Get unmarked neighbors and mine count of a cell
        '''
        neighbors, mine_count = self.game.get_unmarked_neighbors_and_mine_count(literal[0], literal[1])
        return neighbors, mine_count

    def subsumption_checking(self, clause1, clause2):
        '''
        - Check for subsumption between two clauses:
            - An example of subsumption:
                (x2 or x3) is stricter than (x1 or x2 or x3): The former entails the latter.
                As a result, we do not need the less strict clause anymore.
            - clause1 is stricter than an clause2: return clause1
            - clause2 is stricter than an clause1: return clause2
            - else if there is no subsumption: return None
        '''
        clause1 = set(clause1)
        clause2 = set(clause2)
        if clause1.issubset(clause2):
            return tuple(clause1)
        elif clause2.issubset(clause1):
            return tuple(clause2)
        else:
            return None
        
    def resolve(self, clause1, clause2):
        '''
        Do resolution between two clauses using the resolution rule
        Resolution rule:
        - If two clauses have complementary literals:
            - If there is only one pair of complementary literals:
                - Apply resolution to generate a new clause.
                - Resolution applying: Remove the pair of complementary literals from the two clauses, and union the two clauses.
                - Example: (x1 or x2) and (not x1 or x3) -> (x2 or x3)
            - If there are more than one pairs of complementary literals:
                - Do nothing here. (Resolution will results in tautology (always true).)
                - Example: (not x2 or x3) and (x1 or x2 or not x3)
        '''
        clause1 = set(clause1)
        clause2 = set(clause2)

        literal_to_remove = None
        complementary_literals_cnt = 0
        for literal1 in clause1:
            if (literal1[0], literal1[1], not literal1[2]) in clause2:
                literal_to_remove = literal1
                complementary_literals_cnt += 1

        if literal_to_remove and complementary_literals_cnt == 1:
            clause1.remove(literal_to_remove)
            clause2.remove((literal_to_remove[0], literal_to_remove[1], not literal_to_remove[2]))
            return tuple(clause1.union(clause2))
        return None

    def matching_clauses(self, clause1, clause2):
        '''
        About "matching" two clauses:
        - Check for duplication or subsumption first. Keep only the more strict clause.
        - If no duplication or subsumption, do resolution.
        '''
        clause = self.subsumption_checking(clause1, clause2)
        is_strict = False
        if clause:
            is_strict = True
        else:
            clause = self.resolve(clause1, clause2)
        return clause, is_strict
        
    def unit_propagation(self, clause):
        '''
        Unit-propagation heuristic:
        - If a clause has only one literal A:
            - For each multi-literal clause in KB containing A:
                - If the two occurrences of A are both positive or both negative:
                    - Discard the multi-literal clause. It is always true. (This is a case of subsumption.)
                - Else
                    - Remove A from the multi-literal clause. This is the result of resolution.
        - Else if a clause has more than one literal:
            - Check against the single-literal clauses in KB0.
        '''
        clauses_to_add = set()
        clauses_to_remove = set()
        if len(clause) == 1:
            for clause2 in self.KB:
                if clause[0] in clause2:
                    clauses_to_remove.add(clause2)
                elif (clause[0][0], clause[0][1], not clause[0][2]) in clause2:
                    new_clause = tuple(literal for literal in clause2 if literal != (clause[0][0], clause[0][1], not clause[0][2]))
                    clauses_to_add.add(new_clause)
                    clauses_to_remove.add(clause2)
        else:
            for clause0 in self.KB0:
                if clause0[0] in clause:
                    break
                elif (clause0[0][0], clause0[0][1], not clause0[0][2]) in clause:
                    new_clause = tuple(literal for literal in clause if literal != (clause0[0][0], clause0[0][1], not clause0[0][2]))
                    clauses_to_add.add(new_clause)
        for clause_to_add in clauses_to_add:
            self.KB.add(clause_to_add)
        for clause_to_remove in clauses_to_remove:
            self.KB.remove(clause_to_remove)

    def insert_clause_to_KB(self, clause):
        '''
        About inserting a new clause to the KB:
        - Skip the insertion if there is an identical clause in KB or KB0.
        - Do unit-propagation with the new clause.
        - Do resolution of the new clause with all the clauses in KB0, if applicable. Keep only the resulting clause.
        - Check for subsumption with all the clauses in KB:
            - New clause is stricter than an existing clause: Delete the existing clause.
            - An existing clause is stricter than the new clause): Skip (no insertion).
        '''
        if clause in self.KB or clause in self.KB0:
            return None
        
        self.unit_propagation(clause)
        # Do resolution with all the clauses in KB0
        for clause0 in self.KB0:
            new_clause = self.resolve(clause, clause0)
            if not new_clause:
                break
            clause = new_clause

        # Check for subsumption with all the clauses in KB
        clause_to_remove = None
        for clause2 in self.KB:
            strict_clause = self.subsumption_checking(clause, clause2)
            if not strict_clause:
                continue
            elif strict_clause == clause:
                clause_to_remove = clause2
                break
            elif strict_clause == clause2:
                return None
            
        if clause_to_remove:
            self.KB.remove(clause_to_remove)
        self.KB.add(clause)
        return clause
    
    def generate_clauses(self, unmarked_neighbors, n):
        '''
        About generating clauses from the hints:
        - Each hint provides the following information: There are n mines in a list of m unmarked cells.
        - (n == m): Insert the m single-literal positive clauses to the KB, one for each unmarked cell.
        - (n == 0): Insert the m single-literal negative clauses to the KB, one for each unmarked cell.
        - (m > n > 0): General cases (need to generate CNF clauses and add them to the KB):
            - C(m, m-n+1) clauses, each having m-n+1 positive literals
            - C(m, n+1) clauses, each having n+1 negative literals.
            - For example, for m=5 and n=2, let the cells be x1, x2, ..., x5:
            There are C(5,4) all-positive-literal clauses:
                (x1 or x2 or x3 or x4), (x1 or x2 or x3 or x5), ..., (x2 or x3 or x4 or x5)
            There are C(5,3) all-negative-literal clauses:
                (not x1 or not x2 or not x3), (not x1 or not x2 or not x4), (not x1 or not x2 or not x5), ..., (not x3 or not x4 or not x5)
        '''
        # print("generate_clauses: unmarked_neighbors len = {}, n = {}".format(len(unmarked_neighbors), n))
        m = len(unmarked_neighbors)
        if n == m:
            for cell in unmarked_neighbors:
                self.insert_clause_to_KB(((cell[0], cell[1], True),))
        elif n == 0:
            for cell in unmarked_neighbors:
                self.insert_clause_to_KB(((cell[0], cell[1], False),))
        else:
            # Generate all-positive-literal clauses
            for combination_clause in itertools.combinations(unmarked_neighbors, m-n+1):
                self.insert_clause_to_KB(tuple((cell[0], cell[1], True) for cell in combination_clause))

            # Generate all-negative-literal clauses
            for combination_clause in itertools.combinations(unmarked_neighbors, n+1):
                self.insert_clause_to_KB(tuple((cell[0], cell[1], False) for cell in combination_clause))
        # print("finish generating clauses")

    def get_single_clause_count(self):
        '''
        Print KB, its single clause count and KB0 for debugging
        '''
        single_clause_count = 0
        for clause in self.KB:
            if len(clause) == 1:
                single_clause_count += 1
        # print(f"KB length: {len(self.KB)}, single clause count: {single_clause_count}")
        # print(f"KB0 length: {len(self.KB0)}")

    def is_stuck(self):
        '''
        Determine if the game is stucked by KB length history
        If the KB length is the same for 5 consecutive turns, then the game is stucked
        '''
        self.KB_length_history.append(len(self.KB))
        stuck_KB_length = 5
        if len(self.KB_length_history) > stuck_KB_length:
            self.KB_length_history.pop(0)
        if len(set(self.KB_length_history)) == 1 and len(self.KB_length_history) == stuck_KB_length:
            return True
        return False
    
    def make_safe_guess(self):
        '''
        make a guess if the game is stucked
        choose a guess by one of the literal in the clause with the length of 2 in KB
        if there is no clause with the length of 2, then change that to 3, 4, 5, ...
        return the guessed literal
        '''
        clause_len_limit = 2
        max_clause_len = 0
        for clause in self.KB:
            if len(clause) > max_clause_len:
                max_clause_len = len(clause)
        while(clause_len_limit <= max_clause_len):
            for clause in self.KB:
                if len(clause) == clause_len_limit:
                    for literal in clause:
                        if literal[2] == False:
                            print(f"make_safe_guess: {literal}")
                            # print(f"clause_len_limit: {clause_len_limit}, max_clause_len: {max_clause_len}, clause: {clause}")
                            return literal, clause
                        
            clause_len_limit += 1
        return None, None

    def game_move(self):
        '''
        Perform one iteration of the game.
        - Check if the game is stucked, if so, make a safe guess
            - If the guess isn't safe, then the game is over
            - Else, mark the guess as safe and continue the game
        - If there is a single-literal clause in the KB:
            - If this cell is safe:
                - Mark that cell as safe or mined on the game board.
                - Query the game control module for the hint at that cell.
                - Generate new clauses from the hint.
        - Else:
            - Apply pairwise "matching" of the clauses in the KB or 
            apply pairwise "matching" of the clauses between KB and KB0.
        '''
        # If there is a single-literal clause in the KB, move it to KB0
        single_clause_count = self.get_single_clause_count()
        if self.is_stuck() and not single_clause_count:
            guess_safe_literal, guess_clause = self.make_safe_guess()
            if not guess_safe_literal:
                return None
            self.KB.remove(guess_clause)
            self.mark_safe(guess_safe_literal)
            # Query the game control module for the hint at that cell.
            unmarked_neighbors, n = self.get_unmarked_neighbors_and_mine_count(guess_safe_literal)
            self.generate_clauses(unmarked_neighbors, n)
            self.KB0.add((guess_safe_literal,))
            return (guess_safe_literal[0], guess_safe_literal[1])
        
        single_literal_clause = None
        for clause in self.KB:
            if len(clause) == 1:
                single_literal_clause = clause
                break
                
        if single_literal_clause:
            if not single_literal_clause[0][2]:
                self.mark_safe(single_literal_clause[0])
                # Query the game control module for the hint at that cell.
                unmarked_neighbors, n = self.get_unmarked_neighbors_and_mine_count(single_literal_clause[0])
                self.generate_clauses(unmarked_neighbors, n)
            else:
                self.mark_mine(single_literal_clause[0])
            self.KB0.add(single_literal_clause)
            self.KB.remove(single_literal_clause)
            return (single_literal_clause[0][0], single_literal_clause[0][1])
    
        # Otherwise, apply pairwise matching of clauses in the KB
        # self.pairwise_matching()
        self.pairwise_matching_KB0()

        return None        

    def pairwise_matching(self):
        '''
        Apply pairwise "matching" of the clauses in the KB.
        If new clauses are generated due to resolution, insert them into the KB.
        For the step of pairwise matching, to keep the KB from growing too fast,
        only match clause pairs where one clause has only two literals.
        '''
        # print("pairwise_matching")
        KB = list(self.KB)

        # Iterate over all possible pairs of clauses in the knowledge base
        clauses_to_add = set()
        clauses_to_remove = set()
        for i in range(len(self.KB)):
            for j in range(i+1, len(self.KB)):
                # Check if one of the clauses has only two literals
                if len(KB[i]) <= 2 and len(KB[j]) <= 2:
                    new_clause, is_strict = self.matching_clauses(KB[i], KB[j])
                    if is_strict:
                        if new_clause == KB[i]:
                            clauses_to_remove.add(KB[j])
                        elif new_clause == KB[j]:
                            clauses_to_remove.add(KB[i])
                    elif new_clause:
                        clauses_to_add.add(new_clause)
        for clause in clauses_to_remove:
            self.KB.remove(clause)                
        for clause in clauses_to_add:
            self.insert_clause_to_KB(clause)

        # print("finish pairwise_matching")

    def pairwise_matching_KB0(self):
        '''
        Apply pairwise "matching" of the clauses between KB and KB0.
        If new clauses are generated due to resolution, insert them into the KB.
        '''
        # print("pairwise_matching KB0")
        
        # Iterate over all possible pairs between clauses in the knowledge base and clauses in the knowledge base 0
        KB = list(self.KB)
        KB0 = list(self.KB0)    
        clauses_to_add = set()
        clauses_to_remove = set()

        for i in range(len(KB0)):
            for j in range(len(KB)):
                if KB0[i] == KB[j]:
                    self.KB.remove(KB[j])
                    return
                
                new_clause, is_strict = self.matching_clauses(KB0[i], KB[j])
                if is_strict:
                    if new_clause == KB0[i]:
                        clauses_to_remove.add(KB[j])
                elif new_clause:
                    clauses_to_add.add(new_clause)
        for clause in clauses_to_remove:
            self.KB.remove(clause)
        for clause in clauses_to_add:
            self.insert_clause_to_KB(clause)
        

        # print("finish pairwise_matching KB0")