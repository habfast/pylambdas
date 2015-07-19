from abc import ABCMeta


class Exp(object):
    __metaclass__ = ABCMeta


class Zero(Exp):
    def __init__(self):
        pass

    def get(self):
        return 0

    def __repr__(self):
        return "0"


class Incr(Exp):
    def __init__(self, val):
        self.val = val

    def get(self):
        return self.val.get() + 1

    def eval(self, locals):
        val = eval_exp(self.val, locals)
        if isinstance(val, Substr):
            return val.val
        return Incr(val)

    def __repr__(self):
        try:
            return unicode(self.get())
        except:
            return "Incr({})".format(self.val)


class Positive(Exp):
    def __init__(self, exp):
        self.exp = exp

    def __repr__(self):
        return "Positive({})".format(self.exp)


class Substr(Exp):
    def __init__(self, val):
        self.val = val

    def get(self):
        return self.val.get() - 1

    def eval(self, locals):
        val = eval_exp(self.val, locals)
        if isinstance(val, (Zero, Substr)):
            return Substr(val)
        return val.val

    def __repr__(self):
        try:
            return unicode(self.get())
        except:
            return "Substr({})".format(self.val)


class If(Exp):
    def __init__(self, val, exp1, exp2):
        self.val = val
        self.exp1 = exp1
        self.exp2 = exp2

    def __repr__(self):
        return "If({}, {}, {})".format(self.val, self.exp1, self.exp2)


class App(Exp):
    def __init__(self, exp, *args):
        self.exp = exp
        self.args = args

    def eval(self, locals):
        lambda_expr = eval_exp(self.exp, locals)
        return eval_exp(
            lambda_expr.exp,
            applyBinds(
                zip(
                    lambda_expr.vars,
                    map(lambda arg: eval_exp(arg, locals), self.args)
                ),
                locals
            )
        )

    def __repr__(self):
        return "App({}, {})".format(self.exp, self.args)


class Var(Exp):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "Var({})".format(self.name)


class Lambda(Exp):
    def __init__(self, vars, exp):
        self.vars = vars
        self.exp = exp

    def __repr__(self):
        return "Lambda({}, exp)".format(self.vars, self.exp)


class Let(Exp):
    def __init__(self, binds, exp):
        self.binds = binds
        self.exp = exp

    def __repr__(self):
        return "Let"


# returns a new dictionary, same as local but with added bindings
def applyBinds(binds, local):
    return dict(
        local,
        **dict([(bind[0], bind[1]) for bind in binds])
    )


def eval_exp(exp, local):
    res = {
        Zero: lambda: exp,
        Incr: lambda: exp.eval(local),
        Positive: lambda: Incr(Zero()) if isinstance(eval_exp(exp.exp, local), Incr) else Zero(),
        Substr: lambda: exp.eval(local),
        Let: lambda: eval_exp(exp.exp, applyBinds(exp.binds, local)),
        Var: lambda: eval_exp(local[exp.name], local),
        Lambda: lambda: exp,  # lambdas don't do anything, Apps evaluate them.
        App: lambda: exp.eval(local),
        If: lambda:
        eval_exp(exp.exp1, local)
        if type(eval_exp(exp.val, local)) != Zero
        else eval_exp(exp.exp2, local),
    }[type(exp)]()
    return res

binds = [
    ("not", Lambda(
        ('val',),
        If(
            Var("val"),
            Zero(),
            Incr(Zero()),
        )
    ),),
    ("or", Lambda(
        ('val1', "val2"),
        If(
            Var("val1"),
            Incr(Zero()),
            Var("val2"),
        )
    ),),
    ("and", Lambda(
        ('val1', "val2"),
        If(
            Var("val1"),
            Var("val2"),
            Zero(),
        )
    ),),
    ("eq", Lambda(
        ('x', 'y'),
        If(
            Var("x"),
            If(
                Positive(Var("x")),
                App(Var("eq"), Substr(Var("x")), Substr(Var("y"))),
                App(Var("eq"), Incr(Var("x")), Incr(Var("y")))
            ),
            App(Var("not"), Var("y"))
        )
    ),),
    ("plus", Lambda(
        ('x', 'y'),
        If(
            Var("x"),
            If(
                Positive(Var("x")),
                App(Var("plus"), Substr(Var("x")), Incr(Var("y"))),
                App(Var("plus"), Incr(Var("x")), Substr(Var("y"))),
            ),
            Var("y")
        )
    ),),
    ("minus", Lambda(
        ('x', 'y'),
        If(
            Var("y"),
            If(
                Positive(Var("y")),
                App(Var("minus"), Substr(Var("x")), Substr(Var("y"))),
                App(Var("minus"), Incr(Var("x")), Incr(Var("y"))),
            ),
            Var("x")
        )
    ),),
    ("mult", Lambda(
        ("x", "y"),
        If(
            Var("x"),
            App(
                If(Positive(Var("x")), Var("plus"), Var("minus")),
                Var("y"),
                App(
                    Var("mult"),
                    If(Positive(Var("x")), Substr(Var("x")), Incr(Var("x"))),
                    Var("y")
                )
            ),
            Zero()
        )
    )),
    ("21", Incr(
        App(
            Var("mult"),
            Incr(Incr(Incr(Incr(Zero())))),  # 4
            Incr(Incr(Incr(Incr(Incr(Zero())))))  # 5
        )
    )),
    ("fib", Lambda(
        "n",
        If(
            App(Var("and"), Var("n"), Substr(Var("n"))),
            Let(
                (("fib2", Lambda(
                    ("a", "incr1", "incr2"),
                    If(
                        App(Var("eq"), Var("a"), Var("n")),
                        Var("incr1"),
                        App(
                            Var("fib2"),
                            Incr(Var("a")),
                            App(Var("plus"), Var("incr1"), Var("incr2")),
                            Var("incr1"),
                        )
                    )
                ),),),
                App(Var("fib2"), Incr(Zero()), Incr(Zero()), Incr(Zero()))
            ),
            Incr(Zero()),
        )
    ))
]

if __name__ == '__main__':

    print eval_exp(Let(
        binds,
        App(
            Var("plus"),
            Var("21"),
            App(
                Var("minus"),
                Incr(Var("21")),
                Incr(Zero())
            )
        )
    ), {})  # 21 + ((21+1) - 1) => 42

    print eval_exp(Let(
        binds,
        App(
            Var("fib"),
            App(Var("fib"), Incr(Incr(Incr(Incr(Incr(Zero())))))),
        )
    ), {})  # fib(fib(5)) => fib(8) => 34

    print eval_exp(Let(
        binds,
        App(Var("mult"), Incr(Incr(Incr(Zero()))), Var("21"))
    ), {})  # 3 * 21 => 63
