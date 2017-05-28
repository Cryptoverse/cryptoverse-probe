def has_any(params):
    return params and 0 < len(params)


def has_count(params, count):
    return len(params) == count


def has_at_least(params, count):
    return count <= len(params)


def has_single(params):
    return params and has_any(params) and len(params) == 1


def single_int(params):
    return int(params[0]) if has_any(params) else None


def single_str(params):
    return str(params[0]) if has_any(params) else None


def retrieve(params, keyword, found_value, default_value):
    if params:
        for param in params:
            if param == keyword:
                return found_value
    return default_value


def retrieve_value(params, keyword, default_value):
    if params:
        count = len(params)
        for i in range(0, count):
            if params[i] == keyword and i + 1 < count:
                return params[i + 1]
    return default_value


def natural_match(query, values):
    closest = None
    closest_index = -1
    for value in values:
        curr_index = value.find(query)
        if curr_index == -1:
            continue
        if closest_index == -1 or curr_index < closest_index:
            closest = value
            closest_index = curr_index
    return closest
