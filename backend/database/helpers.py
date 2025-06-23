# backend/database/postgres/helpers.py
import inspect
from functools import wraps
from typing import List, Dict, Any, Callable

def set_data_protection_level(data_arg_name: str):
    """
    PostgreSQL version of data protection level setter.
    For PostgreSQL, we'll use a default level since we don't need
    the complex Firestore caching logic.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
            except TypeError:
                return func(*args, **kwargs)

            data: Dict[str, Any] | List[Dict[str, Any]] | None = bound_args.arguments.get(data_arg_name)

            if not isinstance(data, (dict, list)):
                return func(*args, **kwargs)

            # For PostgreSQL, default to 'standard' level
            level = 'standard'

            if isinstance(data, dict):
                if data.get('data_protection_level') is None:
                    data['data_protection_level'] = level
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        if item.get('data_protection_level') is None:
                            item['data_protection_level'] = level

            return func(*args, **kwargs)
        return wrapper
    return decorator


def prepare_for_write(data_arg_name: str, prepare_func: Callable[[Dict[str, Any], str, str], Dict[str, Any]]):
    """
    PostgreSQL version of write preparation decorator.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            uid = bound_args.arguments.get('uid')
            original_data = bound_args.arguments.get(data_arg_name)

            if not uid or not isinstance(original_data, (dict, list)):
                func(*args, **kwargs)
                return original_data

            prepared_data = original_data

            if isinstance(original_data, dict):
                prepared_data = prepare_func(original_data, uid, original_data.get('data_protection_level', 'standard'))
            elif isinstance(original_data, list):
                if original_data and isinstance(original_data[0], dict):
                    prepared_data = [prepare_func(item, uid, item.get('data_protection_level', 'standard')) for item in original_data]

            bound_args.arguments[data_arg_name] = prepared_data
            func(*bound_args.args, **bound_args.kwargs)

            return original_data
        return wrapper
    return decorator


def prepare_for_read(decrypt_func: Callable[[Dict[str, Any], str], Dict[str, Any]]):
    """
    PostgreSQL version of read preparation decorator.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            uid = bound_args.arguments.get('uid')
            
            if not uid:
                raise TypeError(f"Function {func.__name__} decorated with prepare_for_read must have a 'uid' argument.")

            result = func(*args, **kwargs)

            if result is None:
                return None

            def _process(item):
                if isinstance(item, dict):
                    return decrypt_func(item, uid)
                return item

            if isinstance(result, dict):
                return _process(result)
            elif isinstance(result, list):
                return [_process(item) for item in result]
            elif isinstance(result, tuple):
                processed_elements = []
                for element in result:
                    if isinstance(element, dict):
                        processed_elements.append(_process(element))
                    elif isinstance(element, list):
                        processed_elements.append([_process(item) for item in element])
                    else:
                        processed_elements.append(element)
                return tuple(processed_elements)
            return result
        return wrapper
    return decorator