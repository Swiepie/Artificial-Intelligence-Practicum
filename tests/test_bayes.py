"""Tests voor de Bayesiaanse wegschatting."""

import pytest

from algorithms.bayesian_road import BayesianRoadEstimator
from input_data.road import (
    Road,
    RoadReport,
    RoadReportSource,
    RoadStatus,
    Weather,
    RoadProbabilities,
)


def test_posterior_storm_n1_n2(scenario2):
    """Doel / Input: S2 N1->N2 / Verwacht: .0011/.1687/.8302 / Faalt nu? nee."""
    estimator = BayesianRoadEstimator(scenario2.road_probabilities, scenario2.road_reports)
    belief = estimator.estimate(scenario2.graph.get_road("N1", "N2"))
    assert belief.probabilities[RoadStatus.OPEN] == pytest.approx(0.0011, abs=1e-4)
    assert belief.probabilities[RoadStatus.CONGESTED] == pytest.approx(0.1687, abs=1e-4)
    assert belief.probabilities[RoadStatus.BLOCKED] == pytest.approx(0.8302, abs=1e-4)


def test_som_is_een(scenario1, scenario2, scenario3):
    """Doel / Input: alle wegen S1-S3 / Verwacht: som posterior 1 / Faalt nu? nee."""
    for scenario in (scenario1, scenario2, scenario3):
        estimator = BayesianRoadEstimator(
            scenario.road_probabilities, scenario.road_reports
        )
        for belief in estimator.estimate_all(scenario.graph.roads).values():
            assert sum(belief.probabilities.values()) == pytest.approx(1.0, abs=1e-9)


def test_geen_meldingen_geeft_prior(scenario2):
    """Doel / Input: onbekende weg en Storm / Verwacht: .15/.35/.50 / Faalt nu? nee."""
    estimator = BayesianRoadEstimator(
        scenario2.road_probabilities,
        (),
        default_weather=Weather.STORM,
    )
    belief = estimator.estimate(Road("X", "Y", 1, "street", 1))
    assert belief.probabilities[RoadStatus.OPEN] == pytest.approx(0.15, abs=1e-4)
    assert belief.probabilities[RoadStatus.CONGESTED] == pytest.approx(0.35, abs=1e-4)
    assert belief.probabilities[RoadStatus.BLOCKED] == pytest.approx(0.50, abs=1e-4)


def test_extra_blocked_melding_verhoogt_blocked(scenario2):
    """Doel / Input: extra Police Blocked / Verwacht: P(Blocked) stijgt strikt / Faalt nu? nee."""
    road = scenario2.graph.get_road("N1", "N2")
    base = BayesianRoadEstimator(
        scenario2.road_probabilities, scenario2.road_reports
    ).estimate(road)
    extra = (*scenario2.road_reports, RoadReport(
        "N1", "N2", Weather.STORM, RoadReportSource.POLICE, RoadStatus.BLOCKED
    ))
    changed = BayesianRoadEstimator(
        scenario2.road_probabilities, extra
    ).estimate(road)
    assert changed.blocked_probability > base.blocked_probability


def test_tegenstrijdige_meldingen(scenario2):
    """Doel / Input: Citizen Open en Police Blocked bij Storm.

    Verwacht: Police weegt zwaarder. Handberekening voor Open versus Blocked:
    Open = .15*.70*.02=.0021, Congested=.35*.20*.08=.0056 en
    Blocked=.50*.10*.90=.045; na normalisatie is P(Blocked)=.8539.
    Faalt nu? nee.
    """
    road = Road("X", "Y", 1, "street", 1)
    reports = (
        RoadReport("X", "Y", Weather.STORM, RoadReportSource.CITIZEN, RoadStatus.OPEN),
        RoadReport("X", "Y", Weather.STORM, RoadReportSource.POLICE, RoadStatus.BLOCKED),
    )
    belief = BayesianRoadEstimator(scenario2.road_probabilities, reports).estimate(road)
    assert belief.blocked_probability > belief.probabilities[RoadStatus.OPEN]
    assert belief.blocked_probability == pytest.approx(0.8539, abs=1e-4)


def test_nulkans_gooit_fout(scenario2):
    """Doel / Input: CPT met nul likelihood / Verwacht: ValueError / Faalt nu? nee."""
    raw = scenario2.road_probabilities
    likelihood = {
        source: {
            status: dict(values)
            for status, values in statuses.items()
        }
        for source, statuses in raw.report_likelihood.items()
    }
    for status in RoadStatus:
        likelihood[RoadReportSource.CITIZEN][status][RoadStatus.OPEN] = 0.0
        likelihood[RoadReportSource.CITIZEN][status][RoadStatus.BLOCKED] = 0.0
        likelihood[RoadReportSource.CITIZEN][status][RoadStatus.CONGESTED] = 0.0
    probabilities = RoadProbabilities(
        raw.weather_prior, raw.road_status_given_weather, likelihood
    )
    report = RoadReport("X", "Y", Weather.STORM, RoadReportSource.CITIZEN, RoadStatus.OPEN)
    with pytest.raises(ValueError):
        BayesianRoadEstimator(probabilities, (report,)).estimate(
            Road("X", "Y", 1, "street", 1)
        )
