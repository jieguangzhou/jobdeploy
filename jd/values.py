import json
from jinja2 import Template, StrictUndefined
from jd.utils import random_id, log_content, call_script


def get_or_create_values(template, params, meta, on_up=False):
    info_path = f'.jd/{meta["subdir"]}/info.json'
    with open(info_path) as f:
        info = json.load(f)
    existing_values = info.get('values', {})
    missing_values = {k: v for k, v in template.get('values', {}).items()
                      if k not in existing_values}

    if missing_values:
        existing_values.update(
            create_values(missing_values,
                          params,
                          meta,
                          template['config'],
                          existing_values=existing_values,
                          on_up=on_up)
        )

    info['values'] = existing_values
    with open(info_path, 'w') as f:
        json.dump(info, f)
    return existing_values


def create_values(values, params, meta, config, existing_values=None,
                  on_up=False):
    """
    Create values. Go through dictionary of values based on parameters dictionary.

    :param values: Dictionary of values with Jinja2 variables in strings.
    """
    if existing_values is None:
        existing_values = {}

    for k in values:
        if values[k]['type'] == 'static':
            if not on_up or values[k].get('on_up', True):
                existing_values[k] = \
                    create_static_value(values[k]['content'], existing_values, params, meta,
                                        config)
            else:
                print(f"didn't create static value because on_up=False: {k}")

    for k in values:
        if values[k]['type'].startswith('output/'):
            if not on_up or values[k].get('on_up', True):
                output = create_output_value(values[k]['content'], existing_values, params, meta,
                                             config)
                suffix = values[k]['type'].split('output/')[-1]
                if suffix == 'str':
                    existing_values[k] = output
                elif suffix == 'json':
                    existing_values[k] = json.loads(suffix)
                else:
                    raise NotImplementedError(f'output type for value not supported: {suffix}.')
            else:
                print(f"didn't create output value because on_up=False: {k}")
    return existing_values


def create_output_value(value, other_values, params, meta, config):
    script = Template(value, undefined=StrictUndefined).render(params=params,
                                                               meta=meta,
                                                               config=config,
                                                               values=other_values)
    id = random_id()
    print('creating value with script:')
    log_content(script)
    output = call_script(f'/tmp/{id}', script, grab_output=True, cleanup=True)
    return output


def create_static_value(value, other_values, params, meta, config):
    """
    Format a value using template parameters.

    :param value: Value to be formatted using Jinja2.
    :param other_values: Other pre-built values to be used in the value with {{ values[...] }}.
    :param params: Dictionary of parameters, referred to by {{ params[...] }}.
    """
    if isinstance(value, str):
        return Template(value, undefined=StrictUndefined).render(params=params,
                                                                 values=other_values,
                                                                 config=config,
                                                                 meta=meta)
    elif isinstance(value, list):
        return [create_static_value(x, other_values, params, config, meta) for x in value]

    elif isinstance(value, dict):
        return {k: create_static_value(value[k], other_values, params, meta, config)
                for k in value}

    else:
        raise NotImplementedError('only strings, and recursively lists and dicts supported')