from typing import Tuple, Any, Dict, Optional
from enum import Enum


# базовые операции
class BinaryOperation(Enum):
    ADD = '+'
    SUB = '-'
    MULT = '*'
    DIV = '/'
    MOD = '%'
    GT = '>'
    LT = '<'
    GE = '>='
    LE = '<='
    EQUALS = '=='
    NOTEQUALS = '!='
    BIT_AND = '&'
    BIT_OR = '|'
    LOGICAL_AND = '&&'
    LOGICAL_OR = '||'

    def __str__(self):
        return self.value


# типы данных
class PrimitiveType(Enum):
    VOID = 'void'
    INT = 'int'
    DOUBLE = 'double'
    BOOL = 'bool'
    STR = 'string'

    def __str__(self):
        return self.value


VOID, INT, DOUBLE, BOOL, STR = PrimitiveType.VOID, PrimitiveType.INT, PrimitiveType.DOUBLE, \
                               PrimitiveType.BOOL, PrimitiveType.STR


# работа с типами данных
class DataType:
    VOID: 'DataType'
    INT: 'DataType'
    DOUBLE: 'DataType'
    BOOL: 'DataType'
    STR: 'DataType'

    def __init__(self, primitive_type_: Optional[PrimitiveType] = None,
                 return_type: Optional['DataType'] = None, params: Optional[Tuple['DataType']] = None):
        self.primitive_type = primitive_type_
        self.return_type = return_type
        self.params = params

    # если функция
    @property
    def function(self):
        return self.return_type is not None

    # если простой тип данных
    @property
    def simple(self):
        return not self.function

    # проверяет, равны ли два объекта DataType
    def __eq__(self, other: 'DataType'):
        if self.function != other.function:
            return False
        if not self.function:
            return self.primitive_type == other.primitive_type
        else:
            if self.return_type != other.return_type:
                return False
            if len(self.params) != len(other.params):
                return False
            for i in range(len(self.params)):
                if self.params[i] != other.params[i]:
                    return False
            return True

    # создает экземпляр класса DataType на основе переданного базового типа данных
    @staticmethod
    def from_primitive_type(primitive_type_: PrimitiveType):
        return getattr(DataType, primitive_type_.name)

    # создает экземпляр класса DataType на основе переданной строки
    @staticmethod
    def from_string(type_string: str):
        try:
            primitive_type_ = PrimitiveType(type_string)
            return DataType.from_primitive_type(primitive_type_)
        except ValueError:
            raise SemanticException('Невозможно преобразовать строку {} в тип данных'.format(type_string))

    # возвращает строковое представление объекта DataType
    def __str__(self):
        if not self.function:
            return str(self.primitive_type)
        else:
            res = str(self.return_type)
            res += ' ('
            for param in self.params:
                if res[-1] != '(':
                    res += ', '
                res += str(param)
            res += ')'
        return res


# добавляет атрибуты к классу DataType
for primitive_type in PrimitiveType:
    setattr(DataType, primitive_type.name, DataType(primitive_type))


# переменные могут быть параметром функции или локальными
class VariableScope(Enum):

    PARAM = 'param'
    LOCAL = 'local'

    def __str__(self):
        return self.value


# описание переменной
class IdentDesc:
    def __init__(self, name: str, type_: DataType, scope: VariableScope = VariableScope.LOCAL, index: int = 0):
        self.name = name
        self.type = type_
        self.scope = scope
        self.index = index
        self.built_in = False

    def __str__(self):
        return '{}, {}, {}'.format(self.type, self.scope, 'built-in' if self.built_in else self.index)


# область видимости
class IdentScope:
    def __init__(self, parent: Optional['IdentScope'] = None):
        self.idents: Dict[str, IdentDesc] = {}
        self.function: Optional[IdentDesc] = None
        self.parent = parent
        self.var_index = 0
        self.param_index = 0

    @property
    def curr_func(self):
        curr = self
        while curr and not curr.function:
            curr = curr.parent
        return curr

    def add_ident(self, new_ident: IdentDesc):
        func_scope = self.curr_func

        if new_ident.scope != VariableScope.PARAM:
            new_ident.scope = VariableScope.LOCAL
        existing_ident = self.get_ident(new_ident.name)
        if existing_ident:
            error = False
            if new_ident.scope == VariableScope.PARAM:
                if existing_ident.scope == VariableScope.PARAM:
                    error = True
            else:
                error = True
            if error:
                raise SemanticException('Идентификатор {} уже объявлен'.format(new_ident.name))
        if not new_ident.type.function:
            if new_ident.scope == VariableScope.PARAM:
                new_ident.index = func_scope.param_index
                func_scope.param_index += 1
            else:
                ident_scope = func_scope
                new_ident.index = ident_scope.var_index
                ident_scope.var_index += 1
        self.idents[new_ident.name] = new_ident
        return new_ident

    def get_ident(self, name: str):
        scope = self
        ident = None
        while scope:
            ident = scope.idents.get(name)
            if ident:
                break
            scope = scope.parent
        return ident


