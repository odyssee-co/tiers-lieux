from pyomo.environ import ConcreteModel, Var, Binary, Objective, ConstraintList, Constraint, SolverFactory, maximize

def solve(saved_df, nb_offices):
    #saved_df = saved_df.iloc[:500,:15]
    model = ConcreteModel()
    model.offices = range(saved_df.shape[1])
    model.employees = range(saved_df.shape[0])
    #model.x = Var(model.employees, model.offices, bounds=(0.0,1.0) )
    model.x = Var(model.employees, model.offices, within=Binary)
    model.y = Var(model.offices, within=Binary)

    model.obj = Objective(expr=sum(saved_df.iloc[e,o]*model.x[e,o]
        for o in model.offices for e in model.employees), sense=maximize)

    #all employees chose exactly one office
    model.single_x = ConstraintList()
    for e in model.employees:
        model.single_x.add(sum(model.x[e,o] for o in model.offices) == 1)

    #an employee can only work to an office if it is selected
    model.bound_y = ConstraintList()
    for o in model.offices:
        for e in model.employees:
            model.bound_y.add(model.x[e,o] <= model.y[o])

    #nb_offices offices are selected
    model.num_facilities = Constraint(expr=sum(model.y[o] for o in model.offices)==nb_offices)

    solver = SolverFactory('glpk') #glpk is not multithreaded
    #solver = SolverFactory("cbc", options={"threads": 4}) # cbc needs to be compiled multi-threaded
    print("Running solver...")
    res = solver.solve(model)
    print(res)
