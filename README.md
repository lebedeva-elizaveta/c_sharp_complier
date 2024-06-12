# Компилятор для языка С#
На данный момент реализовано построение AST-дерева для исходного кода на C#. Оно строится для:
- базовых операций;
- основных типов данных;
- оператора присваивания;
- оператора сравнения;
- условного оператора if-else;
- цикла for;
- функций.
## Пример №1
Код без ошибок:
```
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
```
Вывод:
```
ast:
...
├ int
│ └ =
│   ├ a
│   └ 5
├ double
│ └ =
│   ├ b
│   └ 7.5
└ if
  ├ <
  │ ├ a
  │ └ b
  ├ ...
  │ └ for
  │   ├ int
  │   │ └ =
  │   │   ├ i
  │   │   └ 0
  │   ├ <
  │   │ ├ i
  │   │ └ 5
  │   ├ ...
  │   │ └ =
  │   │   ├ i
  │   │   └ +
  │   │     ├ i
  │   │     └ 1
  │   └ ...
  │     └ =
  │       ├ a
  │       └ +
  │         ├ a
  │         └ 1
  └ ...
    └ =
      ├ b
      └ 12.7
semantic_check:
prepared
...
├ int
│ └ = : int
│   ├ a : int, global, 0
│   └ 5 : int
├ double
│ └ = : double
│   ├ b : double, global, 1
│   └ 7.5 : double
└ if
  ├ < : boolean
  │ ├ convert : double
  │ │ └ double
  │ │   └ a : int, global, 0
  │ └ b : double, global, 1
  ├ ...
  │ └ for
  │   ├ int
  │   │ └ = : int
  │   │   ├ i : int, global, 2
  │   │   └ 0 : int
  │   ├ < : boolean
  │   │ ├ i : int, global, 2
  │   │ └ 5 : int
  │   ├ ...
  │   │ └ = : int
  │   │   ├ i : int, global, 2
  │   │   └ + : int
  │   │     ├ i : int, global, 2
  │   │     └ 1 : int
  │   └ ...
  │     └ = : int
  │       ├ a : int, global, 0
  │       └ + : int
  │         ├ a : int, global, 0
  │         └ 1 : int
  └ ...
    └ = : double
      ├ b : double, global, 1
      └ 12.7 : double
```
## Пример №2
Код с ошибкой: Неизвестный тип данных
```
int a = 5;
int b = 4;
intt s = a * b;
```
Вывод:
```
ast:
...
├ int
│ └ =
│   ├ a
│   └ 5
├ int
│ └ =
│   ├ b
│   └ 4
└ intt
  └ =
    ├ s
    └ *
      ├ a
      └ b
semantic_check:
prepared
Ошибка: Неизвестный тип intt (строка: 4, позиция: 6)
```
## Пример №3
Код с ошибкой: Идентификатор не найден
```
int a = 4;
int b = 7;
if (b > a)
{
    a = d;
}
```
Вывод:
```
ast:
...
├ int
│ └ =
│   ├ a
│   └ 4
├ int
│ └ =
│   ├ b
│   └ 7
└ if
  ├ >
  │ ├ b
  │ └ a
  └ ...
    └ =
      ├ a
      └ d
semantic_check:
prepared
Ошибка: Идентификатор d не найден (строка: 6, позиция: 13)
```
## Пример №4
Код с ошибкой: Функция не найдена
```
int k = sum(4,5);
int sum(int a, int b) 
{
    int s = a + b;
    return s;
}
```
Вывод:
```
ast:
...
├ int
│ └ =
│   ├ k
│   └ call
│     ├ sum
│     ├ 4
│     └ 5
└ function
  ├ int
  │ └ sum
  ├ params
  │ ├ int
  │ │ └ a
  │ └ int
  │   └ b
  └ ...
    ├ int
    │ └ =
    │   ├ s
    │   └ +
    │     ├ a
    │     └ b
    └ return
      └ s
semantic_check:
prepared
Ошибка: Функция sum не найдена (строка: 2, позиция: 13)
```
