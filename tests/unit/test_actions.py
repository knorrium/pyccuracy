#!/usr/bin/env python
#-*- coding:utf-8 -*-

# Licensed under the Open Software License ("OSL") v. 3.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.opensource.org/licenses/osl-3.0.php

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pmock import *
from nose.tools import raises, set_trace

from pyccuracy import ActionBase, ActionRegistry
from pyccuracy.languages import LanguageItem
from pyccuracy.errors import LanguageDoesNotResolveError

def test_construction():
    class DoNothingAction(ActionBase):
        regex = r'^My Regex$'
        def execute(self, context, *args, **kwargs):
            pass

    assert DoNothingAction.regex == r'^My Regex$'

@raises(NotImplementedError)
def test_construction_fails_without_implementing_execute():
    class DoNothingAction(ActionBase):
        regex = r'^My Regex$'

@raises(NotImplementedError)
def test_construction_fails_without_implementing_setting_regex():
    class DoNothingAction(ActionBase):
        def execute(self, context, *args, **kw):
            pass

@raises(NotImplementedError)
def test_construction_fails_without_implementing_basic_attrs():
    class DoNothingAction(ActionBase):
        pass

@raises(TypeError)
def test_construction_fails_if_regex_nonstring():
    class DoNothingAction(ActionBase):
        regex = range(10)
        def execute(self, context, *args, **kw):
            pass

def test_can_resolve_string():
    class DoSomethingAction(ActionBase):
        regex = r'^(And )?I do "(?P<what>\w+)"$'
        def execute(self, context, *args, **kwargs):
            pass

    assert DoSomethingAction.can_resolve('And I do "test"')
    assert DoSomethingAction.can_resolve('I do "test"')

def test_cannot_resolve_string():
    class DoSomethingAction(ActionBase):
        regex = r'^(And )?I do "(?P<what>\w+)"$'
        def execute(self, context, *args, **kwargs):
            pass

    assert not DoSomethingAction.can_resolve('Not for me')
    assert not DoSomethingAction.can_resolve('Foo Bar')

def test_action_registry_suitable_for_returns_my_action():
    class MyAction(ActionBase):
        regex = LanguageItem('foo_bar_regex')
        def execute(self, context, *args, **kw):
            pass

    language_getter_mock = Mock()
    language_getter_mock.expects(at_least_once()).method('get').will(return_value('^$'))
    language_getter_mock.expects(once()).get(eq(LanguageItem('foo_bar_regex'))).will(return_value('My regex .+'))
    Action, args, kwargs = ActionRegistry.suitable_for('My regex baz', 'en-us', getter=language_getter_mock)
    language_getter_mock.verify()
    assert Action is MyAction

def test_action_registry_suitable_for_returns_my_action_without_language_item():
    class MyActionNoLanguage(ActionBase):
        regex = r'^I do (\w+)\s(\w+) so proudly$'
        def execute(self, context, *args, **kw):
            pass

    language_getter_mock = Mock()
    language_getter_mock.expects(at_least_once()).method('get').will(return_value('^$'))
    Action, args, kwargs = ActionRegistry.suitable_for('I do unit test so proudly', 'en-us', getter=language_getter_mock)
    assert Action is MyActionNoLanguage

def test_action_registry_can_resolve_same_name_classes():
    class MyActionSameName(ActionBase):
        regex = r'I do (\w+) very well'
        def execute(self, context, *args, **kw):
            pass
    Temp1 = MyActionSameName

    class MyActionSameName(ActionBase):
        regex = r'I do (\w+) very bad'
        def execute(self, context, *args, **kw):
            pass
    Temp2 = MyActionSameName

    language_getter_mock = Mock()
    language_getter_mock.expects(at_least_once()).method('get').will(return_value('^$'))

    Action1, args1, kwargs1 = ActionRegistry.suitable_for('I do test very well', 'en-us', getter=language_getter_mock)
    Action2, args2, kwargs2 = ActionRegistry.suitable_for('I do test very bad', 'en-us', getter=language_getter_mock)
    assert Action1 is not MyActionSameName
    assert Action1 is not Temp2
    assert Action1 is Temp1
    assert Action2 is Temp2
    assert Action2 is MyActionSameName

@raises(LanguageDoesNotResolveError)
def test_action_registry_suitable_for_raises_when_language_getter_can_not_resolve():
    class MyActionLanguage(ActionBase):
        regex = LanguageItem('foo_bar_regex1')
        def execute(self, context, *args, **kw):
            pass

    language_getter_mock = Mock()
    language_getter_mock.expects(at_least_once()).method('get').will(return_value('^$'))
    language_getter_mock.expects(once()).get(eq(LanguageItem('foo_bar_regex1'))).will(return_value(None))
    Action, args, kwargs = ActionRegistry.suitable_for('Something blabla', 'en-us', getter=language_getter_mock)

@raises(RuntimeError) # A action can not execute itself for infinite recursion reasons :)
def test_execute_action_will_not_execute_itself():
    class DoSomethingRecursiveAction(ActionBase):
        regex = r'^(And )?I do "(?P<what>\w+)" stuff$'
        def execute(self, context, getter_mock, *args, **kwargs):
            self.execute_action('And I do "recursive" stuff', context, getter=getter_mock)

    language_getter_mock = Mock()
    language_getter_mock.expects(at_least_once()).method('get').will(return_value('^$'))

    context_mock = Mock()
    context_mock.expects(once()).get_language().will(return_value('en-us'))

    dosaction = DoSomethingRecursiveAction()
    args = []
    kwargs = dict(what='nothing')

    dosaction.execute(context_mock, getter_mock=language_getter_mock, *args, **kwargs)
    context_mock.verify()