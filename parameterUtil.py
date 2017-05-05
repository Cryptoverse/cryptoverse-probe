def hasAny(params):
	return params and 0 < len(params)

def hasCount(params, count):
	return len(params) == count

def hasSingle(params):
	return params and hasAny(params) and len(params) == 1

def singleInt(params):
	return int(params[0]) if hasAny(params) else None

def singleStr(params):
	return str(params[0]) if hasAny(params) else None

def retrieve(params, keyword, foundValue, defaultValue):
	if params:
		for param in params:
			if param == keyword:
				return foundValue
	return defaultValue

def retrieveValue(params, keyword, defaultValue):
	if params:
		count = len(params)
		for i in range(0, count):
			if params[i] == keyword and i + 1 < count:
				return params[i + 1]
	return defaultValue

def naturalMatch(query, values):
	closest = None
	closestIndex = -1
	for value in values:
		currIndex = value.find(query)
		if currIndex == -1:
			continue
		if closestIndex == -1 or currIndex < closestIndex:
			closest = value
			closestIndex = currIndex
	return closest