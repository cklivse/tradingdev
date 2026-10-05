"""Parameter plateau analysis over the trials of a parameter grid search.

The question is whether the best parameter set is a real signal, sitting on
a broad region where nearby parameters also perform well, or a lucky spike
in the grid whose neighbours perform poorly. The module only inspects the
trials it is given and never reads jobs, runs, artifacts, or caches.

Required inputs:

* One :class:`Trial` per evaluated parameter set. ``params`` maps every
  searched parameter name to its finite numeric grid value; all trials share
  the same parameter names, and each parameter set appears at most once.
* ``metric`` is a finite score where higher is better. The caller negates
  metrics that are minimised and drops failed trials; a dropped trial is
  treated as a missing grid point.
* All metrics must come from the same evaluation window, data, and cost
  model, otherwise neighbouring scores are not comparable. No per-trial
  return series is needed by this version.

First-version design decisions (adjustable):

* Neighbourhoods use grid indices, not raw parameter distances. The distinct
  values of each parameter axis are sorted and replaced by their rank
  ``r_k``; ``theta'`` is a neighbour of ``theta`` when
  ``max_k |r_k(theta') - r_k(theta)| <= radius`` (Chebyshev distance) and
  ``theta' != theta``. The default radius is 1. This sidesteps parameters
  on different scales, but on a non-uniform grid adjacent grid points span
  different raw parameter distances, so one step of radius is not one fixed
  amount of parameter change.
* A point's plateau score is the mean metric of its neighbours, excluding
  the point itself, so a lone spike gets no credit from its own value.
* With more than three parameters a radius-1 neighbourhood holds up to
  ``3**d - 1`` points and stops being local; results flag this with
  ``dimension_warning``.
* The primary statistic is the metric gap between the best trial and the
  trial with the highest plateau score. Spikiness, the best metric's
  distance from its neighbourhood mean in neighbourhood standard
  deviations, is secondary: its denominator is a sample standard deviation
  estimated from a handful of neighbours and is unstable in small
  neighbourhoods.

Conventions:

* Incomplete grids are fine: neighbourhoods contain only trials that exist,
  and every result reports the actual neighbourhood size.
* Ties for the best metric or best plateau score go to the earliest trial
  in input order.
* Standard deviations are sample standard deviations (``ddof=1``).
* Undefined figures (no neighbours, fewer than two neighbours for a
  standard deviation, zero dispersion) are ``None`` rather than infinities
  or zeros.

Limitation: a broad plateau is not evidence against overfitting when the
whole parameter region is fitted to the same market regime. Every
neighbour then looks good for the same reason and the analysis shows a
false plateau, so plateau analysis cannot replace out-of-sample validation.
"""

from __future__ import annotations

import math
import numbers
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    import numpy.typing as npt

DEFAULT_RADIUS = 1
MAX_LOCAL_DIMENSIONS = 3


@dataclass(frozen=True)
class Trial:
    """One evaluated parameter set and its score (higher is better)."""

    params: Mapping[str, float]
    metric: float


@dataclass(frozen=True)
class PlateauScore:
    """Neighbourhood performance of one trial.

    Attributes:
        params: The trial's parameter set.
        metric: The trial's own metric.
        score: Mean metric of the trial's neighbours; ``None`` without
            neighbours.
        neighborhood_size: Number of existing neighbours, excluding the
            trial itself.
    """

    params: Mapping[str, float]
    metric: float
    score: float | None
    neighborhood_size: int


@dataclass(frozen=True)
class PlateauSummary:
    """Comparison of the best trial with the best plateau.

    Attributes:
        n_trials: Number of trials.
        n_dimensions: Number of searched parameters.
        radius: Grid-index radius used for neighbourhoods.
        dimension_warning: ``True`` when there are more than three
            parameters, so the neighbourhood is too large to be local.
        best_params: Parameters of the trial with the highest metric.
        best_metric: Highest metric.
        plateau_best_params: Parameters of the trial with the highest
            plateau score.
        plateau_best_metric: That trial's own metric.
        plateau_best_score: That trial's plateau score.
        metric_gap: ``best_metric - plateau_best_metric``, the primary
            statistic; a large gap means the best trial is not on the best
            plateau.
        grid_distance: Chebyshev grid-index distance between the best trial
            and the plateau best trial.
        best_neighborhood_mean: Mean metric of the best trial's neighbours.
        best_neighborhood_std: Sample standard deviation of those metrics.
        best_neighborhood_size: Number of the best trial's neighbours.
        spikiness: ``(best_metric - best_neighborhood_mean) /
            best_neighborhood_std``; secondary and unstable in small
            neighbourhoods.
    """

    n_trials: int
    n_dimensions: int
    radius: int
    dimension_warning: bool
    best_params: Mapping[str, float] | None
    best_metric: float | None
    plateau_best_params: Mapping[str, float] | None
    plateau_best_metric: float | None
    plateau_best_score: float | None
    metric_gap: float | None
    grid_distance: int | None
    best_neighborhood_mean: float | None
    best_neighborhood_std: float | None
    best_neighborhood_size: int | None
    spikiness: float | None


