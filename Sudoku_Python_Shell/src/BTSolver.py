import SudokuBoard
import Variable
import Domain
import Trail
import Constraint
import ConstraintNetwork
import time
import random

class BTSolver:

    # ==================================================================
    # Constructors
    # ==================================================================

    def __init__ ( self, gb, trail, val_sh, var_sh, cc ):
        self.network = ConstraintNetwork.ConstraintNetwork(gb)
        self.hassolution = False
        self.gameboard = gb
        self.trail = trail

        self.varHeuristics = var_sh
        self.valHeuristics = val_sh
        self.cChecks = cc

    # ==================================================================
    # Consistency Checks
    # ==================================================================

    # Basic consistency check, no propagation done
    def assignmentsCheck ( self ):
        for c in self.network.getConstraints():
            if not c.isConsistent():
                return False
        return True

    """
        Part 1 TODO: Implement the Forward Checking Heuristic

        This function will do both Constraint Propagation and check
        the consistency of the network

        (1) If a variable is assigned then eliminate that value from
            the square's neighbors.

        Note: remember to trail.push variables before you assign them
        Return: a tuple of a dictionary and a bool. The dictionary contains all MODIFIED variables, mapped to their MODIFIED domain.
                The bool is true if assignment is consistent, false otherwise.
    """
    def forwardChecking ( self ):
        # keep track of which values were inconsistent
        variablesAfterPruning = {}
        for v in self.network.variables:                                             # For all variables:
            if v.isAssigned():      
                value = v.getAssignment()                                            # If a particular variable is assigned:
                for neighbor in self.network.getNeighborsOfVariable(v):              # Get that variable's neighbors.
                    # look for inconsistent assignments. Short circuit check with isChangeable to make sure variable can be assigned.
                    if neighbor.isChangeable and neighbor.getDomain().contains(value):

                        # push to trail to save a snapshot of variable assignments for manager function before pruning
                        self.trail.push(neighbor)

                        # then prune:
                        neighbor.removeValueFromDomain(value)

                        # store the results of the prune:
                        variablesAfterPruning[neighbor] = neighbor.getDomain()

                        # after pruning, check to see if that variable's domain is now empty:
                        if not neighbor.getDomain():
                            return (variablesAfterPruning, False)
        return (variablesAfterPruning, True)
                    
    # =================================================================
	# Arc Consistency
	# =================================================================
    def arcConsistency( self ):
        assignedVars = []
        for c in self.network.constraints:
            for v in c.vars:
                if v.isAssigned():
                    assignedVars.append(v)
        while len(assignedVars) != 0:
            av = assignedVars.pop(0)
            for neighbor in self.network.getNeighborsOfVariable(av):
                if neighbor.isChangeable and not neighbor.isAssigned() and neighbor.getDomain().contains(av.getAssignment()):
                    neighbor.removeValueFromDomain(av.getAssignment())
                    if neighbor.domain.size() == 1:
                        neighbor.assignValue(neighbor.domain.values[0])
                        assignedVars.append(neighbor)


    """
        Part 2 TODO: Implement both of Norvig's Heuristics

        This function will do both Constraint Propagation and check
        the consistency of the network

        (1) If a variable is assigned then eliminate that value from
            the square's neighbors.

        (2) If a constraint has only one possible place for a value
            then put the value there.

        Note: remember to trail.push variables before you assign them
        Return: a pair of a dictionary and a bool. The dictionary contains all variables 
		        that were ASSIGNED during the whole NorvigCheck propagation, and mapped to the values that they were assigned.
                The bool is true if assignment is consistent, false otherwise.
    """
    def norvigCheck ( self ):

        changed = True
        while changed:
            changed = False
            for v in self.network.variables:
                if v.isAssigned():
                    currentAssignment = v.getAssignment()
                    neighbors = self.network.getNeighborsOfVariable(v)
                    for neighbor in neighbors:
                        if neighbor.getDomain().contains(currentAssignment):
                            self.trail.push(neighbor)
                            neighbor.removeValueFromDomain(currentAssignment)

                            if neighbor.getDomain().size() == 0:
                                return ({}, False)
                            changed = True
                        
                        # Start check 2
                    unitConstraints = self.network.getConstraintsContainingVariable(v)

                    for uc in unitConstraints:
                        for val in range(1, 10):
                            candidateVars = []

                            for var in uc.vars:
                                if var.getDomain().contains(val):
                                    candidateVars.append(var)
                            if len(candidateVars) == 1 and not candidateVars[0].isAssigned():
                                self.trail.push(candidateVars[0])
                                candidateVars[0].assignValue(val)
                                changed = True
            return ({}, True)

    """
         Optional TODO: Implement your own advanced Constraint Propagation

         Completing the three tourn heuristic will automatically enter
         your program into a tournament.
     """
    def getTournCC ( self ):
        return False

    # ==================================================================
    # Variable Selectors
    # ==================================================================

    # Basic variable selector, returns first unassigned variable
    def getfirstUnassignedVariable ( self ):
        for v in self.network.variables:
            if not v.isAssigned():
                return v

        # Everything is assigned
        return None

    """
        Part 1 TODO: Implement the Minimum Remaining Value Heuristic

        Return: The unassigned variable with the smallest domain
    """
    def getMRV ( self ):
        best = None
        bestSize = float('inf')

        for v in self.network.variables:
            if not v.isAssigned(): #only unassigned variables
                size = v.size()
                if size < bestSize:
                    bestSize = size
                    best = v

        return best

    """
        Part 2 TODO: Implement the Minimum Remaining Value Heuristic
                       with Degree Heuristic as a Tie Breaker

        Return: The unassigned variable with the smallest domain and affecting the  most unassigned neighbors.
                If there are multiple variables that have the same smallest domain with the same number of unassigned neighbors, add them to the list of Variables.
                If there is only one variable, return the list of size 1 containing that variable.
    """
    def MRVwithTieBreaker ( self ):
        #finds minimum domain size among unassigned vars
        minsize = float('inf')
        for v in self.network.variables:
            if not v.isAssigned():
                if v.size() < minsize:
                    minsize = v.size()
        
        candidates = []
        max_unassigned_neighbors = -1

        #filter unassigned with minsize, count neighbors for each
        for v in self.network.variables:
            if not v.isAssigned() and v.size() == minsize:
                unassigned_neighbors = 0
                for neighbor in self.network.getNeighborsOfVariable(v):
                    if not neighbor.isAssigned():
                        unassigned_neighbors += 1

                #only keep maximum unassigned neighbors
                if unassigned_neighbors > max_unassigned_neighbors:
                    max_unassigned_neighbors = unassigned_neighbors
                    candidates = [v]
                elif unassigned_neighbors == max_unassigned_neighbors:
                    candidates.append(v)

        return candidates

    """
         Optional TODO: Implement your own advanced Variable Heuristic

         Completing the three tourn heuristic will automatically enter
         your program into a tournament.
     """
    def getTournVar ( self ):
        return None

    # ==================================================================
    # Value Selectors
    # ==================================================================

    # Default Value Ordering
    def getValuesInOrder ( self, v ):
        values = v.domain.values
        return sorted( values )

    """
        Part 1 TODO: Implement the Least Constraining Value Heuristic

        The Least constraining value is the one that will knock the least
        values out of it's neighbors domain.

        Return: A list of v's domain sorted by the LCV heuristic
                The LCV is first and the MCV is last
    """
    def getValuesLCVOrder ( self, v ):
        #for each value, count how many eliminations it would cause for neighbors
        value_constraints = []
        for value in v.getValues():
            elimination_count = 0
            for neighbor in self.network.getNeighborsOfVariable(v):
                if neighbor.getDomain().contains(value):
                    elimination_count += 1
            value_constraints.append((value, elimination_count))

        #sort by count of eliminations, least first
        value_constraints.sort(key=lambda x: x[1]) 

        #extract only values
        return [value for value, count in value_constraints]

    """
         Optional TODO: Implement your own advanced Value Heuristic

         Completing the three tourn heuristic will automatically enter
         your program into a tournament.
     """
    def getTournVal ( self, v ):
        return None

    # ==================================================================
    # Engine Functions
    # ==================================================================

    def solve ( self, time_left=600):
        if time_left <= 60:
            return -1

        start_time = time.time()
        if self.hassolution:
            return 0

        # Variable Selection
        v = self.selectNextVariable()

        # check if the assigment is complete
        if ( v == None ):
            # Success
            self.hassolution = True
            return 0

        # Attempt to assign a value
        for i in self.getNextValues( v ):

            # Store place in trail and push variable's state on trail
            self.trail.placeTrailMarker()
            self.trail.push( v )

            # Assign the value
            v.assignValue( i )

            # Propagate constraints, check consistency, recur
            if self.checkConsistency():
                elapsed_time = time.time() - start_time 
                new_start_time = time_left - elapsed_time
                if self.solve(time_left=new_start_time) == -1:
                    return -1
                
            # If this assignment succeeded, return
            if self.hassolution:
                return 0

            # Otherwise backtrack
            self.trail.undo()
        
        return 0

    def checkConsistency ( self ):
        if self.cChecks == "forwardChecking":
            return self.forwardChecking()[1]

        if self.cChecks == "norvigCheck":
            return self.norvigCheck()[1]

        if self.cChecks == "tournCC":
            return self.getTournCC()

        else:
            return self.assignmentsCheck()

    def selectNextVariable ( self ):
        if self.varHeuristics == "MinimumRemainingValue":
            return self.getMRV()

        if self.varHeuristics == "MRVwithTieBreaker":
            return self.MRVwithTieBreaker()[0]

        if self.varHeuristics == "tournVar":
            return self.getTournVar()

        else:
            return self.getfirstUnassignedVariable()

    def getNextValues ( self, v ):
        if self.valHeuristics == "LeastConstrainingValue":
            return self.getValuesLCVOrder( v )

        if self.valHeuristics == "tournVal":
            return self.getTournVal( v )

        else:
            return self.getValuesInOrder( v )

    def getSolution ( self ):
        return self.network.toSudokuBoard(self.gameboard.p, self.gameboard.q)
