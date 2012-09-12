from starflyer import AttributeMapper


def test_basics():
    am = AttributeMapper({
        'a' : 3
    })

    assert am.a == 3
    assert am['a'] == 3


def test_nested():
    am = AttributeMapper({
        'a' : AttributeMapper({
            'b' : 9,
            'c' : 10,
        })
    })
    
    assert am.a.b == 9

def test_nested_update():
    am = AttributeMapper({
        'a' : AttributeMapper({
            'b' : 9,
            'c' : 10,
        })
    })
    am.update({
        'foo' : 'bar',
        'a' : {
            'b' : 13
        }
    })
    
    assert am.a.b == 13
    assert am.a.c == 10
    assert am.foo == "bar"