@dataclass(frozen=True)
class PlateauGrid:
    """A two-parameter slice of metrics and plateau scores for plotting.

    Cells are indexed ``[y_index][x_index]``; missing grid points are
    ``None``. Plateau scores use the full-dimensional neighbourhood, not
    only the neighbours inside the slice.

    Attributes:
        x: Parameter on the x axis.
        y: Parameter on the y axis.
        x_values: Sorted distinct values of ``x`` across all trials.
        y_values: Sorted distinct values of ``y`` across all trials.
        fixed_params: Values of the other parameters, fixed at the best
            trial's values.
        metric: Trial metric per cell.
        score: Plateau score per cell.
        neighborhood_size: Neighbourhood size per cell.
        radius: Grid-index radius used for neighbourhoods.
        dimension_warning: Same flag as :class:`PlateauSummary`.
    """

    x: str
    y: str
    x_values: tuple[float, ...]
    y_values: tuple[float, ...]
    fixed_params: Mapping[str, float]
    metric: tuple[tuple[float | None, ...], ...]
    score: tuple[tuple[float | None, ...], ...]
    neighborhood_size: tuple[tuple[int | None, ...], ...]
    radius: int
    dimension_warning: bool


@dataclass(frozen=True)
class _Grid:
    names: tuple[str, ...]
    axes: tuple[tuple[float, ...], ...]
    params: tuple[Mapping[str, float], ...]
    ranks: npt.NDArray[np.int64]
    metrics: npt.NDArray[np.float64]

    @property
    def dimension_warning(self) -> bool:
        return len(self.names) > MAX_LOCAL_DIMENSIONS

    def neighbours(self, index: int, radius: int) -> npt.NDArray[np.intp]:
        distances = np.abs(self.ranks - self.ranks[index]).max(axis=1)
        mask = distances <= radius
        mask[index] = False
        return np.flatnonzero(mask)

    def distance(self, first: int, second: int) -> int:
        return int(np.abs(self.ranks[first] - self.ranks[second]).max())


def plateau_scores(
    trials: Sequence[Trial], *, radius: int = DEFAULT_RADIUS
) -> tuple[PlateauScore, ...]:
    """Compute every trial's neighbourhood mean metric, in input order.

    Raises:
        ValueError: If ``radius`` is not a positive integer or the trials
            are inconsistent (see :class:`Trial`).
    """
    grid = _build_grid(trials)
    return _scores(grid, _checked_radius(radius))


def plateau_summary(
    trials: Sequence[Trial], *, radius: int = DEFAULT_RADIUS
) -> PlateauSummary:
    """Compare the best trial with the trial on the best plateau.

    Raises:
        ValueError: If ``radius`` is not a positive integer or the trials
            are inconsistent (see :class:`Trial`).
    """
    radius = _checked_radius(radius)
    grid = _build_grid(trials)
    scores = _scores(grid, radius)
    n_trials = len(scores)
    if n_trials == 0:
        return PlateauSummary(
            n_trials=0,
            n_dimensions=0,
            radius=radius,
            dimension_warning=False,
            best_params=None,
            best_metric=None,
            plateau_best_params=None,
            plateau_best_metric=None,
            plateau_best_score=None,
            metric_gap=None,
            grid_distance=None,
            best_neighborhood_mean=None,
            best_neighborhood_std=None,
            best_neighborhood_size=None,
            spikiness=None,
        )

    best = int(np.argmax(grid.metrics))
    best_metric = float(grid.metrics[best])
    plateau_best = _argmax_score(scores)
    neighbour_metrics = grid.metrics[grid.neighbours(best, radius)]
    mean = float(neighbour_metrics.mean()) if neighbour_metrics.size else None
    std = float(neighbour_metrics.std(ddof=1)) if neighbour_metrics.size > 1 else None
    spikiness = (
        (best_metric - mean) / std
        if mean is not None and std is not None and std > 0
        else None
    )
    plateau_best_metric = (
        float(grid.metrics[plateau_best]) if plateau_best is not None else None
    )
    return PlateauSummary(
        n_trials=n_trials,
        n_dimensions=len(grid.names),
        radius=radius,
        dimension_warning=grid.dimension_warning,
        best_params=grid.params[best],
        best_metric=best_metric,
        plateau_best_params=(
            grid.params[plateau_best] if plateau_best is not None else None
        ),
        plateau_best_metric=plateau_best_metric,
        plateau_best_score=(
            scores[plateau_best].score if plateau_best is not None else None
        ),
        metric_gap=(
            best_metric - plateau_best_metric
            if plateau_best_metric is not None
            else None
        ),
        grid_distance=(
            grid.distance(best, plateau_best) if plateau_best is not None else None
        ),
        best_neighborhood_mean=mean,
        best_neighborhood_std=std,
        best_neighborhood_size=int(neighbour_metrics.size),
        spikiness=spikiness,
    )


