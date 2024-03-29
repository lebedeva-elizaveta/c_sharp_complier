from abc import ABC, abstractmethod
from contextlib import suppress
from typing import Optional, Union, Tuple, Callable

from semantic import TYPE_CONVERTIBILITY, BinaryOperation, DataType, IdentDesc, SemanticException


# абстрактный класс для узла дерева
class AstNode(ABC):

    init_action: Callable[['AstNode'], None] = None

    def __init__(self, row: Optional[int] = None, col: Optional[int] = None, **props):
        super().__init__()
        self.row = row
        self.col = col
        for k, v in props.items():
            setattr(self, k, v)
        if AstNode.init_action is not None:
            AstNode.init_action(self)
        self.node_type: Optional[DataType] = None
        self.node_ident: Optional[IdentDesc] = None

    @abstractmethod
    def __str__(self):
        pass

    @property
    def childs(self):
        return ()

    def to_str(self):
        return str(self)

    def to_str_full(self):
        r = ''
        if self.node_ident:
            r = str(self.node_ident)
        elif self.node_type:
            r = str(self.node_type)
        return self.to_str() + (' : ' + r if r else '')

    def semantic_error(self, message: str):
        raise SemanticException(message, self.row, self.col)


# обход дерева
    @property
    def tree(self):
        r = [self.to_str_full()]
        childs = self.childs
        if isinstance(childs, tuple):
            for i, child in enumerate(childs):
                ch0, ch = '├', '│'
                if child is childs[-1]:
                    ch0, ch = '└', ' '
                r.extend(((ch0 if j == 0 else ch) + ' ' + s for j, s in enumerate(child.tree)))
        else:
            ch0, ch = '└', ' '
            r.extend(((ch0 if j == 0 else ch) + ' ' + s for j, s in enumerate(childs.tree)))
        return tuple(r)


# группировка узлов
class _GroupNode(AstNode):
    def __init__(self, name: str, *childs: AstNode,
                 row: Optional[int] = None, col: Optional[int] = None, **props):
        super().__init__(row=row, col=col, **props)
        self.name = name
        self._childs = childs

    def __str__(self):
        return self.name

    @property
    def childs(self):
        return self._childs


# выражения
class ExprNode(AstNode, ABC):
    pass


# класс для представления литералов
class LiteralNode(ExprNode):

    def __init__(self, literal: str,
                 row: Optional[int] = None, col: Optional[int] = None, **props):
        super().__init__(row=row, col=col, **props)
        self.literal = literal
        if literal in ('true', 'false'):
            self.value = bool(literal)
        else:
            self.value = eval(literal)

    def __str__(self):
        return self.literal


# класс для идентификаторов
class IdentNode(ExprNode):
    def __init__(self, name: str,
                 row: Optional[int] = None, col: Optional[int] = None, **props):
        super().__init__(row=row, col=col, **props)
        self.name = str(name)

    def __str__(self):
        return str(self.name)


# класс для типов данных
class TypeNode(IdentNode):
    def __init__(self, name: str,
                 row: Optional[int] = None, col: Optional[int] = None, **props):
        super().__init__(name, row=row, col=col, **props)
        self.type = None
        with suppress(SemanticException):
            self.type = DataType.from_string(name)

    def to_str_full(self):
        return self.to_str()


# класс для бинарных операций
class BinaryOperationNode(ExprNode):
    def __init__(self, op: BinaryOperation, arg1: ExprNode, arg2: ExprNode,
                 row: Optional[int] = None, col: Optional[int] = None, **props):
        super().__init__(row=row, col=col, **props)
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2

    def __str__(self):
        return str(self.op.value)

    @property
    def childs(self):
        return self.arg1, self.arg2


# класс для вызова функций
class CallNode(ExprNode):
    def __init__(self, func: IdentNode, *params: ExprNode,
                 row: Optional[int] = None, col: Optional[int] = None, **props):
        super().__init__(row=row, col=col, **props)
        self.func = func
        self.params = params

    def __str__(self):
        return 'call'

    @property
    def childs(self):
        return self.func, *self.params


# конвертация типов данных
class TypeConvertNode(ExprNode):
    def __init__(self, expr: ExprNode, type_: DataType,
                 row: Optional[int] = None, col: Optional[int] = None, **props):
        super().__init__(row=row, col=col, **props)
        self.expr = expr
        self.type = type_
        self.node_type = type_

    def __str__(self):
        return 'convert'

    @property
    def childs(self):
        return _GroupNode(str(self.type), self.expr),


