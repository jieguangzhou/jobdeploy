import click
import re
from jd.controller import build as _build, rm as _rm, ls as _ls, view as _view


@click.group()
def cli():
    ...


def parse_inputs(x):
    groups = re.finditer('"([^\']+)"', x)
    reference = {}
    for i, g in enumerate(groups):
        x = x.replace(g.group(), f'#{i}')
        reference[f'#{i}'] = g.groups()[0]
    my_dict = dict([x.split('=') for x in x.split(',')])
    for k, val in my_dict.items():
        if val.isnumeric():
            my_dict[k] = eval(val)
        elif val.startswith('#'):
            my_dict[k] = reference[val]
        elif val in {'true', 'True', 'false', 'False'}:
            my_dict[k] = val.lower() == 'true'
        elif '+' in val:
            val = val.split('+')
            val = [x for x in val if x]
            val = [eval(x) if x.isnumeric() else x for x in val]
            my_dict[k] = val
    return my_dict


class KeyValuePairs(click.ParamType):
    """Convert to key value pairs"""
    name = "key-value-pairs"

    def convert(self, value, param, ctx):
        """
        Convert to key value pairs

        :param value: value
        :param param: parameter
        :param ctx: context
        """
        if not value.strip():
            return {}
        try:
            my_dict = parse_inputs(value)
            return my_dict
        except TypeError:
            self.fail(
                "expected string for key-value-pairs() conversion, got "
                f"{value!r} of type {type(value).__name__}",
                param,
                ctx,
            )
        except ValueError:
            self.fail(f"{value!r} is not a valid key-value-pair", param, ctx)


@cli.command()
@click.option('--template', default=None, help='type of resource to list')
def ls(template):
    _ls(template)


@cli.command()
@click.argument('id')
def view(id):
    _view(id)


@cli.command()
@click.argument('id')
@click.option('--purge/--no-purge', default=False, help='purge resource')
@click.option('--down/--no-down', default=True, help='tear down resource with the down method')
def rm(id, purge, down):
    _rm(id, purge, down)


@cli.command(help='build template')
@click.argument('method')
@click.option('--template', default=None)
@click.option('--id', default=None)
@click.option('--params', default=None, help='key-value pairs to add to build',
              type=KeyValuePairs())
def build(method, template, id, params):
    print(params)
    if params is None:
        params = {}
    if isinstance(template, str) and template.endswith('.yaml'):
        template = template.split('.yaml')[0]
    _build(template, method, id=id, **params)


if __name__ == '__main__':
    cli()