def plateau_grid(
    trials: Sequence[Trial],
    *,
    x: str,
    y: str,
    radius: int = DEFAULT_RADIUS,
) -> PlateauGrid:
    """Lay out metrics and plateau scores on two parameter axes.

    Parameters other than ``x`` and ``y`` are fixed at the best trial's
    values. Empty ``trials`` yield an empty grid.

    Raises:
        ValueError: If ``x`` equals ``y``, either is not a searched
            parameter, ``radius`` is not a positive integer, or the trials
            are inconsistent (see :class:`Trial`).
    """
    radius = _checked_radius(radius)
    if x == y:
        raise ValueError("x and y must be different parameters")
    grid = _build_grid(trials)
    if not grid.params:
        return PlateauGrid(
            x=x,
            y=y,
            x_values=(),
            y_values=(),
            fixed_params=MappingProxyType({}),
            metric=(),
            score=(),
            neighborhood_size=(),
            radius=radius,
            dimension_warning=False,
        )
    for name in (x, y):
        if name not in grid.names:
            raise ValueError(f"{name!r} is not a searched parameter")

    scores = _scores(grid, radius)
    best_params = grid.params[int(np.argmax(grid.metrics))]
    fixed = {k: v for k, v in best_params.items() if k not in (x, y)}
    x_values = grid.axes[grid.names.index(x)]
    y_values = grid.axes[grid.names.index(y)]
    x_index = {value: i for i, value in enumerate(x_values)}
    y_index = {value: i for i, value in enumerate(y_values)}

    metric: list[list[float | None]] = [[None] * len(x_values) for _ in y_values]
    score: list[list[float | None]] = [[None] * len(x_values) for _ in y_values]
    sizes: list[list[int | None]] = [[None] * len(x_values) for _ in y_values]
    for entry in scores:
        if any(entry.params[k] != v for k, v in fixed.items()):
            continue
        row = y_index[entry.params[y]]
        column = x_index[entry.params[x]]
        metric[row][column] = entry.metric
        score[row][column] = entry.score
        sizes[row][column] = entry.neighborhood_size

    return PlateauGrid(
        x=x,
        y=y,
        x_values=x_values,
        y_values=y_values,
        fixed_params=MappingProxyType(fixed),
        metric=tuple(tuple(row) for row in metric),
        score=tuple(tuple(row) for row in score),
        neighborhood_size=tuple(tuple(row) for row in sizes),
        radius=radius,
        dimension_warning=grid.dimension_warning,
    )


def _scores(grid: _Grid, radius: int) -> tuple[PlateauScore, ...]:
    results = []
    for index, params in enumerate(grid.params):
        neighbour_metrics = grid.metrics[grid.neighbours(index, radius)]
        results.append(
            PlateauScore(
                params=params,
                metric=float(grid.metrics[index]),
                score=(
                    float(neighbour_metrics.mean()) if neighbour_metrics.size else None
                ),
                neighborhood_size=int(neighbour_metrics.size),
            )
        )
    return tuple(results)


def _argmax_score(scores: Sequence[PlateauScore]) -> int | None:
    best: int | None = None
    best_score = -math.inf
    for index, entry in enumerate(scores):
        if entry.score is not None and (best is None or entry.score > best_score):
            best, best_score = index, entry.score
    return best


def _build_grid(trials: Sequence[Trial]) -> _Grid:
    if not trials:
        return _Grid(
            names=(),
            axes=(),
            params=(),
            ranks=np.empty((0, 0), dtype=np.int64),
            metrics=np.empty(0, dtype=np.float64),
        )

    names = tuple(sorted(trials[0].params))
    if not names:
        raise ValueError("trials must have at least one parameter")
    params: list[Mapping[str, float]] = []
    seen: set[tuple[float, ...]] = set()
    metrics: list[float] = []
    for position, trial in enumerate(trials):
        if set(trial.params) != set(names):
            raise ValueError(f"trial {position} has different parameter names")
        values = tuple(
            _finite(trial.params[name], f"trial {position} parameter {name!r}")
            for name in names
        )
        if values in seen:
            raise ValueError(f"trial {position} repeats an earlier parameter set")
        seen.add(values)
        params.append(MappingProxyType(dict(zip(names, values, strict=True))))
        metrics.append(_finite(trial.metric, f"trial {position} metric"))

    axes = tuple(tuple(sorted({p[name] for p in params})) for name in names)
    rank_of = [{value: rank for rank, value in enumerate(axis)} for axis in axes]
    ranks = np.array(
        [[rank_of[k][p[name]] for k, name in enumerate(names)] for p in params],
        dtype=np.int64,
    )
    return _Grid(
        names=names,
        axes=axes,
        params=tuple(params),
        ranks=ranks,
        metrics=np.array(metrics, dtype=np.float64),
    )


def _finite(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, numbers.Real):
        raise ValueError(f"{label} is not numeric")
    if not math.isfinite(value):
        raise ValueError(f"{label} is not finite")
    return float(value)


def _checked_radius(radius: int) -> int:
    if isinstance(radius, bool) or not isinstance(radius, int) or radius < 1:
        raise ValueError("radius must be a positive integer")
    return radius
