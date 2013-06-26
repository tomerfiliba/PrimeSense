from functools import partial
import logging

# class HelloWorld(Plugin):
#     name = 'helloworld'
# 
#     def options(self, parser, env=os.environ):
#         super(HelloWorld, self).options(parser, env=env)
# 
#     def configure(self, options, conf):
#         super(HelloWorld, self).configure(options, conf)
#         if not self.enabled:
#             return
# 
#     def addError(self, test, ex):
#         pass
# 
#     def addFailure(self, test, ex):
#         pass
# 
#     def addSuccess(self, test):
#         pass
# 
#     def finalize(self, result):
#         log.info('Hello pluginized world!')


def foo(a, b, c):
    assert a + b == c 


def test_suite():
    for i in range(10):
        f = partial(foo, i, 20 - i, 20)
        f.description = "%s.%s %s" % (foo.__module__, foo.__name__, i)
        yield f




