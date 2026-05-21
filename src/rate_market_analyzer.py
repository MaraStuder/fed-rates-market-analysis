import os
import duckdb
import pandas as pd
import matplotlib.pyplot as plt


class RateMarketAnalyzer:
    """
    Analyzes the relationship between the Federal Funds Rate
    and S&P 500 equity market performance using FRED data
    stored in a local DuckDB database.
    """

    def __init__(self, db_path="data/fed_rates.db"):
        """
        Initialize the analyzer and load data from the database.

        Parameters
        ----------
        db_path : str
            Path to the DuckDB database file.

        Raises
        ------
        FileNotFoundError
            If the database file does not exist.
        """
        if not os.path.exists(db_path):
            raise FileNotFoundError(
                f"Database not found: {db_path}. "
                "Run data/build_database.py first."
            )
        self.conn = duckdb.connect(db_path, read_only=True)
        self.observations = self.conn.execute(
            "SELECT * FROM observations"
        ).df()
        self.series = self.conn.execute(
            "SELECT * FROM series"
        ).df()
        self.observations["date"] = pd.to_datetime(
            self.observations["date"]
        )
        self.name_map = dict(zip(
            self.series["series_id"],
            self.series["title"]
        ))

    # ── HELPER METHODS ──────────────────────────────────────────────

    def available_series(self):
        """
        Return all available series IDs with readable names.

        Returns
        -------
        dict
            Mapping of series_id to title.
        """
        return self.name_map

    def get_series(self, series_id, start=None, end=None):
        """
        Load one time series from the database.

        Parameters
        ----------
        series_id : str
            FRED series ID. Must be one of the available series.
        start : str, optional
            Start date in 'YYYY-MM-DD' format.
        end : str, optional
            End date in 'YYYY-MM-DD' format.

        Returns
        -------
        pd.DataFrame
            DataFrame with columns [date, value].

        Raises
        ------
        ValueError
            If series_id is not in the database.
        ValueError
            If start is later than end.
        """
        if series_id not in self.name_map:
            raise ValueError(
                f"'{series_id}' not found. "
                f"Valid options: {list(self.name_map.keys())}"
            )
        if start and end and start > end:
            raise ValueError(
                f"start ('{start}') must be before end ('{end}')."
            )
        df = self.observations[
            self.observations["series_id"] == series_id
        ].copy()
        if start:
            df = df[df["date"] >= pd.to_datetime(start)]
        if end:
            df = df[df["date"] <= pd.to_datetime(end)]
        return df.sort_values("date").reset_index(drop=True)

    # ── OUTPUT METHODS ──────────────────────────────────────────────

    def summary_statistics(self, start=None, end=None):
        """
        Return summary statistics for both series.

        Parameters
        ----------
        start : str, optional
            Start date in 'YYYY-MM-DD' format.
        end : str, optional
            End date in 'YYYY-MM-DD' format.

        Returns
        -------
        pd.DataFrame
            Table with count, mean, std, min, max per series.
        """
        frames = []
        for sid in ["FEDFUNDS", "SP500"]:
            df = self.get_series(sid, start, end)
            stats = df["value"].agg(
                ["count", "mean", "std", "min", "max"]
            ).round(2)
            stats.name = self.name_map[sid]
            frames.append(stats)
        return pd.DataFrame(frames)

    def plot_both(self, start=None, end=None):
        """
        Plot the Federal Funds Rate and S&P 500 on a dual y-axis chart.

        Parameters
        ----------
        start : str, optional
            Start date in 'YYYY-MM-DD' format.
        end : str, optional
            End date in 'YYYY-MM-DD' format.

        Returns
        -------
        matplotlib.axes.Axes
        """
        rates = self.get_series("FEDFUNDS", start, end)
        sp500 = self.get_series("SP500", start, end)

        fig, ax1 = plt.subplots(figsize=(11, 5))
        ax1.plot(rates["date"], rates["value"],
                 color="red", label="Fed Funds Rate", linewidth=1.5)
        ax1.set_ylabel("Federal Funds Rate (%)", color="red")
        ax1.tick_params(axis="y", labelcolor="red")

        ax2 = ax1.twinx()
        ax2.plot(sp500["date"], sp500["value"],
                 color="steelblue", label="S&P 500", linewidth=1.5)
        ax2.set_ylabel("S&P 500 Index", color="steelblue")
        ax2.tick_params(axis="y", labelcolor="steelblue")

        ax1.set_title(
            "Federal Funds Rate vs S&P 500 Index",
            fontsize=13, fontweight="bold"
        )
        ax1.set_xlabel("Year")
        ax1.grid(True, alpha=0.3)
        fig.tight_layout()
        return ax1

    def plot_scatter(self, start=None, end=None):
        """
        Scatter plot of interest rates vs S&P 500 levels.

        Parameters
        ----------
        start : str, optional
            Start date in 'YYYY-MM-DD' format.
        end : str, optional
            End date in 'YYYY-MM-DD' format.

        Returns
        -------
        matplotlib.axes.Axes
        """
        rates = self.get_series(
            "FEDFUNDS", start, end
        ).set_index("date")["value"]
        sp500 = self.get_series(
            "SP500", start, end
        ).set_index("date")["value"]

        merged = pd.concat(
            [rates, sp500], axis=1
        ).dropna()
        merged.columns = ["rate", "sp500"]

        fig, ax = plt.subplots(figsize=(7, 5))
        ax.scatter(merged["rate"], merged["sp500"],
                   alpha=0.4, color="steelblue", edgecolors="none")
        ax.set_xlabel("Federal Funds Rate (%)")
        ax.set_ylabel("S&P 500 Index")
        ax.set_title(
            "Interest Rate vs Stock Market Level",
            fontsize=13, fontweight="bold"
        )
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        return ax

    def plot_rolling_correlation(self, window=12,
                                  start=None, end=None):
        """
        Plot the rolling correlation between rate changes
        and S&P 500 changes over time.

        Parameters
        ----------
        window : int
            Rolling window size in months. Default 12.
        start : str, optional
            Start date in 'YYYY-MM-DD' format.
        end : str, optional
            End date in 'YYYY-MM-DD' format.

        Returns
        -------
        matplotlib.axes.Axes

        Raises
        ------
        ValueError
            If window is not a positive integer.
        """
        if not isinstance(window, int) or window < 1:
            raise ValueError(
                "window must be a positive integer, "
                f"got: {window}"
            )
        rates = self.get_series(
            "FEDFUNDS", start, end
        ).set_index("date")["value"]
        sp500 = self.get_series(
            "SP500", start, end
        ).set_index("date")["value"]

        merged = pd.concat(
            [rates, sp500], axis=1
        ).dropna()
        merged.columns = ["rate", "sp500"]
        pct = merged.pct_change().dropna()

        rolling = pct["rate"].rolling(
            window
        ).corr(pct["sp500"])

        fig, ax = plt.subplots(figsize=(11, 4))
        ax.plot(rolling.index, rolling,
                color="purple", linewidth=1.5)
        ax.axhline(0, color="black",
                   linewidth=0.8, linestyle="--")
        ax.fill_between(rolling.index, rolling, 0,
                        where=(rolling < 0),
                        alpha=0.2, color="red")
        ax.fill_between(rolling.index, rolling, 0,
                        where=(rolling >= 0),
                        alpha=0.2, color="green")
        ax.set_title(
            f"{window}-Month Rolling Correlation: "
            "Rate Changes vs S&P 500 Changes",
            fontsize=13, fontweight="bold"
        )
        ax.set_xlabel("Year")
        ax.set_ylabel("Correlation")
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        return ax


# ── RUN DIRECTLY ────────────────────────────────────────────────────
if __name__ == "__main__":
    analyzer = RateMarketAnalyzer()

    print("Available series:")
    print(analyzer.available_series())

    print("\nSummary statistics:")
    print(analyzer.summary_statistics(start="2015-01-01"))

    analyzer.plot_both(start="2015-01-01")
    analyzer.plot_scatter(start="2015-01-01")
    analyzer.plot_rolling_correlation(window=12, start="2015-01-01")

    plt.show()