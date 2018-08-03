from ticlif import Element, loop, debug_info, controller, Input, Debug
from Command import Command


class Box:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

    def __add__(self, other):
        if isinstance(other, Box):
            return self.value + other.value
        else:
            return self.value + other

    def __iadd__(self, other):
        self.value = self + other


input("Press the return key to continue...")
counter = Box(0)


# counter = [0]


def inc():
    counter.__iadd__(1)


fruit_basket = ['Apple', 'Peach', 'Banana']
froot = (Element()
         .with_child(Element().with_content(fruit_basket))
         .with_child(Element()
                     .with_content(lambda elem: len(fruit_basket))
                     .with_handler(lambda elem, event: fruit_basket.append('Ananas'))
                     )
         )

inputBox = 'write here'


def input_handler(elem, event):
    global inputBox
    if event.key == Command.DELETE_BEFORE:
        inputBox = inputBox[:-1]
    else:
        inputBox += event.key


root = (Element()
        .with_id('.')
        .with_direction('horizontal')
        .with_child(Element()
                    .with_id('.0')
                    .with_child(Element()
                                .with_id('.0.0')
                                .with_content(lambda elem: debug_info(elem))
                                .with_handler(lambda elem, event: inc())
                                )
                    .with_child(Element()
                                .with_id('.0.1')
                                .with_content(lambda elem: Debug.recent_inputs)
                                )
                    )
        .with_child(Element()
                    .with_id('.1')
                    .with_child(Input()
                                .with_id('.1.0')
                                .with_content('write here')
                                )
                    .with_child(Element()
                                .with_id('.1.1')
                                .with_content(lambda _: str(root.pos_of_child(1)))
                                )
                    .with_child(Element()
                                .with_id('.1.2:Counter')
                                .with_content(lambda _: "counter: {}".format(counter))
                                .with_handler(lambda elem, event: inc())
                                )
                    )
        )

controller.add_root(froot)
loop(root)
