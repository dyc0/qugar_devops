# --------------------------------------------------------------------------
#
# Copyright (C) 2025-present by Pablo Antolin
#
# This file is part of the QUGaR library.
#
# SPDX-License-Identifier:    MIT
#
# --------------------------------------------------------------------------

"""Data structures and functionalities for dealing with integrals."""

from qugar.utils import has_FEniCSx

if not has_FEniCSx:
    raise ValueError("FEniCSx installation not found is required.")

from typing import NamedTuple

import dolfinx.cpp.fem
import ffcx.analysis
import ffcx.ir.representation
import numpy as np
import numpy.typing as npt
import ufl.domain
import ufl.geometry

from qugar.dolfinx.fe_table import FETable, extract_FE_tables
from qugar.dolfinx.quadrature_data import QuadratureData, extract_quadrature_data


def _get_integral_subdomain_ids(ir: ffcx.ir.representation.DataIR, name: str) -> list[int]:
    """Extracts the subdomain ids of the integrals in `ir` that have the
    given `name`.

    Args:
        ir (ffcx.ir.representation.DataIR): FFCx Intermediate
            Representation that contains the integrals to be inspected.
        name (str): Integral sought. This string must start with
            ``integral_``.

    Note:
        This function's implementation assumes that ordering the
        subdomain ids stored in the dictionary `form.integral_names`
        (for each form and integral type) matches the ordering of the
        names in `form.integral_names` (for each form and integral
        type).


    Returns:
        list[int]: Subdomain ids of the integrals associated to the
        given `name`.
    """

    for form in ir.forms:
        for itg_type, names in form.integral_names.items():
            all_ids = form.subdomain_ids[itg_type]
            ids = [id for i, id in enumerate(all_ids) if names[i] == name]
            if len(ids) > 0:
                return ids
    return list()


def _get_integral_dimension(
    ir: ffcx.ir.representation.DataIR, itg_ir: ffcx.ir.representation.IntegralIR
) -> int:
    """Gets the topology dimension associated to the given integral
    representation.

    E.g., dimension 2 if the integral is performed inside (or on the
    facet of) triangles or quadrilaterals. Dimension 3 in the case of
    tetrahedra, hexahedra, etc.

    Note:
        This dimension is extracted from the topology dimension of the
        coordinate element associated to the mesh in which the integral
        is computed.

    Arguments:
        ir (ffcx.ir.representation.DataIR): FFCx Intermediate
            Representation that contains the integral `ir_itg`.
        itg_ir (ffcx.ir.representation.IntegralIR): FFCx Intermediate
            Representation of the integral to be modified.

    Returns:
        int: Topology dimension of the integral.
    """

    # Code adapted from function generate_geometry_fables in file
    # ffcx.codegeneration.integral_generator
    cells = set()
    for integrand in itg_ir.expression.integrand.values():
        for attr in integrand["factorization"].nodes.values():
            mt = attr.get("mt")
            if mt is not None:
                if issubclass(type(mt.terminal), ufl.geometry.GeometricQuantity):
                    domain = ufl.domain.extract_unique_domain(mt.terminal)
                    assert domain is not None
                    cells.add(domain.ufl_cell())
    assert len(cells) == 1

    cell = cells.pop()
    return cell.topological_dimension()


class IntegralData(NamedTuple):
    """Class for storing inmutable infomation associated to an integral.

    Parameters:
        name (str): Integral name containing the prefix ``integral_``.
        subdomain_ids (list[int]): Ids of the integral's subdomain.
        integral_type (str): Integral type.
        tdim (int): Topology dimension associated to the given
            integral's domain. E.g., dimension 2 if the integral is
            performed inside (or on the facet of) triangles or
            quadrilaterals. Dimension 3 in the case of tetrahedra,
            hexahedra, etc. domain.
        is_mixed_dim (bool): Flag indicating whether the integral
            presents mixed dimensions among elements and integration
            domain.
        quad_data_and_FE_tables (dict[QuadratureData, list[FETable]]):
            Dictionary mapping quadrature data to all the FE tables
            that share the same quadrature. The ordering of the tables
            for each quadrature stays constant between successive Python
            calls, what allows to reuse previously cached compiled
            forms.
    """

    name: str
    subdomain_ids: list[int]
    integral_type: str
    tdim: int
    is_mixed_dim: bool
    quad_data_FE_tables: dict[QuadratureData, list[FETable]]

    @property
    def dtype(self) -> type[np.float32 | np.float64]:
        """`numpy` type used in the integral."""
        FE_tables = next(iter(self.quad_data_FE_tables.values()))
        assert FE_tables
        return FE_tables[0].dtype

    @property
    def itg_infos(self) -> list[tuple[dolfinx.cpp.fem.IntegralType, int]]:
        """Tuple of integral type and integral's subdomain id."""
        itg_type_strs = {
            "cell": dolfinx.cpp.fem.IntegralType.cell,
            "interior_facet": dolfinx.cpp.fem.IntegralType.interior_facet,
            "exterior_facet": dolfinx.cpp.fem.IntegralType.exterior_facet,
        }
        itg_type = itg_type_strs[self.integral_type]
        return [(itg_type, id) for id in self.subdomain_ids]


def extract_integral_data(
    ufl_analysis: ffcx.analysis.UFLData,
    ir: ffcx.ir.representation.DataIR,
    itg_ir: ffcx.ir.representation.IntegralIR,
    ffcx_options: dict[str, int | float | npt.DTypeLike],
    itg_impl: str,
) -> IntegralData:
    """Extracts the integral data from its intermediate representation.

    Args:
        ufl_analysis (ffcx.analysis.UFLData): UFL (anlysis) data
            structure holding, among others, the UFL form data objects
            that contain the sought integral.
        ir (ffcx.ir.representation.DataIR): FFCx Intermediate
            Representation that contains elements, forms, coordinate
            mappings, and integrals.
        itg_ir (ffcx.ir.representation.IntegralIR): FFCx Intermedia
            Representation of the integral whose data is extracted.
        ffcx_options (dict[str, int | float | npt.DTypeLike]): FFCx
            options used for generating the code.
        itg_impl (str): C code of the integral implementation.

    Returns:
        IntegralData: Data associated to the integral `itg_ir`.
    """

    itg_name = itg_ir.expression.name
    tdim = _get_integral_dimension(ir, itg_ir)
    itg_ids = _get_integral_subdomain_ids(ir, itg_name)
    assert len(itg_ids) > 0

    short_itg_name = itg_name[len("integral_") :]

    all_quads_data = extract_quadrature_data(ufl_analysis, ffcx_options)
    FE_tables = extract_FE_tables(itg_impl, itg_ir, all_quads_data, tdim)

    is_mixed_dim = False

    quad_FE_tables = {}
    for FE_table in FE_tables:
        quad_name = FE_table.quad_name
        quad_data = all_quads_data[quad_name]
        if quad_data not in quad_FE_tables.keys():
            quad_FE_tables[quad_data] = []
        quad_FE_tables[quad_data].append(FE_table)
        if FE_table.element_dim != tdim:
            is_mixed_dim = True

    return IntegralData(
        short_itg_name,
        itg_ids,
        itg_ir.expression.integral_type,
        tdim,
        is_mixed_dim,
        quad_FE_tables,
    )
