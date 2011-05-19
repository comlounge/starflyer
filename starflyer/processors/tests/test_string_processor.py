from starflyer.processors import String, process

def test_string_ok():
    """test a processor"""
    
    ps=[String(max_length=30)]

    data = "hallo"
    ctx = process(data, ps)
    assert ctx.data == "hallo"
    assert ctx.success 

def test_string_too_long():
    """test a processor"""
    
    ps = [String(max_length=10)]

    data = "hallo, this is too long"
    ctx = process(data, ps)
    assert ctx.data == "hallo, this is too long"
    assert not ctx.success 
    assert ctx.errors[0]['code'] == 'too_long'

def test_string_too_short():
    
    ps = [String(min_length=10)]

    data = "hello"
    ctx = process(data, ps)
    assert not ctx.success 
    assert ctx.errors[0]['code'] == 'too_short'

def test_string_strip():
    
    ps = [String(strip=True)]

    data = u"  hello  "
    ctx = process(data, ps)
    assert ctx.data == u"hello"
    assert ctx.success 

def test_string_nostrip():
    
    ps = [String(strip=False)]

    data = u"  hello  "
    ctx = process(data, ps)
    assert ctx.data == u"  hello  "
    assert ctx.success 


def test_string_required_none_value():
    
    ps = [String(required=True)]

    ctx = process(None, ps)
    assert not ctx.success 
    assert ctx.errors[0]['code'] == 'required'

def test_string_required_empty_string():
    
    ps = [String(required=True)]

    ctx = process(u"", ps)
    assert not ctx.success 
    assert ctx.errors[0]['code'] == 'required'


