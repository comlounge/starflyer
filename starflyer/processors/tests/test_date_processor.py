import pytest
from starflyer.processors import Date, process, Error
import datetime


def test_date_ok():
    """test a processor"""
    
    ps=[Date(format='%d.%m.%Y')]

    data = "29.05.2011"
    ctx = process(data, ps)
    assert ctx.data == datetime.datetime.strptime("29.05.2011", '%d.%m.%Y')
    assert ctx.success 

def test_date_wrong_format():
    """test a processor"""
    
    ps=[Date(format='%d.%m.%Y')]

    data = "2011-05-29"
    pytest.raises(Error, process, data, ps)
    
    try:
        ctx = process(data, ps)
    except Error, e:
        assert e.code == 'wrong_format'
    
def test_date_not_before():
    """test a processor"""
    d = datetime.datetime(2012,1,1)
    ps=[Date(not_before=d)]

    data = "2011-05-29"
    pytest.raises(Error, process, data, ps)
    
    try:
        ctx = process(data, ps)
    except Error, e:
        assert e.code == 'not_before'
    
def test_date_not_after():
    """test a processor"""
    d = datetime.datetime(2010,1,1)
    ps=[Date(not_after=d)]

    data = "2011-05-29"
    pytest.raises(Error, process, data, ps)
    
    try:
        ctx = process(data, ps)
    except Error, e:
        assert e.code == 'not_after'
    
def test_date_after_now():
    """test a processor"""
    
    ps=[Date(after_now=True)]

    data = "2011-04-29"
    pytest.raises(Error, process, data, ps)
    
    try:
        ctx = process(data, ps)
    except Error, e:
        assert e.code == 'after_now'    
        
def test_date_not_after_now():
    """test a processor"""
    
    ps=[Date(not_after_now=True)]

    data = "2017-04-29"
    pytest.raises(Error, process, data, ps)
    
    try:
        ctx = process(data, ps)
    except Error, e:
        assert e.code == 'not_after_now'  
    
    
    
    