# исключения
class SemanticException(Exception):
    def __init__(self, message, row: int = None, col: int = None, **kwargs: Any):
        if row or col:
            message += " ("
            if row:
                message += 'строка: {}'.format(row)
                if col:
                    message += ', '
            if row:
                message += 'позиция: {}'.format(col)
            message += ")"
        self.message = message


# конвертация типов
TYPE_CONVERTIBILITY = {
    INT: (DOUBLE, BOOL, STR),
    DOUBLE: (STR,),
    BOOL: (STR,)
}


# проверяет может ли конвертироваться
def can_type_convert_to(from_type: DataType, to_type: DataType):
    if not from_type.simple or not to_type.simple:
        return False
    return from_type.primitive_type in TYPE_CONVERTIBILITY and to_type.primitive_type in TYPE_CONVERTIBILITY[
        to_type.primitive_type]


# правила конвертации
BINARY_OPERATION_TYPE_COMPATIBILITY = {
    BinaryOperation.ADD: {
        (INT, INT): INT,
        (DOUBLE, DOUBLE): DOUBLE,
        (STR, STR): STR,
        (INT, DOUBLE): DOUBLE,
        (DOUBLE, INT): DOUBLE
    },
    BinaryOperation.SUB: {
        (INT, INT): INT,
        (DOUBLE, DOUBLE): DOUBLE,
        (INT, DOUBLE): DOUBLE,
        (DOUBLE, INT): DOUBLE
    },
    BinaryOperation.MULT: {
        (INT, INT): INT,
        (DOUBLE, DOUBLE): DOUBLE,
        (INT, DOUBLE): DOUBLE,
        (DOUBLE, INT): DOUBLE
    },
    BinaryOperation.DIV: {
        (INT, INT): INT,
        (DOUBLE, DOUBLE): DOUBLE,
        (INT, DOUBLE): DOUBLE,
        (DOUBLE, INT): DOUBLE
    },
    BinaryOperation.MOD: {
        (INT, INT): INT,
        (DOUBLE, DOUBLE): DOUBLE,
        (INT, DOUBLE): DOUBLE,
        (DOUBLE, INT): DOUBLE
    },

    BinaryOperation.GT: {
        (INT, INT): BOOL,
        (DOUBLE, DOUBLE): BOOL,
        (STR, STR): BOOL,
    },
    BinaryOperation.LT: {
        (INT, INT): BOOL,
        (DOUBLE, DOUBLE): BOOL,
        (STR, STR): BOOL,
    },
    BinaryOperation.GE: {
        (INT, INT): BOOL,
        (DOUBLE, DOUBLE): BOOL,
        (STR, STR): BOOL,
    },
    BinaryOperation.LE: {
        (INT, INT): BOOL,
        (DOUBLE, DOUBLE): BOOL,
        (STR, STR): BOOL,
    },
    BinaryOperation.EQUALS: {
        (INT, INT): BOOL,
        (DOUBLE, DOUBLE): BOOL,
        (STR, STR): BOOL,
    },
    BinaryOperation.NOTEQUALS: {
        (INT, INT): BOOL,
        (DOUBLE, DOUBLE): BOOL,
        (STR, STR): BOOL,
    },

    BinaryOperation.BIT_AND: {
        (INT, INT): INT
    },
    BinaryOperation.BIT_OR: {
        (INT, INT): INT
    },

    BinaryOperation.LOGICAL_AND: {
        (BOOL, BOOL): BOOL
    },
    BinaryOperation.LOGICAL_OR: {
        (BOOL, BOOL): BOOL
    },
}


# создает новую область видимости для программы
def create_scope():
    scope = IdentScope()
    for name, ident in scope.idents.items():
        ident.built_in = True
    scope.var_index = 0
    return scope
