import inspect

import pyparsing as pp
from pyparsing import pyparsing_common as ppc

from ast_nodes import *


# создает и настраивает парсер
def make_parser():
    IF = pp.Keyword('if')
    FOR = pp.Keyword('for')
    RETURN = pp.Keyword('return')
    keywords = IF | FOR | RETURN

    num = pp.Regex('[+-]?\\d+\\.?\\d*([eE][+-]?\\d+)?')
    str_ = pp.QuotedString('"', escChar='\\', unquoteResults=False, convertWhitespaceEscapes=False)
    literal = num | str_ | pp.Regex('true|false')
    ident = (~keywords + ppc.identifier.copy()).setName('ident')
    type_ = ident.copy().setName('type')

    LPAR, RPAR = pp.Literal('(').suppress(), pp.Literal(')').suppress()
    LBRACE, RBRACE = pp.Literal("{").suppress(), pp.Literal("}").suppress()
    SEMI, COMMA = pp.Literal(';').suppress(), pp.Literal(',').suppress()
    ASSIGN = pp.Literal('=')

    ADD, SUB = pp.Literal('+'), pp.Literal('-')
    MULT, DIV, MOD = pp.Literal('*'), pp.Literal('/'), pp.Literal('%')
    AND = pp.Literal('&&')
    OR = pp.Literal('||')
    GE, LE, GT, LT = pp.Literal('>='), pp.Literal('<='), pp.Literal('>'), pp.Literal('<')
    NOTEQUALS, EQUALS = pp.Literal('!='), pp.Literal('==')

    expr = pp.Forward()
    stmt = pp.Forward()
    stmt_list = pp.Forward()

    call = ident + LPAR + pp.Optional(expr + pp.ZeroOrMore(COMMA + expr)) + RPAR

    group = (
            literal |
            call |
            ident |
            LPAR + expr + RPAR
    )

    mult = pp.Group(group + pp.ZeroOrMore((MULT | DIV | MOD) + group)).setName('binary_operation')
    add = pp.Group(mult + pp.ZeroOrMore((ADD | SUB) + mult)).setName('binary_operation')
    compare1 = pp.Group(add + pp.Optional((GE | LE | GT | LT) + add)).setName('binary_operation')
    compare2 = pp.Group(compare1 + pp.Optional((EQUALS | NOTEQUALS) + compare1)).setName('binary_operation')
    logical_and = pp.Group(compare2 + pp.ZeroOrMore(AND + compare2)).setName('binary_operation')
    logical_or = pp.Group(logical_and + pp.ZeroOrMore(OR + logical_and)).setName('binary_operation')

    expr << logical_or

    simple_assign = (ident + ASSIGN.suppress() + expr).setName('assign')
    var_inner = simple_assign | ident
    vars_ = type_ + var_inner + pp.ZeroOrMore(COMMA + var_inner)

    assign = ident + ASSIGN.suppress() + expr
    simple_stmt = assign | call

    for_stmt_list0 = (pp.Optional(simple_stmt + pp.ZeroOrMore(COMMA + simple_stmt))).setName('stmt_list')
    for_stmt_list = vars_ | for_stmt_list0
    for_cond = expr | pp.Group(pp.empty).setName('stmt_list')
    for_body = stmt | pp.Group(SEMI).setName('stmt_list')

    if_ = IF.suppress() + LPAR + expr + RPAR + stmt + pp.Optional(pp.Keyword("else").suppress() + stmt)
    for_ = FOR.suppress() + LPAR + for_stmt_list + SEMI + for_cond + SEMI + for_stmt_list + RPAR + for_body
    return_ = RETURN.suppress() + expr
    composite = LBRACE + stmt_list + RBRACE

    param = type_ + ident
    params = pp.Optional(param + pp.ZeroOrMore(COMMA + param))
    func = type_ + ident + LPAR + params + RPAR + LBRACE + stmt_list + RBRACE

    stmt << (
            if_ |
            for_ |
            return_ |
            simple_stmt + SEMI |
            vars_ + SEMI |
            composite |
            func
    )

    stmt_list << (pp.ZeroOrMore(stmt + pp.ZeroOrMore(SEMI)))

    program = stmt_list.ignore(pp.cStyleComment).ignore(pp.dblSlashComment) + pp.StringEnd()

    start = program

    # автоматическое преобразование результатов разбора текста
    def set_parse_action_magic(rule_name: str, parser_element: pp.ParserElement):
        if rule_name == rule_name.upper():
            return
        if getattr(parser_element, 'name', None) and parser_element.name.isidentifier():
            rule_name = parser_element.name
        if rule_name in ('binary_operation',):
            def binary_operation_parse_action(s, loc, tocs):
                node = tocs[0]
                if not isinstance(node, AstNode):
                    node = binary_operation_parse_action(s, loc, node)
                for i in range(1, len(tocs) - 1, 2):
                    second_node = tocs[i + 1]
                    if not isinstance(second_node, AstNode):
                        second_node = binary_operation_parse_action(s, loc, second_node)
                    node = BinaryOperationNode(BinaryOperation(tocs[i]), node, second_node, loc=loc)
                return node

            parser_element.setParseAction(binary_operation_parse_action)
        else:
            cls = ''.join(x.capitalize() for x in rule_name.split('_')) + 'Node'
            with suppress(NameError):
                cls = eval(cls)
                if not inspect.isabstract(cls):
                    def parse_action(s, loc, tocs):
                        if cls is FuncNode:
                            return FuncNode(tocs[0], tocs[1], tocs[2:-1], tocs[-1], loc=loc)
                        else:
                            return cls(*tocs, loc=loc)

                    parser_element.setParseAction(parse_action)

    for var_name, value in locals().copy().items():
        if isinstance(value, pp.ParserElement):
            set_parse_action_magic(var_name, value)

    return start


parser = make_parser()

# разбирает переданный программный код и возвращает соответствующее AST
def parse(prog: str):
    locs = []
    row, col = 0, 0
    for ch in prog:
        if ch == '\n':
            row += 1
            col = 0
        elif ch == '\r':
            pass
        else:
            col += 1
        locs.append((row, col))

    previous_init_action = AstNode.init_action

    # установка строки и столбца в узле AST
    def init_action(node: AstNode):
        loc = getattr(node, 'loc', None)
        if isinstance(loc, int):
            node.row = locs[loc][0] + 1
            node.col = locs[loc][1] + 1

    AstNode.init_action = init_action
    try:
        prog: StmtListNode = parser.parseString(str(prog))[0]
        prog.program = True
        return prog
    finally:
        AstNode.init_action = previous_init_action