def type_convert(expr: ExprNode, type_: DataType, except_node: Optional[AstNode] = None,
                 comment: Optional[str] = None):
    if expr.node_type is None:
        except_node.semantic_error('Тип выражения не определен')
    if expr.node_type == type_:
        return expr
    if expr.node_type.simple and type_.simple and \
            expr.node_type.primitive_type in TYPE_CONVERTIBILITY and type_.primitive_type in TYPE_CONVERTIBILITY[
        expr.node_type.primitive_type]:
        return TypeConvertNode(expr, type_)
    else:
        (except_node if except_node else expr).semantic_error('Тип {0}{2} не конвертируется в {1}'.format(
            expr.node_type, type_, ' ({})'.format(comment) if comment else ''))


class StmtNode(ExprNode, ABC):
    def to_str_full(self):
        return self.to_str()


# оператор присваивания
class AssignNode(ExprNode):
    def __init__(self, var: IdentNode, val: ExprNode,
                 row: Optional[int] = None, col: Optional[int] = None, **props):
        super().__init__(row=row, col=col, **props)
        self.var = var
        self.val = val

    def __str__(self):
        return '='

    @property
    def childs(self):
        return self.var, self.val


# класс для объявления переменных
class VarsNode(StmtNode):
    def __init__(self, type_: TypeNode, *vars_: Union[IdentNode, 'AssignNode'],
                 row: Optional[int] = None, col: Optional[int] = None, **props):
        super().__init__(row=row, col=col, **props)
        self.type = type_
        self.vars = vars_

    def __str__(self):
        return str(self.type)

    @property
    def childs(self):
        return self.vars


# класс для оператора return
class ReturnNode(StmtNode):
    def __init__(self, val: ExprNode,
                 row: Optional[int] = None, col: Optional[int] = None, **props):
        super().__init__(row=row, col=col, **props)
        self.val = val

    def __str__(self):
        return 'return'

    @property
    def childs(self):
        return self.val


# класс для if-else
class IfNode(StmtNode):
    def __init__(self, cond: ExprNode, then_stmt: StmtNode, else_stmt: Optional[StmtNode] = None,
                 row: Optional[int] = None, col: Optional[int] = None, **props):
        super().__init__(row=row, col=col, **props)
        self.cond = cond
        self.then_stmt = then_stmt
        self.else_stmt = else_stmt

    def __str__(self):
        return 'if'

    @property
    def childs(self):
        return self.cond, self.then_stmt, *((self.else_stmt,) if self.else_stmt else tuple())


# класс для цикла for
class ForNode(StmtNode):
    def __init__(self, init: Optional[StmtNode], cond: Optional[ExprNode],
                 step: Optional[StmtNode], body: Optional[StmtNode],
                 row: Optional[int] = None, col: Optional[int] = None, **props):
        super().__init__(row=row, col=col, **props)
        self.init = init if init else EMPTY_STMT
        self.cond = cond if cond else EMPTY_STMT
        self.step = step if step else EMPTY_STMT
        self.body = body if body else EMPTY_STMT

    def __str__(self):
        return 'for'

    @property
    def childs(self):
        return self.init, self.cond, self.step, self.body


# класс для параметров функции
class ParamNode(StmtNode):
    def __init__(self, type_: TypeNode, name: IdentNode,
                 row: Optional[int] = None, col: Optional[int] = None, **props):
        super().__init__(row=row, col=col, **props)
        self.type = type_
        self.name = name

    def __str__(self) -> str:
        return str(self.type)

    @property
    def childs(self) -> Tuple[IdentNode]:
        return self.name,


# класс для объявления функции
class FuncNode(StmtNode):
    def __init__(self, type_: TypeNode, name: IdentNode, params: Tuple[ParamNode], body: StmtNode,
                 row: Optional[int] = None, col: Optional[int] = None, **props):
        super().__init__(row=row, col=col, **props)
        self.type = type_
        self.name = name
        self.params = params
        self.body = body

    def __str__(self):
        return 'function'

    @property
    def childs(self):
        return _GroupNode(str(self.type), self.name), _GroupNode('params', *self.params), self.body


# хранит список операторов или выражений
class StmtListNode(StmtNode):
    def __init__(self, *exprs: StmtNode,
                 row: Optional[int] = None, col: Optional[int] = None, **props):
        super().__init__(row=row, col=col, **props)
        self.exprs = exprs
        self.program = False

    def __str__(self):
        return '...'

    @property
    def childs(self):
        return self.exprs


EMPTY_STMT = StmtListNode()
EMPTY_IDENT = IdentDesc('', DataType.VOID)
