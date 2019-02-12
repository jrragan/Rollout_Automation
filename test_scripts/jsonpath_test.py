from jsonpath_ng import jsonpath, parse

jsonpath_expr = parse('foo[*].baz')
result = [match.value for match in jsonpath_expr.find({'foo': [{'baz': 1}, {'baz': 2}]})]
print(result)

jsonpath_expr = parse('objects[cow]')
result = [match.value for match in jsonpath_expr.find({'objects': [{'cow': 'moo'},{'cat': 'neigh'}]})]
print(result)