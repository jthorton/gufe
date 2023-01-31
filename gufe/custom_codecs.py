# This code is part of OpenFE and is licensed under the MIT license.
# For details, see https://github.com/OpenFreeEnergy/gufe

# custom_codecs.py: A place to keep various custom JSONCodec instances

import pathlib
import numpy as np

import gufe
from gufe.custom_json import JSONCodec
from gufe.settings.models import SettingsBaseModel
import openff.units
import functools
import pint.util
from openff.units import DEFAULT_UNIT_REGISTRY

def default_from_dict(dct):
    dct = dict(dct)  # make a copy
    module = dct.pop('__module__')
    qualname = dct.pop('__class__')
    del dct[':is_custom:']

    cls = gufe.tokenization.get_class(module, qualname)
    return cls(**dct)


def inherited_is_my_dict(dct, cls):
    if not ("__module__" in dct and "__class__" in dct):
        return False
    dct = dict(dct)
    module = dct.pop('__module__')
    classname = dct.pop('__class__')
    stored = gufe.tokenization.get_class(module, classname)
    return cls in stored.mro()

def is_openff_unit(obj):
    return isinstance(obj, DEFAULT_UNIT_REGISTRY.Unit)

def is_openff_quantity(obj):
    return isinstance(obj, DEFAULT_UNIT_REGISTRY.Quantity)

def openff_unit_to_dict(unit):
    return {":is_custom:": True,
            "pint_unit_registry": "openff_units",
            "unit_name": str(unit)}

def is_openff_unit_dict(dct):
    expected = ['pint_unit_registry', 'unit_name', ':is_custom:']
    is_custom = all(exp in dct for exp in expected)
    return is_custom and dct['pint_unit_registry'] == "openff_units"

def is_openff_quantity_dict(dct):
    expected = ['pint_unit_registry', 'magnitude', ':is_custom:', "unit"]
    is_custom = all(exp in dct for exp in expected)
    return is_custom and dct['pint_unit_registry'] == "openff_units"


def openff_unit_from_dict(dct):
    return openff.units.DEFAULT_UNIT_REGISTRY(dct["unit_name"]).u

PATH_CODEC = JSONCodec(
    cls=pathlib.Path,
    to_dict=lambda p: {'path': str(p)},
    from_dict=lambda dct: pathlib.Path(dct['path'])
)

BYTES_CODEC = JSONCodec(
    cls=bytes,
    to_dict=lambda obj: {'latin-1': obj.decode('latin-1')},
    from_dict=lambda dct: dct['latin-1'].encode('latin-1'),
)

NUMPY_CODEC = JSONCodec(
    cls=np.ndarray,
    to_dict=lambda obj: {
        'dtype': str(obj.dtype),
        'shape': list(obj.shape),
        'bytes': obj.tobytes()
    },
    from_dict=lambda dct: np.frombuffer(
        dct['bytes'], dtype=np.dtype(dct['dtype'])
    ).reshape(dct['shape'])
)

SETTINGS_CODEC = JSONCodec(
    cls=SettingsBaseModel,
    to_dict=lambda obj: {field: getattr(obj, field)
                         for field in obj.__fields__},
    from_dict=default_from_dict,
    is_my_dict=functools.partial(inherited_is_my_dict,
                                 cls=SettingsBaseModel)
)

OPENFF_QUANTITY_CODEC = JSONCodec(
    cls=None,
    to_dict=lambda obj: {'magnitude': obj.m, 'unit': obj.u, ":is_custom:": True,
        "pint_unit_registry": "openff_units",},
    from_dict=lambda dct: dct['magnitude'] * dct['unit'],
    is_my_obj=is_openff_quantity,
    is_my_dict=is_openff_quantity_dict,
)

OPENFF_UNIT_CODEC = JSONCodec(
    cls=None,
    to_dict=openff_unit_to_dict,
    from_dict=openff_unit_from_dict,
    is_my_obj=is_openff_unit,
    is_my_dict=is_openff_unit_dict,
)
