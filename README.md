# `ticlif` - tiled interactive command line interface framework

`ticlif` is a front-end framework for interactive command line applications written in Python.

It divides the space in your terminal window up into rectangular areas in a hierarchical structure.
If you know i3, this should sound very familiar.

Currently, it is only tested in Windows PowerShell.
To work with bash, the code to record user input will have to be revised.

## First Steps

Disclaimer: `ticlif` is in very early development.
Examples may be broken without notice.

To use `ticlif` in our application, we create `Element`s, configure them and tell `ticlif` to draw them.

```python
from ticlif import Element, draw
root = Element().with_content('Hello World')
draw(root)
```

In the above example, we create a single `Element`, tell it to display the text `Hello World` and then let `ticlif` draw that element to the terminal window.
Because there is only one element, it occupies the entire space.
Also note that the text on screen actually reads `$ello World`.
The `$` is our cursor but we can't move it yet.
To move the cursor, we need to get user input and call `draw(root)` in a loop.
We could write the loop ourselves but `ticlif` already did it for us.

```python
from ticlif import Element, loop
root = Element().with_content('Hello World')
loop(root)
```

Great, now we can move our cursor with the arrow keys!
Other than that, our app is still pretty dull, though.
Let's try something more interesting...

```python
from ticlif import Element, loop
fruit_basket = ['Apple', 'Peach', 'Banana'] 
root = (Element()
        .with_child(Element().with_content(fruit_basket))
        .with_child(Element()
                    .with_content(lambda elem: len(fruit_basket))
                    .with_handler(lambda elem, event: fruit_basket.append('Ananas'))
                    )
        )
loop(root)
```

Did you know that pretty much everyone calls it 'Ananas' instead of 'Pineapple'?

Anyway, now we have some fruit and more than one `Element`
We give our `root` two children, the first of which will display our fruit basked.
The second child, instead of an object to display, gets a function that will return the size of the basket when called.
Furthermore, we also define a handler which will be called when we press the Enter key while the cursor is inside that element.

We have now used `with_content` in three different ways:

1. In `with_content('Hello World')` we passed it a simple string which was displayed as-is.
2. In `with_content(fruit_basket)` we passed it a list whose elements were then displayed on a new line each.
3. In `.with_content(lambda elem: len(fruit_basket))` we passed it a function that returned a new value each time the element was drawn.
Notice that the display of the basked size would not have updated if we had written `.with_content(len(fruit_basket))`. In that case, `with_content` would have received an immutable integer by value (not reference).

In general, i.e. for arguments that aren't lists or functions, `with_content(o)` will use `str(o)` to turn the arguments into a strings.

We have also seen how we can register a callback with the `with_handler` method.
When an event occurs, the responsible element will call the registered method with itself and the event as arguments.
These callback methods are the main way how your application can react to user input.
You can also use these callbacks to change the structure of the displayed hierarchy: 
create new elements, remove old ones, move elements or add new roots...
The possibilities are endless!

Wait... New roots?

## Multiple Roots

`ticlif` does not have a single root element but actually keeps a stack of them.
When you call `loop(root)`, you tell `ticlif` to make `root` the *active root*.
The active root is the element which is currently being displayed as the top-level node.
Let's look at an example.

```python
from ticlif import Element, loop, controller

root = Element().with_content('Hello World')

fruit_basket = ['Apple', 'Peach', 'Banana'] 
froot = (Element()
        .with_child(Element().with_content(fruit_basket))
        .with_child(Element()
                    .with_content(lambda elem: len(fruit_basket))
                    .with_handler(lambda elem, event: fruit_basket.append('Ananas'))
                    )
        )

controller.add_root(root)
loop(froot) # not endorsed by fruit loops, honest...
```

You will have recognized our two roots from the previous examples.
The important difference is that before entering the loop with `froot` as the active root, we also tell `ticlif` about the other root.

When you run this example, you will see the familiar elements of `froot` but no sign of `Hello World` because `root` is not the active root and therefore not drawn.
The key to cycle through the different nodes is `` ` `` (backtick / tilde).
If you press it, the display will change and greet you with `Hello World`.
Another press and you are back to the fruits.
