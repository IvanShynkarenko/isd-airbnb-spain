import numpy as np
import pandas as pd

from airbnb.baseline import fit_baseline


def test_baseline_medians_and_fallbacks():
    train = pd.DataFrame({
        "room_type": ["Entire home/apt"] * 3 + ["Private room"] * 2,
        "accommodates": [2, 2, 4, 1, 1],
        "price": [100.0, 120.0, 200.0, 40.0, 60.0],
    })
    b = fit_baseline(train)
    test = pd.DataFrame({
        "room_type": ["Entire home/apt", "Entire home/apt", "Hotel room", "Private room"],
        "accommodates": [2, 9, 2, None],
    })
    np.testing.assert_allclose(b.predict(test), [110.0, 120.0, 100.0, 50.0])
