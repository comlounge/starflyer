from starflyer import AttributeMapper
import pytest


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


def test_dotted_update():
    am = AttributeMapper({
        'a' : AttributeMapper({
            'b' : 9,
            'c' : 10,
        })
    })

    am.update({
        'foo' : 'bar',
        'a.b' : 13
    })
    
    assert am.a.b == 13
    assert am.a.c == 10
    assert am.foo == "bar"


def test_dotted_update2():
    am = AttributeMapper({
        'a' : AttributeMapper({
            'b' : 9,
            'c' : AttributeMapper({
                'd' : 19
            }),
        })
    })

    am.update({
        'foo' : 'bar',
        'a.b' : 13,
        'a.c.d' : 21
    })
    
    assert am.a.b == 13
    assert am.a.c.d == 21
    assert am.foo == "bar"


def test_dotted_update_first_missing():
    am = AttributeMapper({
        'a' : AttributeMapper({
            'b' : 9,
            'c' : 10,
        })
    })

    pytest.raises(ValueError, am.update, {
        'foo' : 'bar',
        'e.b' : 13
    })
    
def test_dotted_update_last_missing():
    am = AttributeMapper({
        'a' : AttributeMapper({
            'b' : 9,
            'c' : 10,
        })
    })

    am.update({
        'foo' : 'bar',
        'a.e' : 13
    })
    
    assert am.a.e == 13
    assert am.a.c == 10
    assert am.foo == "bar"


def test_dotted_update_no_dict():
    am = AttributeMapper({
        'a' : AttributeMapper({
            'b' : 9,
            'c' : 10,
        }), 
        'e' : "foobar"
    })

    pytest.raises(ValueError, am.update, {
        'foo' : 'bar',
        'e.foo' : 'bar'
    })
