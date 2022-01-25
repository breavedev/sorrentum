"""
Import as:

import dataflow.system.system_tester as dtfsysytes
"""

import logging
from typing import List, Tuple, Union

import pandas as pd

import dataflow.model as dtfmod
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


class SystemTester:
    """
    Test a System.
    """

    def get_events_signature(self, events) -> str:
        # TODO(gp): Use events.to_str()
        actual = ["# event signature=\n"]
        events_as_str = "\n".join(
            [
                event.to_str(
                    include_tenths_of_secs=False,
                    include_wall_clock_time=False,
                )
                for event in events
            ]
        )
        actual.append("events_as_str=\n%s" % events_as_str)
        actual = "\n".join(actual)
        return actual

    def get_portfolio_signature(self, portfolio) -> Tuple[str, pd.Series]:
        actual = ["\n# portfolio signature=\n"]
        actual.append(str(portfolio))
        actual = "\n".join(actual)
        statistics = portfolio.get_historical_statistics()
        pnl = statistics["pnl"]
        _LOG.debug("pnl=\n%s", pnl)
        return actual, pnl

    def get_research_pnl_signature(
        self,
        result_bundle,
        *,
        returns_col: str,
        volatility_col: str,
        prediction_col: str,
        target_gmv: float = 100000,
        dollar_neutral: bool = False,
    ) -> Tuple[str, pd.Series]:
        actual = ["\n# forecast_evaluator signature=\n"]
        forecast_evaluator = dtfmod.ForecastEvaluator(
            returns_col=returns_col,
            volatility_col=volatility_col,
            prediction_col=prediction_col,
        )
        result_df = result_bundle.result_df
        signature = forecast_evaluator.to_str(
            result_df,
            target_gmv=target_gmv,
            dollar_neutral=dollar_neutral,
        )
        actual.append(signature)
        _, _, stats = forecast_evaluator.compute_portfolio(
            result_df,
            target_gmv=target_gmv,
            dollar_neutral=dollar_neutral,
        )
        research_pnl = stats["pnl"]
        actual = "\n".join(map(str, actual))
        return actual, research_pnl

    def compute_run_signature(
        self,
        dag_runner,
        portfolio,
        result_bundle,
        *,
        returns_col: str,
        volatility_col: str,
        prediction_col: str,
    ) -> str:
        # Check output.
        actual = []
        #
        events = dag_runner.events
        actual.append(self.get_events_signature(events))
        signature, pnl = self.get_portfolio_signature(portfolio)
        actual.append(signature)
        signature, research_pnl = self.get_research_pnl_signature(
            result_bundle,
            returns_col=returns_col,
            volatility_col=volatility_col,
            prediction_col=prediction_col,
        )
        actual.append(signature)
        if min(pnl.count(), research_pnl.count()) > 1:
            # Resample `pnl` so that its datetime index aligns on even bars, like
            #  research_pnl's does.
            freq = research_pnl.index.freq
            pnl = pnl.resample(rule=freq).sum(min_count=1)
            _LOG.debug("resampled pnl=\n%s", pnl)
            correlation = pnl.corr(research_pnl)
            actual.append("\n# pnl agreement with research pnl\n")
            actual.append(f"corr = {correlation:.3f}")
        actual = "\n".join(map(str, actual))
        return actual

    @staticmethod
    def _append(
        list_: List[str], label: str, data: Union[pd.Series, pd.DataFrame]
    ) -> None:
        data_str = hunitest.convert_df_to_string(data, index=True, decimals=3)
        list_.append(f"{label}=\n{data_str}")