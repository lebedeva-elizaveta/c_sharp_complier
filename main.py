import os

import _parser
import semantic


def main():
    prog1 = '''
    int a = 5;
    double b = 7.5;
    if (a < b)
    {
        for (int i = 0; i < 5; i = i + 1)
        {
            a = a + 1;
        }
    }
    else
    {
        b = 12.7;
    }
    '''

    prog2 = '''
    int a = 5;
    int b = 4;
    intt s = a * b;
    '''

    prog3 = '''
    int a = 4;
    int b = 7;
    if (b > a)
    {
        a = d;
    }
    '''
    prog4 = '''
    int k = sum(4,5);
    int sum(int a, int b) 
    {
        int s = a + b;
        return s;
    }
    '''

    execute(prog4)


def execute(prog: str):
    prog = _parser.parse(prog)
    print('ast:')
    print(*prog.tree, sep=os.linesep)

    print('semantic_check:')
    try:
        scope = semantic.prepare_global_scope()
        print("prepared")
        prog.semantic_check(scope)
        print(*prog.tree, sep=os.linesep)
    except semantic.SemanticException as e:
        print('Ошибка: {}'.format(e.message))
        return
    print()


if __name__ == "__main__":
    main()
