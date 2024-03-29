import os

import _parser


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
    int s = a * b;
    '''

    prog3 = '''
    int a = 4;
    int b = 7;
    if (b > a)
    {
        a = b;
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


if __name__ == "__main__":
    main()
